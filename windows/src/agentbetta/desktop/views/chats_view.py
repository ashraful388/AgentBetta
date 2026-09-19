"""Chats view: all saved conversations, with a preview."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from agentbetta.desktop.services import AppServices
from agentbetta.desktop.widgets.ui import Card, SectionHeader, muted


class ChatsView(QWidget):
    openChatRequested = Signal(str)
    changed = Signal()

    def __init__(self, services: AppServices, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self._chats: list[Any] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(
            SectionHeader(
                "Chats",
                "Every conversation is saved automatically. Open one to continue it.",
            )
        )

        toolbar = QHBoxLayout()
        self.open_button = QPushButton("Open chat")
        self.open_button.setObjectName("Primary")
        self.open_button.clicked.connect(self.open_selected)
        delete = QPushButton("Delete")
        delete.setObjectName("Danger")
        delete.clicked.connect(self.delete_selected)
        refresh = QPushButton("Refresh")
        refresh.setObjectName("Ghost")
        refresh.clicked.connect(self.refresh)
        new_chat = QPushButton("New chat")
        new_chat.setObjectName("Ghost")
        new_chat.clicked.connect(self.new_chat)
        toolbar.addWidget(self.open_button)
        toolbar.addWidget(new_chat)
        toolbar.addWidget(refresh)
        toolbar.addStretch(1)
        toolbar.addWidget(delete)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Chat", "Project", "Messages", "Updated", "Status"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 110)
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.doubleClicked.connect(self.open_selected)
        layout.addWidget(self.table, 1)

        preview = Card("Preview")
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        preview.add(self.preview)
        layout.addWidget(preview, 1)

        self.info = muted("")
        layout.addWidget(self.info)

    # -- data -------------------------------------------------------------
    def refresh(self) -> None:
        self._chats = self.services.chats.all()
        self.table.setRowCount(0)
        for chat in self._chats:
            row = self.table.rowCount()
            self.table.insertRow(row)
            status = "—" if chat.verified is None else ("verified" if chat.verified else "not verified")
            values = [
                chat.title,
                chat.project or "—",
                str(len(chat.messages)),
                chat.updated_at[:19].replace("T", " "),
                status,
            ]
            for index, value in enumerate(values):
                self.table.setItem(row, index, QTableWidgetItem(value))
        self.info.setText(f"{len(self._chats)} chat(s)")
        if self._chats:
            self.table.selectRow(0)
        else:
            self.preview.clear()

    def _selected(self) -> Any:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._chats):
            return None
        return self._chats[row]

    def _on_selection(self) -> None:
        chat = self._selected()
        if chat is None:
            return
        lines: list[str] = []
        for message in chat.messages:
            if message.role == "user":
                lines.append(f"**You:** {message.text}")
            elif message.role == "agent":
                lines.append(message.text)
            else:
                lines.append(f"_{message.text}_")
        self.preview.setMarkdown("\n\n".join(lines) or "_(empty)_")

    def open_selected(self) -> None:
        chat = self._selected()
        if chat is not None:
            self.openChatRequested.emit(chat.id)

    def delete_selected(self) -> None:
        chat = self._selected()
        if chat is None:
            return
        if QMessageBox.question(self, "AgentBetta", f"Delete chat '{chat.title}'?") == QMessageBox.Yes:
            self.services.chats.remove(chat.id)
            self.refresh()
            self.changed.emit()

    def new_chat(self) -> None:
        self.openChatRequested.emit("")
