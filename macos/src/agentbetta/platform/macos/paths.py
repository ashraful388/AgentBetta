"""Per-user application data paths for macOS.

Binary application files must never be mixed with mutable user data. Secrets
live in the macOS Keychain (via ``keyring``), not under these directories.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_DIR_NAME = "AgentBetta"


def _env(name: str) -> str | None:
    value = os.environ.get(name)
    return value or None


def app_data_root(override: str | Path | None = None) -> Path:
    if override:
        return Path(override).expanduser()
    env = _env("AGENTBETTA_APPDATA")
    if env:
        return Path(env)
    return Path.home() / "Library" / "Application Support" / APP_DIR_NAME


def local_app_data_root(override: str | Path | None = None) -> Path:
    if override:
        return Path(override).expanduser()
    env = _env("AGENTBETTA_LOCALAPPDATA")
    if env:
        return Path(env)
    return Path.home() / "Library" / "Application Support" / APP_DIR_NAME


def documents_root(override: str | Path | None = None) -> Path:
    if override:
        return Path(override).expanduser()
    env = _env("AGENTBETTA_DOCUMENTS")
    if env:
        return Path(env)
    return Path.home() / "Documents" / APP_DIR_NAME


def config_dir(override: str | Path | None = None) -> Path:
    return app_data_root(override) / "config"


def settings_path(override: str | Path | None = None) -> Path:
    return app_data_root(override) / "settings.json"


def logs_dir(override: str | Path | None = None) -> Path:
    if override or _env("AGENTBETTA_LOCALAPPDATA"):
        return local_app_data_root(override) / "logs"
    return Path.home() / "Library" / "Logs" / APP_DIR_NAME


def cache_dir(override: str | Path | None = None) -> Path:
    if override or _env("AGENTBETTA_LOCALAPPDATA"):
        return local_app_data_root(override) / "cache"
    return Path.home() / "Library" / "Caches" / APP_DIR_NAME


def browser_dir(override: str | Path | None = None) -> Path:
    return local_app_data_root(override) / "browser"


def browser_profile_dir(override: str | Path | None = None) -> Path:
    return browser_dir(override) / "profile"


def downloads_dir(override: str | Path | None = None) -> Path:
    return local_app_data_root(override) / "downloads"


def runs_dir(override: str | Path | None = None) -> Path:
    return documents_root(override) / "runs"


def logs_path(override: str | Path | None = None) -> Path:
    return logs_dir(override) / "agentbetta.log"


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def known_folders() -> dict[str, str]:
    """Return the user's standard folders (Home/Desktop/Documents/Downloads)."""

    home = Path.home()
    return {
        "user_profile": str(home),
        "home": str(home),
        "desktop": str(home / "Desktop"),
        "documents": str(home / "Documents"),
        "downloads": str(home / "Downloads"),
    }
