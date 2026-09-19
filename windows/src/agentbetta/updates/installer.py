"""Download and install an AgentBetta update.

Windows uses the Inno Setup installer (silent, per-user, upgrades in place).
macOS opens the downloaded disk image, or swaps the ``.app`` bundle for the
zipped build via a detached helper script.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable

from agentbetta.platform import paths
from agentbetta.updates.models import ReleaseAsset

_CHUNK = 256 * 1024
ProgressCallback = Callable[[int, int], None]


class InstallError(RuntimeError):
    pass


def updates_dir() -> Path:
    target = paths.local_app_data_root() / "updates"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _hidden_kwargs() -> dict:
    try:
        from agentbetta.platform.processes import _hidden_process_kwargs

        return _hidden_process_kwargs()
    except Exception:  # pragma: no cover - non-Windows
        return {}


def can_self_update() -> bool:
    """True when running from a packaged build that can replace itself."""

    return bool(getattr(sys, "frozen", False))


def parse_sha256sums(text: str) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for line in (text or "").splitlines():
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 64:
            checksums[parts[-1].lstrip("*").lower()] = parts[0].lower()
    return checksums


def download_asset(asset: ReleaseAsset, dest_dir: Path | None = None,
                   progress: ProgressCallback | None = None) -> Path:
    directory = Path(dest_dir) if dest_dir else updates_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (asset.name or "AgentBetta-update.bin")
    request = urllib.request.Request(asset.url, headers={"User-Agent": "AgentBetta-Updater"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response, open(target, "wb") as handle:
            total = int(response.headers.get("Content-Length") or asset.size or 0)
            done = 0
            while True:
                chunk = response.read(_CHUNK)
                if not chunk:
                    break
                handle.write(chunk)
                done += len(chunk)
                if progress is not None:
                    progress(done, total)
    except Exception as exc:
        raise InstallError(f"Download failed: {type(exc).__name__}: {exc}") from exc
    return target


def download_checksums(info) -> dict[str, str]:
    asset = info.checksums_asset()
    if asset is None:
        return {}
    request = urllib.request.Request(asset.url, headers={"User-Agent": "AgentBetta-Updater"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return parse_sha256sums(response.read().decode("utf-8", errors="replace"))
    except Exception:
        return {}


def verify_checksum(path: Path, expected: str | None) -> bool:
    if not expected:
        return True
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower() == expected.lower()


def install_update(path: Path, *, platform: str | None = None) -> str:
    """Launch the installer for the downloaded artifact. Returns a message."""

    platform = platform or ("macos" if sys.platform == "darwin" else "windows")
    if platform == "windows":
        args = [
            str(path),
            "/VERYSILENT",
            "/SUPPRESSMSGBOXES",
            "/NORESTART",
            "/SP-",
            "/CLOSEAPPLICATIONS",
            "/RESTARTAPPLICATIONS",
        ]
        subprocess.Popen(args, **_hidden_kwargs())
        return "Installer launched. AgentBetta will close and restart to finish the update."
    # macOS
    suffix = path.suffix.lower()
    if suffix == ".dmg":
        subprocess.Popen(["open", str(path)])
        return "Disk image opened. Drag AgentBetta into Applications to finish the update."
    if suffix == ".zip":
        return _macos_swap_app(path)
    raise InstallError(f"Unsupported update artifact: {path.name}")


def _macos_swap_app(zip_path: Path) -> str:
    app_path = _current_app_bundle()
    if app_path is None:
        subprocess.Popen(["open", str(zip_path)])
        return "Update downloaded. Unzip it and replace AgentBetta.app to finish."
    staging = Path(tempfile.mkdtemp(prefix="agentbetta_update_"))
    subprocess.run(["ditto", "-x", "-k", str(zip_path), str(staging)], check=True)
    new_app = next((p for p in staging.iterdir() if p.suffix == ".app"), None)
    if new_app is None:
        raise InstallError("The downloaded archive did not contain an .app bundle.")
    script = staging / "apply_update.sh"
    script.write_text(
        "#!/bin/bash\n"
        "sleep 2\n"
        f'rm -rf "{app_path}"\n'
        f'ditto "{new_app}" "{app_path}"\n'
        f'open "{app_path}"\n',
        encoding="utf-8",
    )
    script.chmod(0o755)
    subprocess.Popen(["/bin/bash", str(script)])
    return "Update staged. AgentBetta will quit, be replaced, and relaunch."


def _current_app_bundle() -> Path | None:
    exe = Path(sys.executable).resolve()
    for parent in exe.parents:
        if parent.suffix == ".app":
            return parent
    return None
