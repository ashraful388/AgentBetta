"""Playwright browser tools with a dedicated AgentBetta profile.

The default engine is the installed Microsoft Edge. The user's normal browser
profile is never used or harvested. All actions are recorded on the session.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from agentbetta.permissions import policy
from agentbetta.platform import PREFERRED_BROWSER_ENGINE, paths
from agentbetta.tools.guards import requires
from agentbetta.tools.registry import ToolContext

_ALLOWED_SCHEMES = ("http://", "https://")


@dataclass
class BrowserConfig:
    engine: str = ""
    headless: bool = True
    profile_dir: str | None = None
    downloads_dir: str | None = None
    timeout_ms: int = 30_000

    def resolved_engine(self) -> str:
        return self.engine or PREFERRED_BROWSER_ENGINE

    def resolved_profile_dir(self) -> Path:
        return Path(self.profile_dir) if self.profile_dir else paths.browser_profile_dir()

    def resolved_downloads_dir(self) -> Path:
        return Path(self.downloads_dir) if self.downloads_dir else paths.downloads_dir()


class BrowserSession:
    def __init__(self, config: BrowserConfig | None = None) -> None:
        self.config = config or BrowserConfig()
        self.actions: list[dict[str, Any]] = []
        self._pw: Any = None
        self._context: Any = None
        self.page: Any = None
        self.engine_used: str | None = None

    def record(self, action: str, target: str = "", **extra: Any) -> None:
        entry = {"action": action, "target": target, "time": time.time()}
        entry.update(extra)
        self.actions.append(entry)

    def _start(self) -> None:
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        profile = self.config.resolved_profile_dir()
        downloads = self.config.resolved_downloads_dir()
        profile.mkdir(parents=True, exist_ok=True)
        downloads.mkdir(parents=True, exist_ok=True)
        launch_kwargs: dict[str, Any] = {
            "user_data_dir": str(profile),
            "headless": self.config.headless,
            "accept_downloads": True,
            "downloads_path": str(downloads),
            "viewport": {"width": 1280, "height": 900},
        }
        engine = self.config.resolved_engine()
        try:
            self._context = self._pw.chromium.launch_persistent_context(
                channel=engine, **launch_kwargs
            )
            self.engine_used = engine
        except Exception:
            self._context = self._pw.chromium.launch_persistent_context(**launch_kwargs)
            self.engine_used = "chromium"
        self.page = self._context.pages[0] if self._context.pages else self._context.new_page()
        self.page.set_default_timeout(self.config.timeout_ms)

    def ensure(self) -> Any:
        if self._context is None:
            self._start()
        return self.page

    def close(self) -> None:
        try:
            if self._context is not None:
                self._context.close()
            if self._pw is not None:
                self._pw.stop()
        finally:
            self._context = None
            self._pw = None
            self.page = None


_DEFAULT_SESSION: BrowserSession | None = None


def get_default_session() -> BrowserSession:
    global _DEFAULT_SESSION
    if _DEFAULT_SESSION is None:
        _DEFAULT_SESSION = BrowserSession()
    return _DEFAULT_SESSION


def reset_default_session() -> None:
    global _DEFAULT_SESSION
    if _DEFAULT_SESSION is not None:
        _DEFAULT_SESSION.close()
    _DEFAULT_SESSION = None


def _session(ctx: ToolContext) -> BrowserSession:
    if ctx.browser is not None:
        return ctx.browser
    return get_default_session()


def validate_browser_url(ctx: ToolContext, url: str) -> None:
    lowered = url.strip().lower()
    if lowered.startswith(_ALLOWED_SCHEMES):
        return
    if lowered.startswith("file://"):
        if not ctx.permissions.permits(policy.FILE_READ):
            raise PermissionError("file:// navigation requires the file_read permission")
        return
    raise ValueError("Only http(s) and permitted file:// URLs may be opened")


def browser_available() -> tuple[bool, str]:
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment dependent
        return (False, f"Playwright is not installed: {exc}")
    return (True, "Playwright available; Chromium preferred, Microsoft Edge optional.")


@requires(policy.BROWSER_READ)
def browser_open(*, ctx: ToolContext, url: str) -> dict[str, Any]:
    validate_browser_url(ctx, url)
    session = _session(ctx)
    page = session.ensure()
    response = page.goto(url, wait_until="domcontentloaded")
    session.record("open", url)
    return {
        "url": page.url,
        "title": page.title(),
        "status": getattr(response, "status", None),
    }


@requires(policy.BROWSER_READ)
def browser_search(*, ctx: ToolContext, query: str, max_chars: int = 5_000) -> dict[str, Any]:
    session = _session(ctx)
    page = session.ensure()
    url = f"https://duckduckgo.com/?q={quote_plus(query)}"
    page.goto(url, wait_until="domcontentloaded")
    session.record("search", query)
    try:
        text = page.inner_text("body")
    except Exception:
        text = ""
    return {"query": query, "url": page.url, "title": page.title(), "text": text[:max_chars]}


@requires(policy.BROWSER_READ)
def browser_extract_text(*, ctx: ToolContext, selector: str | None = None,
                         max_chars: int = 20_000) -> dict[str, Any]:
    session = _session(ctx)
    page = session.ensure()
    target = selector or "body"
    text = page.inner_text(target)
    session.record("extract_text", target)
    return {"selector": target, "url": page.url, "text": text[:max_chars]}


@requires(policy.BROWSER_READ)
def browser_screenshot(*, ctx: ToolContext, path: str | None = None) -> dict[str, Any]:
    session = _session(ctx)
    page = session.ensure()
    if path:
        target = Path(path)
    else:
        target = session.config.resolved_downloads_dir() / f"screenshot-{int(time.time())}.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(target), full_page=False)
    session.record("screenshot", str(target))
    return {"path": str(target)}


@requires(policy.BROWSER_INTERACT)
def browser_click(*, ctx: ToolContext, selector: str) -> dict[str, Any]:
    session = _session(ctx)
    page = session.ensure()
    page.click(selector)
    session.record("click", selector)
    return {"selector": selector, "url": page.url}


@requires(policy.BROWSER_INTERACT)
def browser_fill(*, ctx: ToolContext, selector: str, value: str) -> dict[str, Any]:
    session = _session(ctx)
    page = session.ensure()
    page.fill(selector, value)
    session.record("fill", selector)
    return {"selector": selector, "filled": True}


@requires(policy.BROWSER_INTERACT)
def browser_select(*, ctx: ToolContext, selector: str, value: str) -> dict[str, Any]:
    session = _session(ctx)
    page = session.ensure()
    page.select_option(selector, value)
    session.record("select", selector)
    return {"selector": selector, "value": value}


@requires(policy.BROWSER_DOWNLOAD)
def browser_download(*, ctx: ToolContext, selector: str) -> dict[str, Any]:
    session = _session(ctx)
    page = session.ensure()
    with page.expect_download() as download_info:
        page.click(selector)
    download = download_info.value
    target = session.config.resolved_downloads_dir() / download.suggested_filename
    target.parent.mkdir(parents=True, exist_ok=True)
    download.save_as(str(target))
    session.record("download", selector, path=str(target))
    return {"path": str(target), "suggested_filename": download.suggested_filename}


@requires(policy.BROWSER_READ)
def browser_back(*, ctx: ToolContext) -> dict[str, Any]:
    session = _session(ctx)
    page = session.ensure()
    page.go_back()
    session.record("back")
    return {"url": page.url}


@requires(policy.BROWSER_READ)
def browser_close(*, ctx: ToolContext) -> dict[str, Any]:
    session = _session(ctx)
    count = len(session.actions)
    session.close()
    return {"closed": True, "actions": count}


__all__ = [
    "BrowserConfig",
    "BrowserSession",
    "browser_available",
    "browser_back",
    "browser_click",
    "browser_close",
    "browser_download",
    "browser_extract_text",
    "browser_fill",
    "browser_open",
    "browser_screenshot",
    "browser_search",
    "browser_select",
    "get_default_session",
    "reset_default_session",
    "validate_browser_url",
]
