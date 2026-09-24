"""Check GitHub Releases for a newer AgentBetta version."""

from __future__ import annotations

import json
import platform as _platform
import sys
import urllib.error
import urllib.request
from functools import cmp_to_key
from typing import Any

from agentbetta.updates.models import ReleaseAsset, UpdateInfo
from agentbetta.updates.version import compare_versions, is_newer, is_prerelease

GITHUB_API = "https://api.github.com"
DEFAULT_UPDATE_REPO = "ashraful388/AgentBetta"
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
        if exc.code in (403, 429):
            raise UpdateError(
                "GitHub's update API rate limit was reached. Try again later."
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
        candidates: list[UpdateInfo] = []
        page = 1
        while True:
            releases = _get(
                f"{GITHUB_API}/repos/{repo}/releases?per_page=100&page={page}"
            )
            if not isinstance(releases, list):
                raise UpdateError("Unexpected update response.")
            candidates.extend(
                _to_info(release) for release in releases if not release.get("draft")
            )
            if len(releases) < 100:
                break
            page += 1
        if not candidates:
            raise UpdateError("No published releases found.")
        return max(
            candidates,
            key=cmp_to_key(lambda left, right: compare_versions(left.version, right.version)),
        )
    data = _get(f"{GITHUB_API}/repos/{repo}/releases/latest")
    if not isinstance(data, dict):
        raise UpdateError("Unexpected update response.")
    info = _to_info(data)
    if bool(data.get("prerelease")) or is_prerelease(info.version):
        raise UpdateError("The latest GitHub release is a pre-release, not a stable release.")
    return info


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
    machine = _platform.machine().lower()
    if machine == "aarch64":
        machine = "arm64"
    if machine == "amd64":
        machine = "x86_64"
    dmgs = [(asset, name) for asset, name in names if name.endswith(".dmg")]
    zips = [
        (asset, name)
        for asset, name in names
        if name.endswith(".zip") and "portable" not in name
    ]
    for candidates in (dmgs, zips):
        for asset, name in candidates:
            if machine and machine in name:
                return asset
        for asset, name in candidates:
            if "universal" in name:
                return asset
        if machine and any(
            "arm64" in name or "x86_64" in name for _, name in candidates
        ):
            continue
        if candidates:
            return candidates[0][0]
    return None


def check_for_update(current_version: str, repo: str, *, channel: str = "stable",
                     platform: str | None = None) -> UpdateInfo | None:
    """Return UpdateInfo when a newer release exists, else None."""

    info = fetch_latest_release(repo, channel=channel)
    if not info.version or not is_newer(info.version, current_version):
        return None
    return info
