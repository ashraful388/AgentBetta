"""Line-icon set for the AgentBetta GUI.

Icons are small inline SVGs rendered with QtSvg, so they stay crisp at any DPI
and can be tinted to the active theme colour. No external icon dependency.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

_ICONS: dict[str, str] = {
    "tasks": (
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h9"/>'
        '<line x1="16" y1="5" x2="22" y2="5"/><line x1="19" y1="2" x2="19" y2="8"/>'
    ),
    "chats": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "projects": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "agents": (
        '<rect x="6" y="6" width="12" height="12" rx="2"/>'
        '<path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>'
    ),
    "memory": (
        '<ellipse cx="12" cy="6" rx="8" ry="3"/>'
        '<path d="M4 6v6c0 1.7 3.6 3 8 3s8-1.3 8-3V6"/>'
        '<path d="M4 12v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>'
    ),
    "history": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "settings": (
        '<line x1="4" y1="7" x2="20" y2="7"/><circle cx="9" cy="7" r="2.5"/>'
        '<line x1="4" y1="17" x2="20" y2="17"/><circle cx="15" cy="17" r="2.5"/>'
    ),
    "guide": (
        '<path d="M12 6c-2-1.5-5-2-8-2v14c3 0 6 .5 8 2 2-1.5 5-2 8-2V4c-3 0-6 .5-8 2z"/>'
        '<path d="M12 6v14"/>'
    ),
    "about": (
        '<circle cx="12" cy="12" r="9"/><line x1="12" y1="11" x2="12" y2="16"/>'
        '<circle cx="12" cy="8" r="0.6" fill="currentColor" stroke="none"/>'
    ),
    "update": (
        '<path d="M6 18a4 4 0 0 1 0-8 5 5 0 0 1 9.6-1.6A4 4 0 0 1 18 18"/>'
        '<line x1="12" y1="11" x2="12" y2="20"/><path d="M9 17l3 3 3-3"/>'
    ),
    "refresh": '<path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v5h-5"/>',
    "inspector": '<rect x="3" y="4" width="18" height="16" rx="2"/><line x1="15" y1="4" x2="15" y2="20"/>',
    "sun": (
        '<circle cx="12" cy="12" r="4"/>'
        '<path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19"/>'
    ),
    "moon": '<path d="M20 13a8 8 0 1 1-9-9 6 6 0 0 0 9 9z"/>',
    "send": '<line x1="12" y1="20" x2="12" y2="5"/><path d="M6 11l6-6 6 6"/>',
    "attach": '<path d="M20 11l-8 8a5 5 0 0 1-7-7l8-8a3.5 3.5 0 0 1 5 5l-8 8a2 2 0 0 1-3-3l7-7"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="2"/>',
    "new": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    "clear": (
        '<path d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>'
        '<path d="M6 7l1 12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-12"/>'
    ),
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "chevron": '<path d="M6 9l6 6 6-6"/>',
    "copy": '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/>',
    "like": (
        '<path d="M7 10v10H4V10z"/>'
        '<path d="M7 10l4-6a1.5 1.5 0 0 1 2.8 1V9h4.2a1.8 1.8 0 0 1 1.7 2.3l-1.4 6A1.8 1.8 0 0 1 16.6 19H7z"/>'
    ),
    "dislike": (
        '<path d="M17 14V4h3v10z"/>'
        '<path d="M17 14l-4 6a1.5 1.5 0 0 1-2.8-1V15H6a1.8 1.8 0 0 1-1.7-2.3l1.4-6A1.8 1.8 0 0 1 7.4 5H17z"/>'
    ),
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
}

_cache: dict[tuple[str, str, int], QIcon] = {}


def pixmap(name: str, color: str, size: int = 22) -> QPixmap:
    body = _ICONS.get(name, _ICONS["about"])
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{body}</svg>"
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    app = QApplication.instance()
    ratio = app.devicePixelRatio() if app is not None else 1.0
    target = QPixmap(int(size * ratio), int(size * ratio))
    target.fill(Qt.transparent)
    painter = QPainter(target)
    renderer.render(painter)
    painter.end()
    target.setDevicePixelRatio(ratio)
    return target


def icon(name: str, color: str, size: int = 22) -> QIcon:
    key = (name, color, size)
    if key not in _cache:
        _cache[key] = QIcon(pixmap(name, color, size))
    return _cache[key]


def clear_cache() -> None:
    _cache.clear()
