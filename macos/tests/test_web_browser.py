import functools
import http.server
import threading

import pytest

from agentbetta.core.models import PermissionSet
from agentbetta.permissions import profile_permission_set
from agentbetta.permissions.policy import BROWSER_READ, FILE_READ
from agentbetta.platform.windows import paths
from agentbetta.tools.browser import (
    BrowserConfig,
    BrowserSession,
    validate_browser_url,
)
from agentbetta.tools.web import http_fetch, html_to_text, validate_http_url
from agentbetta.tools import browser as browsert
from agentbetta.tools import web as webt
from agentbetta.tools import ToolContext


@pytest.fixture(scope="module")
def web_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("webroot")
    (root / "index.html").write_text(
        "<html><head><title>Fixture</title></head><body>"
        "<h1>Hello AgentBetta</h1><p id='p'>needle text</p>"
        "<input id='name' />"
        "<a id='dl' href='sample.txt' download>download</a>"
        "</body></html>",
        encoding="utf-8",
    )
    (root / "sample.txt").write_text("download-content", encoding="utf-8")
    return root


@pytest.fixture(scope="module")
def web_server(web_root):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(web_root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture(scope="module")
def browser_session(tmp_path_factory):
    profile = tmp_path_factory.mktemp("browserprofile")
    downloads = tmp_path_factory.mktemp("downloads")
    session = BrowserSession(BrowserConfig(headless=True, profile_dir=str(profile), downloads_dir=str(downloads)))
    yield session
    session.close()


@pytest.fixture
def full_ctx(browser_session):
    return ToolContext(permissions=profile_permission_set("full"), browser=browser_session)


def test_html_to_text_strips_scripts():
    assert "visible" in html_to_text("<div>visible</div><script>hidden()</script>")


def test_http_fetch_local(web_server):
    ctx = ToolContext(permissions=PermissionSet(allowed=frozenset({"network_http"}), eligible=frozenset({"network_http"})))
    result = http_fetch(ctx=ctx, url=f"{web_server}/index.html")
    assert result["status_code"] == 200
    assert "Hello AgentBetta" in result["text"]


def test_http_fetch_blocks_non_http():
    with pytest.raises(ValueError):
        validate_http_url("file:///C:/secret.txt")


def test_http_fetch_permission_required(web_server):
    ctx = ToolContext(permissions=PermissionSet(allowed=frozenset(), eligible=frozenset()))
    with pytest.raises(PermissionError):
        http_fetch(ctx=ctx, url=f"{web_server}/index.html")


def test_browser_open_and_extract(full_ctx, web_server):
    opened = browsert.browser_open(ctx=full_ctx, url=f"{web_server}/index.html")
    assert opened["title"] == "Fixture"
    extracted = browsert.browser_extract_text(ctx=full_ctx)
    assert "Hello AgentBetta" in extracted["text"]


def test_browser_fill_and_click_need_interact(full_ctx, web_server):
    browsert.browser_open(ctx=full_ctx, url=f"{web_server}/index.html")
    result = browsert.browser_fill(ctx=full_ctx, selector="#name", value="Betta")
    assert result["filled"] is True


def test_browser_interact_denied_without_permission(browser_session, web_server):
    ctx = ToolContext(permissions=profile_permission_set("safe"), browser=browser_session)
    with pytest.raises(PermissionError):
        browsert.browser_click(ctx=ctx, selector="#dl")


def test_browser_download(full_ctx, web_server, browser_session):
    browsert.browser_open(ctx=full_ctx, url=f"{web_server}/index.html")
    result = browsert.browser_download(ctx=full_ctx, selector="#dl")
    from pathlib import Path

    assert Path(result["path"]).read_text(encoding="utf-8") == "download-content"


def test_file_url_requires_file_read_permission():
    ctx = ToolContext(
        permissions=PermissionSet(allowed=frozenset({BROWSER_READ}), eligible=frozenset({BROWSER_READ}))
    )
    with pytest.raises(PermissionError):
        validate_browser_url(ctx, "file:///C:/secret.txt")
    ok = ToolContext(
        permissions=PermissionSet(allowed=frozenset({BROWSER_READ, FILE_READ}), eligible=frozenset())
    )
    validate_browser_url(ok, "file:///C:/public.txt")


def test_dedicated_profile_is_not_user_profile():
    assert "AgentBetta" in str(paths.browser_profile_dir())
    assert "Edge" not in str(paths.browser_profile_dir())
