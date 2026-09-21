"""Main task screen: a chat-style console with a compact composer."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from agentbetta.desktop.chats import Conversation
from agentbetta.desktop.icons import icon
from agentbetta.desktop.services import AppServices, RunRequest
from agentbetta.desktop.theme import current_tokens
from agentbetta.desktop.widgets.chat import ChatTranscript
from agentbetta.desktop.widgets.report import build_result_markdown
from agentbetta.desktop.widgets.ui import Card, SectionHeader, badge, set_badge_tone
from agentbetta.desktop.workers import RunWorker
from agentbetta.permissions import PROFILES

_WRITE_TOOLS = {
    "write_text_file_global",
    "append_text_file",
    "create_directory",
    "copy_path",
    "move_path",
    "browser_download",
    "browser_screenshot",
}

_FOLLOWUP_CUES = re.compile(
    r"\b(it|its|this|that|these|those|them|again|continue|continuing|also|"
    r"instead|above|previous|last|same|run it|do it|fix it|now)\b",
    re.IGNORECASE,
)


def _is_followup(objective: str, has_prior_output: bool) -> bool:
    """Heuristic: a short message in an ongoing chat, or one referencing prior
    work, is a follow-up that needs the previous assistant output as context."""

    if not has_prior_output or not objective.strip():
        return False
    if len(objective.strip()) < 200:
        return True
    return bool(_FOLLOWUP_CUES.search(objective))


def _extract_artifacts(tool_results: list[dict[str, Any]]) -> list[str]:
    artifacts: list[str] = []
    for result in tool_results or []:
        if not result.get("ok") or result.get("tool_name") not in _WRITE_TOOLS:
            continue
        output = result.get("output") or ""
        try:
            data = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            data = None
        if isinstance(data, dict):
            for key in ("path", "destination", "file", "saved"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    artifacts.append(value)
        summary = result.get("arguments_summary") or ""
        for token in summary.split(","):
            if "=" in token:
                key, _, value = token.partition("=")
                if key.strip() in ("path", "destination") and value.strip():
                    artifacts.append(value.strip())
    seen: set[str] = set()
    unique: list[str] = []
    for path in artifacts:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


class _Composer(QPlainTextEdit):
    submitted = Signal()

    def keyPressEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (
            event.modifiers() & Qt.ShiftModifier
        ):
            self.submitted.emit()
            return
        super().keyPressEvent(event)


class TaskView(QWidget):
    historyChanged = Signal()
    chatChanged = Signal()
    inspectorUpdated = Signal(object)

    def __init__(self, services: AppServices, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self.worker: RunWorker | None = None
        self.attachments: list[str] = []
        self._context_folder: str | None = None
        self._context_name: str | None = None
        self._conversation: Conversation | None = None
        self._build_ui()
        self.reload_settings()

    # -- UI ---------------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.addWidget(
            SectionHeader(
                "New Task",
                "Describe the outcome. AgentBetta configures model, context, tools and "
                "permissions per task, then verifies the result.",
            )
        )
        header.addStretch(1)
        self.status_badge = badge("IDLE", "muted")
        header.addWidget(self.status_badge, 0, Qt.AlignTop)
        clear = QPushButton("New chat")
        clear.setObjectName("Ghost")
        clear.setIcon(icon("clear", current_tokens().text_muted, 16))
        clear.clicked.connect(self.new_chat)
        header.addWidget(clear, 0, Qt.AlignTop)
        layout.addLayout(header)

        self.transcript = ChatTranscript()
        self.output = self.transcript  # compatibility alias
        self.transcript.copyText.connect(lambda _text: self._say_status("Copied to clipboard"))
        self.transcript.rate.connect(self._on_rate)
        self.transcript.regenerate.connect(self._regenerate)
        self.transcript.editUser.connect(self._edit_user)
        self.transcript.resendUser.connect(self._resend_user)
        layout.addWidget(self.transcript, 1)

        composer_card = Card()
        self.composer = _Composer()
        self.composer.setPlaceholderText(
            "Message AgentBetta…  (Enter to send, Shift+Enter for a new line)"
        )
        self.composer.setMinimumHeight(64)
        self.composer.setMaximumHeight(140)
        self.composer.submitted.connect(self.run_task)
        composer_card.add(self.composer)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.attach_button = QPushButton()
        self.attach_button.setObjectName("Ghost")
        self.attach_button.setToolTip("Attach files")
        self.attach_button.setIcon(icon("attach", current_tokens().text_muted, 16))
        self.attach_button.clicked.connect(self.attach_files)
        self.advanced_toggle = QPushButton("Advanced")
        self.advanced_toggle.setObjectName("Ghost")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setIcon(icon("chevron", current_tokens().text_muted, 16))
        self.advanced_toggle.toggled.connect(self._toggle_advanced)
        toolbar.addWidget(self.attach_button)
        toolbar.addWidget(self.advanced_toggle)
        toolbar.addStretch(1)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(180)
        self.profile_combo = QComboBox()
        toolbar.addWidget(QLabel("Model"))
        toolbar.addWidget(self.model_combo)
        toolbar.addWidget(QLabel("Permissions"))
        toolbar.addWidget(self.profile_combo)
        self.run_button = QPushButton("Run")
        self.run_button.setObjectName("Primary")
        self.run_button.setIcon(icon("send", current_tokens().on_accent, 16))
        self.run_button.clicked.connect(self._on_action)
        toolbar.addWidget(self.run_button)
        composer_card.add_layout(toolbar)

        self.advanced = QWidget()
        advanced_layout = QHBoxLayout(self.advanced)
        advanced_layout.setContentsMargins(0, 4, 0, 0)
        self.local_only = QCheckBox("Local only")
        self.mode_combo = QComboBox()
        for mode in ("adaptive", "fixed", "wholesale"):
            self.mode_combo.addItem(mode, mode)
        self.context_badge = badge("No context folder", "muted")
        context_button = QPushButton("Context folder…")
        context_button.setObjectName("Ghost")
        context_button.setIcon(icon("folder", current_tokens().text_muted, 16))
        context_button.clicked.connect(self.choose_workspace)
        clear_context = QPushButton("Clear")
        clear_context.setObjectName("Ghost")
        clear_context.clicked.connect(self._clear_workspace)
        advanced_layout.addWidget(self.local_only)
        advanced_layout.addWidget(QLabel("Mode"))
        advanced_layout.addWidget(self.mode_combo)
        advanced_layout.addWidget(context_button)
        advanced_layout.addWidget(self.context_badge)
        advanced_layout.addWidget(clear_context)
        advanced_layout.addStretch(1)
        self.advanced.setVisible(False)
        composer_card.add(self.advanced)

        layout.addWidget(composer_card)
        self._welcome()

    def _welcome(self) -> None:
        self.transcript.add_agent(
            "Hi — I'm **AgentBetta**. Tell me what you'd like to get done and I'll "
            "configure the model, tools and permissions for the task, run it, and "
            "verify the result. Nothing runs with more access than the permission "
            "profile you choose.",
            actions=False,
        )

    def _toggle_advanced(self, checked: bool) -> None:
        self.advanced.setVisible(checked)

    def refresh_icons(self) -> None:
        tokens = current_tokens()
        self.attach_button.setIcon(icon("attach", tokens.text_muted, 16))
        self.advanced_toggle.setIcon(icon("chevron", tokens.text_muted, 16))
        if self._running():
            self.run_button.setIcon(icon("stop", tokens.danger, 16))
        else:
            self.run_button.setIcon(icon("send", tokens.on_accent, 16))

    # -- conversations ----------------------------------------------------
    def _persist(self) -> None:
        if self._conversation is not None:
            self.services.chats.upsert(self._conversation)

    def _say_user(self, text: str) -> None:
        conversation = self._conversation or Conversation()
        if not conversation.messages:
            conversation.title = text.strip().replace("\n", " ")[:60] or "New chat"
        conversation.project = self._context_name or conversation.project
        message = conversation.add("user", text)
        self._conversation = conversation
        self.transcript.add_user(text, message_id=message.id)
        self._persist()

    def _say_agent(self, markdown: str) -> None:
        if self._conversation is not None:
            message = self._conversation.add("agent", markdown)
            self.transcript.add_agent(markdown, message_id=message.id)
            self._persist()
        else:
            self.transcript.add_agent(markdown)

    def _say_status(self, text: str) -> None:
        self.transcript.add_status(text)
        if self._conversation is not None:
            self._conversation.add("status", text)
            self._persist()

    def _on_rate(self, message_id: str, value: int) -> None:
        if self._conversation is None:
            return
        for message in self._conversation.messages:
            if message.id == message_id:
                message.rating = value
                break
        self._persist()

    def _last_user_text(self) -> str:
        if self._conversation is None:
            return ""
        for message in reversed(self._conversation.messages):
            if message.role == "user":
                return message.text
        return ""

    def _regenerate(self) -> None:
        text = self._last_user_text()
        if text and not self._running():
            self.composer.setPlainText(text)
            self.run_task()

    def _edit_user(self, text: str) -> None:
        self.composer.setPlainText(text)
        self.composer.setFocus()

    def _resend_user(self, text: str) -> None:
        if not self._running():
            self.composer.setPlainText(text)
            self.run_task()

    def new_chat(self) -> None:
        self._conversation = None
        self.transcript.clear()
        set_badge_tone(self.status_badge, "IDLE")
        self._welcome()

    def load_conversation(self, conversation: Conversation) -> None:
        self._conversation = conversation
        self.transcript.clear()
        for message in conversation.messages:
            if message.role == "user":
                self.transcript.add_user(message.text, message_id=message.id)
            elif message.role == "agent":
                self.transcript.add_agent(
                    message.text, message_id=message.id, rating=message.rating
                )
            else:
                self.transcript.add_status(message.text)
        if not conversation.messages:
            self._welcome()
        if conversation.verified is None:
            set_badge_tone(self.status_badge, "IDLE")
        else:
            set_badge_tone(self.status_badge, "VERIFIED" if conversation.verified else "NOT VERIFIED")

    # -- data -------------------------------------------------------------
    def reload_settings(self) -> None:
        self.model_combo.clear()
        for uid, label in self.services.model_choices():
            self.model_combo.addItem(label, uid)
        self.profile_combo.clear()
        for key, profile in PROFILES.items():
            self.profile_combo.addItem(profile.label, key)
        index = self.profile_combo.findData(
            self.services.settings.general.default_permission_profile
        )
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)
        self.mode_combo.setCurrentIndex(
            max(0, self.mode_combo.findData(self.services.settings.general.default_mode))
        )
        self.local_only.setChecked(self.services.settings.general.local_only_default)

    def load_objective(self, objective: str, workspace: str | None = None) -> None:
        self.composer.setPlainText(objective)
        if workspace:
            self._set_context(os.path.basename(workspace.rstrip("\\/")) or workspace, workspace)
        self.composer.setFocus()

    def set_project(self, name: str, folder: str | None) -> None:
        self._set_context(name, folder)

    def _set_context(self, name: str | None, folder: str | None) -> None:
        self._context_name = name
        self._context_folder = folder
        set_badge_tone(self.context_badge, name or "No context folder", "info" if name else "muted")

    def choose_workspace(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose a context folder (optional)")
        if folder:
            self._set_context(os.path.basename(folder.rstrip("\\/")) or folder, folder)

    def _clear_workspace(self) -> None:
        self._set_context(None, None)

    def _workspace(self) -> str | None:
        return self._context_folder

    def attach_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Attach files")
        if files:
            self.attachments = files
            self._say_status(f"{len(files)} attachment(s) ready")

    # -- run --------------------------------------------------------------
    def _running(self) -> bool:
        return self.worker is not None and self.worker.isRunning()

    def _on_action(self) -> None:
        if self._running():
            self.stop_task()
        else:
            self.run_task()

    def _previous_agent_output(self) -> str:
        if self._conversation is None:
            return ""
        for message in reversed(self._conversation.messages):
            if message.role == "agent" and message.text.strip():
                return message.text
        return ""

    def run_task(self) -> None:
        objective = self.composer.toPlainText().strip()
        if not objective or self._running():
            return
        selection = self.model_combo.currentData() or "auto"
        profile = self.profile_combo.currentData() or "safe"
        mode = self.mode_combo.currentData() or "adaptive"
        previous_output = self._previous_agent_output()
        followup_output = (
            previous_output if _is_followup(objective, bool(previous_output)) else None
        )
        request = RunRequest(
            objective=objective,
            selection=selection,
            profile=profile,
            mode=mode,
            local_only=self.local_only.isChecked(),
            privacy=self.services.settings.general.privacy_mode,
            workspace=self._workspace(),
            inputs=list(self.attachments),
            previous_output=followup_output,
        )
        self._say_user(objective)
        self.composer.clear()
        self._set_running(True)
        self.transcript.show_thinking()
        self.chatChanged.emit()
        self.inspectorUpdated.emit(
            {
                "phase": "start",
                "model_label": self.model_combo.currentText(),
                "profile": PROFILES[profile].label if profile in PROFILES else profile,
                "mode": mode,
                "local_only": self.local_only.isChecked(),
            }
        )
        self.worker = RunWorker(self.services, request, self)
        self.worker.event.connect(self.on_event)
        self.worker.approvalRequired.connect(self.on_approval)
        self.worker.completed.connect(self.on_completed)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def stop_task(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            self._say_status("Cancelling…")

    def _set_running(self, running: bool) -> None:
        tokens = current_tokens()
        if running:
            self.run_button.setText("Stop")
            self.run_button.setObjectName("Danger")
            self.run_button.setIcon(icon("stop", tokens.danger, 16))
            set_badge_tone(self.status_badge, "RUNNING")
        else:
            self.run_button.setText("Run")
            self.run_button.setObjectName("Primary")
            self.run_button.setIcon(icon("send", tokens.on_accent, 16))
        style = self.run_button.style()
        style.unpolish(self.run_button)
        style.polish(self.run_button)

    _STATUS_EVENTS = {
        "tool_started": lambda d: f"Using {d.get('tool_name')}…",
        "tool_finished": lambda d: f"{d.get('tool_name')} {'succeeded' if d.get('ok') else 'failed'}",
        "adaptation_recorded": lambda d: "Adapting: " + ", ".join(d.get("changed_dimensions", []) or []),
        "verification_updated": lambda d: f"Verification: {d.get('status')}",
    }

    def on_event(self, event: Any) -> None:
        handler = self._STATUS_EVENTS.get(event.type)
        if handler is not None:
            try:
                self._say_status(handler(event.data or {}))
            except Exception:
                pass
        self.inspectorUpdated.emit({"phase": "event", "event": event})

    def on_approval(self, payload: Any) -> None:
        from agentbetta.desktop.widgets.approval_dialog import ApprovalDialog

        approval_request, holder, done = payload
        try:
            dialog = ApprovalDialog(approval_request, self)
            dialog.exec()
            holder["decision"] = dialog.decision()
        finally:
            done.set()

    def on_completed(self, summary: dict[str, Any]) -> None:
        self.transcript.hide_thinking()
        self._set_running(False)
        self._say_agent(build_result_markdown(summary))
        verified = summary.get("verified")
        if summary.get("cancelled"):
            set_badge_tone(self.status_badge, "CANCELLED")
        elif summary.get("error"):
            set_badge_tone(self.status_badge, "FAILED")
        else:
            set_badge_tone(self.status_badge, "VERIFIED" if verified else "NOT VERIFIED")
        artifacts = _extract_artifacts(summary.get("tool_results") or [])
        if artifacts:
            self._say_status("Artifacts: " + "  ·  ".join(artifacts))
        if self._conversation is not None:
            self._conversation.run_id = summary.get("run_id")
            self._conversation.verified = bool(verified)
            self._persist()
        self.inspectorUpdated.emit({"phase": "summary", "summary": summary})
        self.historyChanged.emit()
        self.chatChanged.emit()

    def on_failed(self, message: str) -> None:
        self.transcript.hide_thinking()
        self._set_running(False)
        set_badge_tone(self.status_badge, "FAILED")
        self._say_agent(
            "**The run failed.**\n\n"
            f"{message}\n\n"
            "Open **Settings ▸ Diagnostics** for details. If the provider is unreachable, "
            "check the endpoint and API key."
        )
        self.inspectorUpdated.emit({"phase": "failed", "message": message})
        self.historyChanged.emit()
        self.chatChanged.emit()
