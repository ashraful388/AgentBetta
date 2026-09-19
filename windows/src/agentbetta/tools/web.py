"""Read-only HTTP retrieval for ordinary public pages."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Any

try:  # optional dependency: the web tool degrades gracefully without it
    import httpx
except ImportError:  # pragma: no cover - environment dependent
    httpx = None  # type: ignore[assignment]

from agentbetta.permissions import policy
from agentbetta.tools.guards import requires
from agentbetta.tools.registry import ToolContext

MAX_BYTES = 2_000_000
USER_AGENT = "AgentBetta/0.2 (+https://agentbetta.invalid)"
_SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        text = data.strip()
        if text:
            self._parts.append(text)

    def text(self) -> str:
        return "\n".join(self._parts)


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


def validate_http_url(url: str) -> None:
    lowered = url.strip().lower()
    if not (lowered.startswith("http://") or lowered.startswith("https://")):
        raise ValueError("Only http:// and https:// URLs are allowed by http_fetch")


@requires(policy.NETWORK_HTTP)
def http_fetch(*, ctx: ToolContext, url: str, max_chars: int = 20_000) -> dict[str, Any]:
    validate_http_url(url)
    if httpx is None:
        raise RuntimeError(
            "http_fetch requires the 'httpx' package. Install it with: pip install 'agentbetta[http]'"
        )
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url, headers={"User-Agent": USER_AGENT})
    raw = response.content[:MAX_BYTES]
    content_type = response.headers.get("content-type", "")
    if "html" in content_type.lower():
        body = html_to_text(raw.decode(response.encoding or "utf-8", errors="replace"))
    else:
        body = raw.decode(response.encoding or "utf-8", errors="replace")
    truncated = len(response.content) > MAX_BYTES or len(body) > max_chars
    return {
        "status_code": response.status_code,
        "url": str(response.url),
        "content_type": content_type,
        "text": body[:max_chars],
        "truncated": truncated,
    }


__all__ = ["html_to_text", "http_fetch", "validate_http_url"]
