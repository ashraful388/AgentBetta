"""Filesystem primitives for global (non-workspace) macOS access.

All paths are canonicalized. Raw device paths are blocked. Network mounts
(``/Volumes`` external shares and ``//`` SMB paths) are flagged so the
permission layer can require ``network_share``.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from agentbetta.platform.macos.paths import known_folders

_DEVICE_PREFIXES = ("/dev/",)
_FOLDER_ALIASES = {
    "desktop": "desktop",
    "documents": "documents",
    "document": "documents",
    "downloads": "downloads",
    "download": "downloads",
    "home": "user_profile",
    "userprofile": "user_profile",
    "user_profile": "user_profile",
}


class UnsafePathError(PermissionError):
    pass


def _apply_folder_alias(text: str) -> str:
    if not text or text.startswith(("/", "~", "//")):
        return text
    parts = re.split(r"[\\/]", text, maxsplit=1)
    head = parts[0].lower()
    if head in _FOLDER_ALIASES:
        base = known_folders().get(_FOLDER_ALIASES[head])
        if base:
            rest = parts[1] if len(parts) > 1 else ""
            return os.path.join(base, rest) if rest else base
    return text


def canonical_path(raw: str | os.PathLike[str]) -> Path:
    text = os.path.expandvars(str(raw)).strip().strip('"')
    if not text:
        raise UnsafePathError("Empty path is not allowed")
    if text.startswith(_DEVICE_PREFIXES):
        raise UnsafePathError(f"Raw device paths are blocked: {text}")
    text = _apply_folder_alias(text)
    return Path(text).expanduser().resolve(strict=False)


def is_network_path(path: str | os.PathLike[str]) -> bool:
    text = str(path)
    if text.startswith("//"):
        return True
    if text.startswith("/Volumes/"):
        return True
    return text.startswith("/Network/")


def list_drives() -> list[dict[str, object]]:
    """List mounted volumes (the root volume plus anything under /Volumes)."""

    import shutil

    roots = [Path("/")]
    volumes = Path("/Volumes")
    if volumes.is_dir():
        roots.extend(sorted(p for p in volumes.iterdir() if p.is_dir()))
    entries: list[dict[str, object]] = []
    for root in roots:
        entry: dict[str, object] = {"path": str(root)}
        try:
            usage = shutil.disk_usage(root)
            entry.update(total=usage.total, used=usage.used, free=usage.free)
        except OSError:
            entry.update(total=None, used=None, free=None)
        entries.append(entry)
    return entries


def file_hash(path: str | os.PathLike[str], algorithm: str = "sha256") -> str:
    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    digest = hashlib.new(algorithm)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def human_size(value: int | None) -> str:
    if value is None:
        return "unknown"
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def search_files(root: str | os.PathLike[str], pattern: str, *, max_results: int = 200,
                 recursive: bool = True) -> list[str]:
    import fnmatch

    root_path = Path(root)
    results: list[str] = []
    iterator = root_path.rglob("*") if recursive else root_path.glob("*")
    for candidate in iterator:
        if len(results) >= max_results:
            break
        if fnmatch.fnmatch(candidate.name, pattern):
            results.append(str(candidate))
    return results


def grep_files(root: str | os.PathLike[str], query: str, *, max_results: int = 100,
               max_file_bytes: int = 2_000_000) -> list[dict[str, object]]:
    root_path = Path(root)
    hits: list[dict[str, object]] = []
    for candidate in root_path.rglob("*"):
        if len(hits) >= max_results:
            break
        if not candidate.is_file():
            continue
        try:
            if candidate.stat().st_size > max_file_bytes:
                continue
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if query in line:
                hits.append({"path": str(candidate), "line": line_no, "text": line.strip()[:300]})
                if len(hits) >= max_results:
                    break
    return hits
