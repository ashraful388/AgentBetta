"""Governed Memory Fabric view.

Presents the memory tiers described in the development plan using the existing
typed memory store: working/short-term are run-scoped views, while the durable
store is classified into semantic, episodic and procedural tiers.
"""

from __future__ import annotations

import os
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from agentbetta.desktop.services import AppServices
from agentbetta.desktop.widgets.ui import Card, SectionHeader, StatTile, muted

_TIER_FOR_KIND = {
    "fact": "Semantic",
    "preference": "Semantic",
    "episode": "Episodic",
    "summary": "Procedural",
}
_TIERS = ("All tiers", "Semantic", "Episodic", "Procedural")


class MemoryView(QWidget):
    """Memory fabric: tier summary, governed store and retrieval."""

    memoryChanged = Signal()

    def __init__(self, services: AppServices, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self._entries: list[dict[str, Any]] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        layout.addWidget(
            SectionHeader(
                "Memory Fabric",
                "Tiered, governed memory. Untrusted output never writes directly to durable "
                "tiers; verified outcomes and explicit statements are captured.",
            )
        )

        tiles = QHBoxLayout()
        tiles.setSpacing(10)
        self.tile_working = StatTile("Working memory", "run-scoped")
        self.tile_short = StatTile("Short-term (runs)", "0")
        self.tile_semantic = StatTile("Semantic", "0")
        self.tile_episodic = StatTile("Episodic", "0")
        self.tile_procedural = StatTile("Procedural", "0")
        for tile in (
            self.tile_working,
            self.tile_short,
            self.tile_semantic,
            self.tile_episodic,
            self.tile_procedural,
        ):
            tiles.addWidget(tile)
        layout.addLayout(tiles)

        add_card = Card("Add a durable memory", "Stored with provenance and deduplicated on write.")
        add_row = QHBoxLayout()
        self.kind_combo = QComboBox()
        for key in ("fact", "preference", "episode", "summary"):
            self.kind_combo.addItem(key, key)
        self.memory_input = QLineEdit()
        self.memory_input.setPlaceholderText("e.g. I prefer concise answers with code examples")
        add_button = QPushButton("Remember")
        add_button.setObjectName("Primary")
        add_button.clicked.connect(self.memory_add)
        add_row.addWidget(self.kind_combo)
        add_row.addWidget(self.memory_input, 1)
        add_row.addWidget(add_button)
        add_card.add_layout(add_row)
        layout.addWidget(add_card)

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search memory…")
        self.search.textChanged.connect(self._apply_filter)
        self.tier_filter = QComboBox()
        for tier in _TIERS:
            self.tier_filter.addItem(tier, tier)
        self.tier_filter.currentIndexChanged.connect(self._apply_filter)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        forget = QPushButton("Forget selected")
        forget.clicked.connect(self.memory_forget_selected)
        clear = QPushButton("Clear all")
        clear.setObjectName("Danger")
        clear.clicked.connect(self.memory_clear)
        folder = QPushButton("Open folder")
        folder.setObjectName("Ghost")
        folder.clicked.connect(self.open_memory_folder)
        toolbar.addWidget(self.search, 2)
        toolbar.addWidget(self.tier_filter, 1)
        toolbar.addStretch(1)
        toolbar.addWidget(refresh)
        toolbar.addWidget(forget)
        toolbar.addWidget(clear)
        toolbar.addWidget(folder)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Tier", "Kind", "Memory", "Source", "Importance", "Updated"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 96)
        self.table.setColumnWidth(1, 84)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 88)
        self.table.setColumnWidth(5, 150)
        layout.addWidget(self.table, 1)

        self.status = muted("")
        layout.addWidget(self.status)

    # -- data -------------------------------------------------------------
    def refresh(self) -> None:
        self._entries = self.services.memory_entries()
        semantic = sum(1 for e in self._entries if _TIER_FOR_KIND.get(e.get("kind")) == "Semantic")
        episodic = sum(1 for e in self._entries if _TIER_FOR_KIND.get(e.get("kind")) == "Episodic")
        procedural = sum(1 for e in self._entries if _TIER_FOR_KIND.get(e.get("kind")) == "Procedural")
        self.tile_semantic.set_value(str(semantic))
        self.tile_episodic.set_value(str(episodic))
        self.tile_procedural.set_value(str(procedural))
        self.tile_short.set_value(str(len(self.services.list_runs(limit=50))))
        self._apply_filter()

    def _apply_filter(self) -> None:
        query = self.search.text().strip().lower()
        tier = self.tier_filter.currentData()
        rows = []
        for entry in self._entries:
            entry_tier = _TIER_FOR_KIND.get(entry.get("kind"), "Semantic")
            if tier and tier != "All tiers" and entry_tier != tier:
                continue
            if query and query not in str(entry.get("text", "")).lower():
                continue
            rows.append((entry_tier, entry))
        self.table.setRowCount(0)
        for entry_tier, entry in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                entry_tier,
                str(entry.get("kind", "")),
                str(entry.get("text", "")),
                str(entry.get("source", "")),
                f"{float(entry.get('importance', 0.0)):.2f}",
                str(entry.get("updated_at", ""))[:19].replace("T", " "),
            ]
            for index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if index == 2:
                    item.setToolTip(value)
                self.table.setItem(row, index, item)
        self.status.setText(f"{len(rows)} of {len(self._entries)} memories shown")

    def memory_add(self) -> None:
        text = self.memory_input.text().strip()
        if not text:
            return
        try:
            self.services.memory_add(text, kind=self.kind_combo.currentData())
        except ValueError as exc:
            self.status.setText(str(exc))
            return
        self.memory_input.clear()
        self.refresh()
        self.memoryChanged.emit()

    def memory_forget_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        text = self.table.item(row, 2).text()
        self.services.memory_forget(text)
        self.refresh()
        self.memoryChanged.emit()

    def memory_clear(self) -> None:
        if QMessageBox.question(self, "AgentBetta", "Delete all long-term memories?") == QMessageBox.Yes:
            removed = self.services.memory_clear()
            self.refresh()
            self.memoryChanged.emit()
            QMessageBox.information(self, "AgentBetta", f"Deleted {removed} memories.")

    def open_memory_folder(self) -> None:
        target = self.services.memory_path().parent
        target.mkdir(parents=True, exist_ok=True)
        startfile = getattr(os, "startfile", None)
        if startfile is not None:
            startfile(str(target))
        else:  # pragma: no cover - non-Windows
            self.status.setText(str(target))
