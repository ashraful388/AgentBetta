"""GitHub Releases based update checking and installation."""

from __future__ import annotations

from agentbetta.updates.checker import (
    DEFAULT_UPDATE_REPO,
    UpdateError,
    check_for_update,
    current_platform,
    fetch_latest_release,
    select_asset,
)
from agentbetta.updates.installer import (
    InstallError,
    can_self_update,
    download_asset,
    download_checksums,
    install_update,
    parse_sha256sums,
    updates_dir,
    verify_checksum,
)
from agentbetta.updates.models import ReleaseAsset, UpdateInfo
from agentbetta.updates.version import compare_versions, is_newer, parse_version

__all__ = [
    "DEFAULT_UPDATE_REPO",
    "InstallError",
    "ReleaseAsset",
    "UpdateError",
    "UpdateInfo",
    "can_self_update",
    "check_for_update",
    "compare_versions",
    "current_platform",
    "download_asset",
    "download_checksums",
    "fetch_latest_release",
    "install_update",
    "is_newer",
    "parse_sha256sums",
    "parse_version",
    "select_asset",
    "updates_dir",
    "verify_checksum",
]
