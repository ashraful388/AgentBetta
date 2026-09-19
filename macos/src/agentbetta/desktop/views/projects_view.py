"""Projects view.

Projects are optional task context (name + folder + preferred profile/model).
They are not a filesystem boundary; permissions still govern access.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
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

from agentbetta.desktop.projects import Project
from agentbetta.desktop.services import AppServices
from agentbetta.desktop.widgets.ui import SectionHeader, muted
from agentbetta.permissions import PROFILES


class ProjectDialog(QDialog):
    def __init__(self, services: AppServices, project: Project | None = None, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self._project = project
        self.setWindowTitle("Project")
        self.setMinimumWidth(460)
        layout = QFormLayout(self)

        self.name_edit = QLineEdit(project.name if project else "")
        self.name_edit.setPlaceholderText("e.g. Literature review")
        folder_row = QWidget()
        folder_layout = QHBoxLayout(folder_row)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        self.folder_edit = QLineEdit(project.folder if project else "")
        browse = QPushButton("Browse…")
        browse.setObjectName("Ghost")
        browse.clicked.connect(self._browse)
        folder_layout.addWidget(self.folder_edit, 1)
        folder_layout.addWidget(browse)

        self.profile_combo = QComboBox()
        self.profile_combo.addItem("(use default)", "")
        for key, profile in PROFILES.items():
            self.profile_combo.addItem(profile.label, key)
        self.model_combo = QComboBox()
        self.model_combo.addItem("(use default)", "")
        for uid, label in services.model_choices():
            if uid == "auto":
                continue
            self.model_combo.addItem(label, uid)
        self.notes_edit = QLineEdit(project.notes if project else "")

        layout.addRow("Name:", self.name_edit)
        layout.addRow("Folder:", folder_row)
        layout.addRow("Permission profile:", self.profile_combo)
        layout.addRow("Preferred model:", self.model_combo)
        layout.addRow("Notes:", self.notes_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if project:
            self.profile_combo.setCurrentIndex(max(0, self.profile_combo.findData(project.profile)))
            self.model_combo.setCurrentIndex(max(0, self.model_combo.findData(project.model)))

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose project folder")
        if folder:
            self.folder_edit.setText(folder)

    def result_project(self) -> Project:
        project = self._project or Project(name="")
        project.name = self.name_edit.text().strip() or "Untitled project"
        project.folder = self.folder_edit.text().strip()
        project.profile = self.profile_combo.currentData() or ""
        project.model = self.model_combo.currentData() or ""
        project.notes = self.notes_edit.text().strip()
        return project


class ProjectsView(QWidget):
    useInTaskRequested = Signal(str, object)
    openChatRequested = Signal(str)

    def __init__(self, services: AppServices, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self._projects: list[Project] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(
            SectionHeader(
                "Projects",
                "Reusable task context. A project is a convenience, never a filesystem boundary.",
            )
        )

        toolbar = QHBoxLayout()
        for label, slot, name in (
            ("New project", self.add_project, "Primary"),
            ("Edit", self.edit_project, ""),
            ("Remove", self.remove_project, "Danger"),
            ("Refresh", self.refresh, "Ghost"),
        ):
            button = QPushButton(label)
            if name:
                button.setObjectName(name)
            button.clicked.connect(slot)
            toolbar.addWidget(button)
        toolbar.addStretch(1)
        self.use_button = QPushButton("Use in New Task")
        self.use_button.setObjectName("Primary")
        self.use_button.clicked.connect(self.use_selected)
        toolbar.addWidget(self.use_button)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Project", "Folder", "Default profile", "Last used"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 160)
        self.table.doubleClicked.connect(self.use_selected)
        self.table.itemSelectionChanged.connect(self._refresh_project_chats)
        layout.addWidget(self.table, 1)

        self.chat_table = QTableWidget(0, 3)
        self.chat_table.setHorizontalHeaderLabels(["Chat in this project", "Messages", "Updated"])
        self.chat_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.chat_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.chat_table.setAlternatingRowColors(True)
        self.chat_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.chat_table.setColumnWidth(1, 90)
        self.chat_table.setColumnWidth(2, 150)
        self.chat_table.doubleClicked.connect(self._open_project_chat)
        layout.addWidget(self.chat_table, 1)
        self._project_chats: list[Any] = []

        self.info = muted("")
        layout.addWidget(self.info)

    def refresh(self) -> None:
        self._projects = self.services.projects.load()
        self.table.setRowCount(0)
        for project in self._projects:
            row = self.table.rowCount()
            self.table.insertRow(row)
            profile_label = PROFILES[project.profile].label if project.profile in PROFILES else "—"
            values = [
                project.name,
                project.folder or "—",
                profile_label,
                (project.last_used_at or "—")[:19].replace("T", " "),
            ]
            for index, value in enumerate(values):
                self.table.setItem(row, index, QTableWidgetItem(value))
        self.info.setText(f"{len(self._projects)} project(s)")
        self._refresh_project_chats()

    def _selected(self) -> Project | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._projects):
            return None
        return self._projects[row]

    def _refresh_project_chats(self) -> None:
        project = self._selected()
        self._project_chats = self.services.chats.for_project(project.name) if project else []
        self.chat_table.setRowCount(0)
        for chat in self._project_chats:
            row = self.chat_table.rowCount()
            self.chat_table.insertRow(row)
            values = [
                chat.title,
                str(len(chat.messages)),
                chat.updated_at[:19].replace("T", " "),
            ]
            for index, value in enumerate(values):
                self.chat_table.setItem(row, index, QTableWidgetItem(value))

    def _open_project_chat(self) -> None:
        row = self.chat_table.currentRow()
        if 0 <= row < len(self._project_chats):
            self.openChatRequested.emit(self._project_chats[row].id)

    def add_project(self) -> None:
        dialog = ProjectDialog(self.services, None, self)
        if dialog.exec() == QDialog.Accepted:
            self.services.projects.add(dialog.result_project())
            self.refresh()

    def edit_project(self) -> None:
        project = self._selected()
        if project is None:
            return
        dialog = ProjectDialog(self.services, project, self)
        if dialog.exec() == QDialog.Accepted:
            self.services.projects.update(dialog.result_project())
            self.refresh()

    def remove_project(self) -> None:
        project = self._selected()
        if project is None:
            return
        if QMessageBox.question(self, "AgentBetta", f"Remove project '{project.name}'?") == QMessageBox.Yes:
            self.services.projects.remove(project.id)
            self.refresh()

    def use_selected(self) -> None:
        project = self._selected()
        if project is None:
            return
        self.services.projects.touch(project.id)
        self.useInTaskRequested.emit(project.name, project.folder or None)
        self.refresh()
