from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

_TRANSIENT_CODES = {408, 425, 429, 500, 502, 503, 504, 520, 522, 524}


class ProviderHTTPError(RuntimeError):
    def __init__(self, message: str, *, code: int | None = None, detail: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.detail = detail

    @property
    def transient(self) -> bool:
        if self.code is None:
            return True  # network/URLError is usually transient
        return self.code in _TRANSIENT_CODES


def _request(url: str, *, method: str, payload: dict[str, Any] | None, headers: dict[str, str] | None,
             timeout: int) -> Any:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    hdr = {"Content-Type": "application/json", "Accept": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=body, headers=hdr, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:1000]
        raise ProviderHTTPError(f"HTTP {e.code}: {detail}", code=e.code, detail=detail) from e
    except urllib.error.URLError as e:
        raise ProviderHTTPError(f"Provider connection failed: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise ProviderHTTPError("Provider returned a non-JSON response") from e


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None,
              timeout: int = 60) -> Any:
    return _request(url, method="POST", payload=payload, headers=headers, timeout=timeout)


def get_json(url: str, headers: dict[str, str] | None = None, timeout: int = 30) -> Any:
    return _request(url, method="GET", payload=None, headers=headers, timeout=timeout)
