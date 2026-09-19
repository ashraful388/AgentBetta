"""Per-user application data paths.

Binary install files must never be mixed with mutable user data. Secrets live
in the platform credential manager, not under these directories.
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
    base = _env("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(base) / APP_DIR_NAME


def local_app_data_root(override: str | Path | None = None) -> Path:
    if override:
        return Path(override).expanduser()
    env = _env("AGENTBETTA_LOCALAPPDATA")
    if env:
        return Path(env)
    base = _env("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(base) / APP_DIR_NAME


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
    return local_app_data_root(override) / "logs"


def cache_dir(override: str | Path | None = None) -> Path:
    return local_app_data_root(override) / "cache"


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
    """Return the user's real shell folders (Desktop/Documents/Downloads).

    Uses the Windows shell-known-folder registry entries so OneDrive-redirected
    locations are reported correctly, with a home-relative fallback.
    """

    home = Path.home()
    folders: dict[str, str] = {
        "user_profile": str(home),
        "home": str(home),
        "desktop": str(home / "Desktop"),
        "documents": str(home / "Documents"),
        "downloads": str(home / "Downloads"),
    }
    if os.name != "nt":
        return folders
    try:
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            mapping = {
                "Desktop": ("desktop",),
                "Personal": ("documents",),
                "{374DE290-123F-4565-9164-39C4925E467B}": ("downloads",),
            }
            for value_name, targets in mapping.items():
                try:
                    raw, _ = winreg.QueryValueEx(key, value_name)
                except OSError:
                    continue
                expanded = os.path.expandvars(str(raw))
                for target in targets:
                    folders[target] = expanded
    except Exception:
        pass
    return folders

