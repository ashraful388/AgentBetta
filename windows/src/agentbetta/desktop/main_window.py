"""Main window: three-pane agent console.

Left: navigation (New Task, Chats, Projects, Agents, Memory, Settings, Guide, About).
Center: task composer, execution stream, results and artifacts.
Right: the live Run Inspector (model, configuration, tools, permissions, usage,
verification).
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from agentbetta import __version__
from agentbetta.desktop.assets import app_icon, logo_pixmap
from agentbetta.desktop.icons import icon
from agentbetta.desktop.services import AppServices
from agentbetta.desktop.theme import apply_theme, current_tokens, resolve_theme
from agentbetta.desktop.views.about_view import AboutView
from agentbetta.desktop.views.agents_view import AgentsView
from agentbetta.desktop.views.chats_view import ChatsView
from agentbetta.desktop.views.guide_view import GuideView
from agentbetta.desktop.views.memory_view import MemoryView
from agentbetta.desktop.views.projects_view import ProjectsView
from agentbetta.desktop.views.settings_view import SettingsView
from agentbetta.desktop.views.task_view import TaskView
from agentbetta.desktop.widgets.inspector import InspectorPanel

_NAV = [
    ("New Task", "tasks"),
    ("Chats", "chats"),
    ("Projects", "projects"),
    ("Agents", "agents"),
    ("Memory", "memory"),
    ("Settings", "settings"),
    ("Guide", "guide"),
    ("About", "about"),
]

_THEME_CYCLE = {"system": "light", "light": "dark", "dark": "system"}


class MainWindow(QMainWindow):
    def __init__(self, services: AppServices, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self._pending_update: Any = None
        self._update_worker: Any = None
        self.setWindowTitle("AgentBetta")
        self.setWindowIcon(app_icon())
        self.resize(1380, 900)
        self.setMinimumSize(1120, 700)

        central = QWidget()
        central.setObjectName("AppRoot")
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setObjectName("CenterPane")
        self.task_view = TaskView(services)
        self.chats_view = ChatsView(services)
        self.projects_view = ProjectsView(services)
        self.agents_view = AgentsView(services)
        self.memory_view = MemoryView(services)
        self.settings_view = SettingsView(services)
        self.guide_view = GuideView()
        self.about_view = AboutView()
        for view in (
            self.task_view,
            self.chats_view,
            self.projects_view,
            self.agents_view,
            self.memory_view,
            self.settings_view,
            self.guide_view,
            self.about_view,
        ):
            self.stack.addWidget(view)
        body.addWidget(self.stack, 1)

        self.inspector = InspectorPanel()
        body.addWidget(self.inspector)
        root.addLayout(body, 1)

        self.setCentralWidget(central)

        self.nav.currentRowChanged.connect(self._on_nav)
        self.nav.setCurrentRow(0)
        self._wire()

        self.statusBar().showMessage(f"AgentBetta {__version__} — ready")

        if services.settings.general.auto_check_updates:
            QTimer.singleShot(1500, lambda: self._check_updates(silent=True))

    # -- updates ----------------------------------------------------------
    def _check_updates(self, *, silent: bool = False) -> None:
        from agentbetta.desktop.workers import CallWorker

        if self._update_worker is not None and self._update_worker.isRunning():
            return
        self.update_button.setText("Checking…")
        self.update_button.setEnabled(False)
        worker = CallWorker(self.services.check_for_updates, self)
        self._update_worker = worker
        worker.done.connect(lambda info: self._on_update_checked(info, silent=silent))
        worker.failed.connect(lambda message: self._on_update_failed(message, silent=silent))
        worker.start()

    def _on_update_checked(self, info: Any, *, silent: bool = False) -> None:
        self.update_button.setEnabled(True)
        self._pending_update = info
        if info is not None:
            self.update_button.setText(f"Update {info.version}")
            self.update_button.setObjectName("Primary")
            self.update_button.setIcon(icon("update", current_tokens().on_accent, 18))
            self._repolish(self.update_button)
            self.statusBar().showMessage(
                f"Update available: AgentBetta {info.version} — click Update."
            )
        else:
            self.update_button.setText("Updates")
            self.update_button.setObjectName("Ghost")
            self.update_button.setIcon(icon("update", current_tokens().text_muted, 18))
            self._repolish(self.update_button)
            if not silent:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.information(
                    self, "AgentBetta", f"You are running the latest version ({__version__})."
                )

    def _on_update_failed(self, message: str, *, silent: bool = False) -> None:
        self.update_button.setEnabled(True)
        self.update_button.setText("Updates")
        if not silent:
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "AgentBetta", f"Update check failed: {message}")

    def _open_update_dialog(self) -> None:
        if self._pending_update is None:
            self._check_updates(silent=False)
            return
        from agentbetta.desktop.widgets.update_dialog import UpdateDialog

        UpdateDialog(self.services, self._pending_update, self).exec()

    @staticmethod
    def _repolish(widget: Any) -> None:
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    # -- chrome -----------------------------------------------------------
    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("HeaderBar")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        mark = QLabel()
        mark.setObjectName("BrandLogo")
        mark.setPixmap(logo_pixmap(44))
        mark.setAlignment(Qt.AlignCenter)
        layout.addWidget(mark)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        name = QLabel("AgentBetta™")
        name.setObjectName("BrandName")
        tag = QLabel("Adaptive AI Nano-Agent · verified task completion")
        tag.setObjectName("BrandTag")
        titles.addWidget(name)
        titles.addWidget(tag)
        layout.addLayout(titles)
        layout.addStretch(1)

        self.update_button = QPushButton("Updates")
        self.update_button.setObjectName("Ghost")
        self.update_button.setToolTip("Check for updates")
        self.update_button.setIcon(icon("update", current_tokens().text_muted, 18))
        self.update_button.clicked.connect(self._open_update_dialog)
        layout.addWidget(self.update_button)

        self.inspector_toggle = QPushButton("Inspector")
        self.inspector_toggle.setObjectName("Ghost")
        self.inspector_toggle.setCheckable(True)
        self.inspector_toggle.setChecked(True)
        self.inspector_toggle.setIcon(icon("inspector", current_tokens().text_muted, 18))
        layout.addWidget(self.inspector_toggle)

        self.theme_button = QPushButton()
        self.theme_button.setObjectName("Ghost")
        self.theme_button.clicked.connect(self._cycle_theme)
        self._update_theme_button()
        layout.addWidget(self.theme_button)
        return header

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(238)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        label = QLabel("NAVIGATION")
        label.setObjectName("NavSection")
        layout.addWidget(label)

        self.nav = QListWidget()
        self.nav.setObjectName("NavList")
        self.nav.setFrameShape(QListWidget.NoFrame)
        self.nav.setIconSize(QSize(22, 22))
        for text, icon_name in _NAV:
            item = QListWidgetItem(icon(icon_name, current_tokens().text_muted, 22), text)
            self.nav.addItem(item)
        layout.addWidget(self.nav, 1)

        footer = QLabel(f"Windows desktop client · {__version__}")
        footer.setObjectName("NavSection")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        return sidebar

    def _wire(self) -> None:
        self.inspector_toggle.toggled.connect(self.inspector.setVisible)
        self.task_view.inspectorUpdated.connect(self._on_inspector)
        self.task_view.chatChanged.connect(self.chats_view.refresh)
        self.chats_view.openChatRequested.connect(self._open_chat)
        self.projects_view.useInTaskRequested.connect(self._use_project)
        self.projects_view.openChatRequested.connect(self._open_chat)
        self.settings_view.settingsChanged.connect(self._on_settings_changed)
        self.memory_view.memoryChanged.connect(self.settings_view.refresh_memory)

    # -- navigation -------------------------------------------------------
    def _on_nav(self, row: int) -> None:
        if row < 0 or row >= self.stack.count():
            return
        self.stack.setCurrentIndex(row)
        self.inspector.setVisible(row == 0 and self.inspector_toggle.isChecked())
        if row == 4:
            self.memory_view.refresh()
        elif row == 2:
            self.projects_view.refresh()
        elif row == 1:
            self.chats_view.refresh()
        elif row == 0:
            self.task_view.reload_settings()

    def _use_project(self, name: str, folder: str | None) -> None:
        self.task_view.set_project(name, folder)
        self.nav.setCurrentRow(0)

    def _open_chat(self, conversation_id: str) -> None:
        if not conversation_id:
            self.task_view.new_chat()
        else:
            conversation = self.services.chats.get(conversation_id)
            if conversation is not None:
                self.task_view.load_conversation(conversation)
        self.nav.setCurrentRow(0)

    def _on_settings_changed(self) -> None:
        from PySide6.QtWidgets import QApplication

        apply_theme(QApplication.instance(), self.services.settings.general.theme)
        self.task_view.reload_settings()
        self.memory_view.refresh()
        self.projects_view.refresh()
        self._refresh_icons()

    # -- inspector --------------------------------------------------------
    def _on_inspector(self, payload: Any) -> None:
        if not isinstance(payload, dict):
            return
        phase = payload.get("phase")
        if phase == "start":
            self.inspector.set_run_context(
                model_label=payload.get("model_label", ""),
                profile=payload.get("profile", ""),
                mode=payload.get("mode", ""),
                local_only=bool(payload.get("local_only")),
            )
        elif phase == "event":
            self.inspector.on_event(payload.get("event"))
        elif phase == "summary":
            self.inspector.set_summary(payload.get("summary") or {})
        elif phase == "failed":
            self.inspector.set_summary(
                {"error": payload.get("message"), "verification": {"status": "ERROR",
                 "reason": payload.get("message", "")}}
            )

    # -- theme ------------------------------------------------------------
    def _cycle_theme(self) -> None:
        from PySide6.QtWidgets import QApplication

        general = self.services.settings.general
        order = ("system", "light", "dark")
        current_visible = resolve_theme(general.theme)
        start = order.index(general.theme) if general.theme in order else 0
        # Skip a target that resolves to the same visible theme (e.g. System is
        # Light on a light Windows theme) so every click visibly changes theme.
        for offset in (1, 2):
            candidate = order[(start + offset) % len(order)]
            if resolve_theme(candidate) != current_visible:
                general.theme = candidate
                break
        else:
            general.theme = _THEME_CYCLE.get(general.theme, "light")
        self.services.save()
        apply_theme(QApplication.instance(), general.theme)
        self._refresh_icons()

    def _update_theme_button(self) -> None:
        theme = self.services.settings.general.theme
        resolved = resolve_theme(theme)
        self.theme_button.setText(f"Theme: {theme.capitalize()}")
        self.theme_button.setToolTip("Cycle System → Light → Dark")
        self.theme_button.setIcon(
            icon("moon" if resolved == "dark" else "sun", current_tokens().text_muted, 18)
        )

    def _refresh_icons(self) -> None:
        tokens = current_tokens()
        for row, (_, icon_name) in enumerate(_NAV):
            item = self.nav.item(row)
            if item is not None:
                item.setIcon(icon(icon_name, tokens.text_muted, 22))
        self.inspector_toggle.setIcon(icon("inspector", tokens.text_muted, 18))
        if self._pending_update is not None:
            self.update_button.setIcon(icon("update", tokens.on_accent, 18))
        else:
            self.update_button.setIcon(icon("update", tokens.text_muted, 18))
        self.task_view.refresh_icons()
        self._update_theme_button()
