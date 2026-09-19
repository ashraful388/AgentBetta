"""Check GitHub Releases for a newer AgentBetta version."""

from __future__ import annotations

import json
import platform as _platform
import sys
import urllib.error
import urllib.request
from typing import Any

from agentbetta.updates.models import ReleaseAsset, UpdateInfo
from agentbetta.updates.version import is_newer

GITHUB_API = "https://api.github.com"
DEFAULT_UPDATE_REPO = "ashrafulbabu/AgentBetta"
_USER_AGENT = "AgentBetta-Updater"
_TIMEOUT = 20


class UpdateError(RuntimeError):
    pass


def current_platform() -> str:
    return "macos" if sys.platform == "darwin" else "windows"


def _get(url: str, timeout: int = _TIMEOUT) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": _USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise UpdateError(
                "No releases found for the configured update source. "
                "Check Settings ▸ Updates."
            ) from exc
        raise UpdateError(f"Update server returned HTTP {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise UpdateError(f"Could not reach the update server: {exc.reason}") from exc
    except (json.JSONDecodeError, TimeoutError) as exc:
        raise UpdateError(f"Malformed update response: {type(exc).__name__}") from exc


def _to_info(release: dict[str, Any]) -> UpdateInfo:
    assets = [
        ReleaseAsset(
            name=str(asset.get("name") or ""),
            url=str(asset.get("browser_download_url") or ""),
            size=int(asset.get("size") or 0),
        )
        for asset in (release.get("assets") or [])
    ]
    return UpdateInfo(
        version=str(release.get("tag_name") or "").lstrip("vV"),
        tag=str(release.get("tag_name") or ""),
        notes=str(release.get("body") or ""),
        page_url=str(release.get("html_url") or ""),
        published_at=str(release.get("published_at") or ""),
        prerelease=bool(release.get("prerelease")),
        assets=assets,
    )


def fetch_latest_release(repo: str, *, channel: str = "stable") -> UpdateInfo:
    if not repo or "/" not in repo:
        raise UpdateError("No update source configured (expected 'owner/repo').")
    if channel == "prerelease":
        releases = _get(f"{GITHUB_API}/repos/{repo}/releases?per_page=20")
        if not isinstance(releases, list) or not releases:
            raise UpdateError("No releases found for the configured update source.")
        candidates = [_to_info(release) for release in releases if not release.get("draft")]
        if not candidates:
            raise UpdateError("No published releases found.")
        return max(candidates, key=lambda info: info.version)
    data = _get(f"{GITHUB_API}/repos/{repo}/releases/latest")
    if not isinstance(data, dict):
        raise UpdateError("Unexpected update response.")
    return _to_info(data)


def select_asset(info: UpdateInfo, platform: str | None = None) -> ReleaseAsset | None:
    """Pick the installer asset appropriate for the platform."""

    platform = platform or current_platform()
    names = [(asset, asset.name.lower()) for asset in info.assets]
    if platform == "windows":
        for asset, name in names:
            if "setup" in name and name.endswith(".exe"):
                return asset
        for asset, name in names:
            if name.endswith(".exe"):
                return asset
        return None
    # macOS: prefer a disk image for the running architecture, then any dmg,
    # then the zipped .app bundle.
    machine = _platform.machine().lower()
    if machine in ("aarch64",):
        machine = "arm64"
    if machine in ("amd64",):
        machine = "x86_64"
    dmgs = [(asset, name) for asset, name in names if name.endswith(".dmg")]
    for asset, name in dmgs:
        if machine and machine in name:
            return asset
    if dmgs:
        return dmgs[0][0]
    for asset, name in names:
        if name.endswith(".zip") and "portable" not in name:
            if machine and machine in name:
                return asset
    for asset, name in names:
        if name.endswith(".zip") and "portable" not in name:
            return asset
    return None


def check_for_update(current_version: str, repo: str, *, channel: str = "stable",
                     platform: str | None = None) -> UpdateInfo | None:
    """Return UpdateInfo when a newer release exists, else None."""

    info = fetch_latest_release(repo, channel=channel)
    if not info.version or not is_newer(info.version, current_version):
        return None
    return info
