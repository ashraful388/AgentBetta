"""Reusable, theme-aware building blocks for the AgentBetta desktop GUI.

These are intentionally small and dependency-free so views can compose a clean
layout without duplicating stylesheet object names.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

TONE_BY_STATUS = {
    "PASS": "success",
    "VERIFIED": "success",
    "COMPLETED": "success",
    "FAIL": "danger",
    "FAILED": "danger",
    "ERROR": "danger",
    "NOT VERIFIED": "warning",
    "INSUFFICIENT_EVIDENCE": "warning",
    "CANCELLED": "warning",
    "RUNNING": "info",
    "IDLE": "muted",
}


def badge(text: str, tone: str = "muted") -> QLabel:
    label = QLabel(text)
    label.setObjectName("Badge")
    label.setProperty("tone", tone)
    label.setAlignment(Qt.AlignCenter)
    label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    return label


def status_badge(text: str) -> QLabel:
    return badge(text, TONE_BY_STATUS.get(text.upper(), "muted"))


def set_badge_tone(label: QLabel, text: str, tone: str | None = None) -> None:
    label.setText(text)
    label.setProperty("tone", tone or TONE_BY_STATUS.get(text.upper(), "muted"))
    _repolish(label)


def _repolish(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def divider() -> QFrame:
    line = QFrame()
    line.setObjectName("Divider")
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    return line


def heading(text: str, level: int = 2) -> QLabel:
    label = QLabel(text)
    label.setObjectName({1: "H1", 2: "H2", 3: "H3"}.get(level, "H3"))
    return label


def muted(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Muted")
    label.setWordWrap(True)
    return label


def faint(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("Faint")
    label.setWordWrap(True)
    return label


class SectionHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent: Any = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(heading(title, 1))
        if subtitle:
            layout.addWidget(muted(subtitle))


class Card(QFrame):
    """A surface panel with an optional title/subtitle header."""

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        *,
        flat: bool = False,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setProperty("flat", "true" if flat else "false")
        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(16, 14, 16, 14)
        self._outer.setSpacing(10)
        if title:
            header = QVBoxLayout()
            header.setSpacing(1)
            title_label = QLabel(title)
            title_label.setObjectName("CardTitle")
            header.addWidget(title_label)
            if subtitle:
                sub = QLabel(subtitle)
                sub.setObjectName("CardSubtitle")
                sub.setWordWrap(True)
                header.addWidget(sub)
            self._outer.addLayout(header)

    def body(self) -> QVBoxLayout:
        return self._outer

    def add(self, widget: QWidget) -> QWidget:
        self._outer.addWidget(widget)
        return widget

    def add_layout(self, layout: Any) -> Any:
        self._outer.addLayout(layout)
        return layout


class StatTile(QFrame):
    def __init__(self, label: str, value: str = "—", parent: Any = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setProperty("flat", "true")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        caption = QLabel(label)
        caption.setObjectName("FieldLabel")
        layout.addWidget(self.value_label)
        layout.addWidget(caption)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class KeyValueGrid(QWidget):
    """A compact label/value grid used by the run inspector."""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(5)

    def clear(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def set_rows(self, rows: list[tuple[str, str]]) -> None:
        self.clear()
        for key, value in rows:
            row = QWidget()
            layout = QHBoxLayout(row)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(10)
            key_label = QLabel(str(key))
            key_label.setObjectName("FieldLabel")
            key_label.setMinimumWidth(112)
            value_label = QLabel(str(value) if value not in (None, "") else "—")
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(key_label)
            layout.addWidget(value_label, 1)
            self._layout.addWidget(row)


class ChipList(QWidget):
    """A simple wrapping-free chip strip for tool names / capabilities."""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

    def clear(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def set_items(self, items: list[str], empty: str = "none", tone: str = "muted") -> None:
        self.clear()
        if not items:
            self._layout.addWidget(faint(empty))
            return
        for text in items:
            self._layout.addWidget(badge(text, tone))


class EmptyState(QWidget):
    def __init__(self, title: str, hint: str = "", parent: Any = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 40, 24, 40)
        layout.setSpacing(6)
        title_label = QLabel(title)
        title_label.setObjectName("H3")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        if hint:
            hint_label = QLabel(hint)
            hint_label.setObjectName("EmptyState")
            hint_label.setWordWrap(True)
            hint_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(hint_label)
        layout.addStretch(1)
