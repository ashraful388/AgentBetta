"""Access to bundled desktop image assets (logo, application icon)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

RESOURCES = Path(__file__).resolve().parent / "resources"

ICON_FILE = RESOURCES / "agentbetta.ico"
LOGO_FILE = RESOURCES / "agentbetta.png"
FULL_LOGO_FILE = RESOURCES / "agentbetta_logo.png"


def resource_path(name: str) -> Path:
    return RESOURCES / name


def app_icon() -> QIcon:
    if ICON_FILE.exists():
        return QIcon(str(ICON_FILE))
    if LOGO_FILE.exists():
        return QIcon(str(LOGO_FILE))
    return QIcon()


def logo_pixmap(size: int = 40) -> QPixmap:
    pixmap = QPixmap(str(LOGO_FILE))
    if pixmap.isNull():
        return pixmap
    return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def full_logo_pixmap(width: int = 320) -> QPixmap:
    source = FULL_LOGO_FILE if FULL_LOGO_FILE.exists() else LOGO_FILE
    pixmap = QPixmap(str(source))
    if pixmap.isNull():
        return pixmap
    return pixmap.scaledToWidth(width, Qt.SmoothTransformation)
