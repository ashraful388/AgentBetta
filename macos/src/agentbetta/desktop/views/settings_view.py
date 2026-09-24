"""Settings surface: General, Providers & Models, Local Models, Model Tiers,
Tools & Permissions, Browser & Web, Privacy & Data, Diagnostics."""

from __future__ import annotations

import os
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from agentbetta import __version__
from agentbetta.desktop.guide import USER_GUIDE
from agentbetta.desktop.services import AppServices
from agentbetta.desktop.workers import CallWorker
from agentbetta.permissions import PROFILES, inspect_profiles
from agentbetta.platform import paths
from agentbetta.settings import ModelProfile, ProviderProfile, preset, profile_from_preset


class ProviderDialog(QDialog):
    def __init__(self, services: AppServices, profile: ProviderProfile | None = None, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self._profile = profile
        self.setWindowTitle("Provider")
        self.setMinimumWidth(480)
        layout = QFormLayout(self)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("(choose a preset)", "")
        from agentbetta.settings import PRESETS

        for key, item in PRESETS.items():
            self.preset_combo.addItem(item.label, key)
        self.name_edit = QLineEdit(profile.name if profile else "")
        self.type_combo = QComboBox()
        self.type_combo.addItem("Ollama (local)", "ollama")
        self.type_combo.addItem("OpenAI-compatible", "openai_compatible")
        self.base_url_edit = QLineEdit(profile.base_url if profile else "")
        self.default_model_edit = QLineEdit((profile.default_model if profile else "") or "")
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 1800)
        self.timeout_spin.setValue(profile.timeout if profile else 120)
        self.is_cloud_check = QCheckBox("This is a cloud provider")
        self.is_cloud_check.setChecked(profile.is_cloud if profile else True)
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(profile.enabled if profile else True)
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText("Leave blank to keep existing key")
        self.clear_key_check = QCheckBox("Delete stored API key")
        self.key_status = QLabel("")

        layout.addRow("Preset:", self.preset_combo)
        layout.addRow("Name:", self.name_edit)
        layout.addRow("Type:", self.type_combo)
        layout.addRow("Base URL:", self.base_url_edit)
        layout.addRow("Default model:", self.default_model_edit)
        layout.addRow("Timeout (s):", self.timeout_spin)
        layout.addRow("", self.is_cloud_check)
        layout.addRow("", self.enabled_check)
        layout.addRow("API key:", self.key_edit)
        layout.addRow("", self.clear_key_check)
        layout.addRow("", self.key_status)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.preset_combo.currentIndexChanged.connect(self._apply_preset)
        self._refresh_key_status()

    def _apply_preset(self) -> None:
        key = self.preset_combo.currentData()
        if not key:
            return
        p = preset(key)
        if p is None:
            return
        self.name_edit.setText(p.label)
        self.type_combo.setCurrentIndex(0 if p.type == "ollama" else 1)
        self.base_url_edit.setText(p.base_url)
        self.default_model_edit.setText(p.default_model or "")
        self.is_cloud_check.setChecked(p.is_cloud)

    def _refresh_key_status(self) -> None:
        from agentbetta.settings import keyring_available

        if not keyring_available():
            self.key_status.setText(
                "⚠ Secure storage is unavailable — keys will NOT be saved after the app closes."
            )
            return
        if self._profile and self.services.secret_store.get_secret(self._profile.secret_ref()):
            self.key_status.setText("A key is stored securely (Windows Credential Manager).")
        else:
            self.key_status.setText("No key stored.")

    def result_profile(self) -> ProviderProfile:
        if self._profile is None:
            self._profile = ProviderProfile()
        self._profile.name = self.name_edit.text().strip() or "Provider"
        self._profile.type = self.type_combo.currentData()
        self._profile.base_url = self.base_url_edit.text().strip()
        self._profile.default_model = self.default_model_edit.text().strip() or None
        self._profile.timeout = self.timeout_spin.value()
        self._profile.is_cloud = self.is_cloud_check.isChecked()
        self._profile.enabled = self.enabled_check.isChecked()
        return self._profile

    def accept(self) -> None:  # noqa: D102 - Qt override
        profile = self.result_profile()
        if profile.type == "ollama":
            url = (profile.base_url or "").lower()
            local_markers = ("localhost", "127.0.0.1", "0.0.0.0", "[::1]")
            if url and not any(marker in url for marker in local_markers):
                answer = QMessageBox.warning(
                    self,
                    "AgentBetta",
                    "Type is set to 'Ollama (local)' but the endpoint is not a local "
                    "address:\n\n"
                    f"{profile.base_url}\n\n"
                    "If this is a cloud or OpenAI-compatible endpoint, change Type to "
                    "'OpenAI-compatible'. Save anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if answer != QMessageBox.Yes:
                    return
        super().accept()

    def apply_secret(self) -> None:
        ref = self._profile.secret_ref()
        if self.clear_key_check.isChecked():
            self.services.secret_store.delete_secret(ref)
        elif self.key_edit.text():
            self.services.secret_store.set_secret(ref, self.key_edit.text())


class SettingsView(QWidget):
    settingsChanged = Signal()
    updateCheckRequested = Signal()

    def __init__(self, services: AppServices, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self._workers: list[CallWorker] = []
        self._build_ui()
        self.reload()

    def _start_worker(self, function: Any, on_done: Any, on_error: Any) -> None:
        worker = CallWorker(function, self)
        worker.done.connect(on_done)
        worker.failed.connect(on_error)
        self._workers.append(worker)
        worker.start()

    # -- construction -----------------------------------------------------
    def _build_ui(self) -> None:
        from agentbetta.desktop.widgets.ui import SectionHeader

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)
        layout.addWidget(
            SectionHeader(
                "Settings",
                "Providers, models, permissions, browser, memory, privacy and diagnostics.",
            )
        )
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self.tabs.addTab(self._build_general_tab(), "General")
        self.tabs.addTab(self._build_providers_tab(), "Providers & Models")
        self.tabs.addTab(self._build_local_tab(), "Local Models")
        self.tabs.addTab(self._build_tiers_tab(), "Model Tiers")
        self.tabs.addTab(self._build_permissions_tab(), "Tools & Permissions")
        self.tabs.addTab(self._build_browser_tab(), "Browser & Web")
        self.tabs.addTab(self._build_memory_tab(), "Memory")
        self.tabs.addTab(self._build_privacy_tab(), "Privacy & Data")
        self.tabs.addTab(self._build_diagnostics_tab(), "Diagnostics")
        self.tabs.addTab(self._build_guide_tab(), "User Guide")

        buttons = QHBoxLayout()
        self.save_button = QPushButton("Save settings")
        self.save_button.clicked.connect(self.save)
        buttons.addStretch(1)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)

    def _build_general_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.theme_combo = QComboBox()
        for key in ("system", "light", "dark"):
            self.theme_combo.addItem(key, key)
        self.default_mode_combo = QComboBox()
        for key in ("adaptive", "fixed", "wholesale"):
            self.default_mode_combo.addItem(key, key)
        self.default_profile_combo = QComboBox()
        for key, profile in PROFILES.items():
            self.default_profile_combo.addItem(profile.label, key)
        self.data_dir_edit = QLineEdit()
        self.privacy_check = QCheckBox("Privacy mode (redact task text in records)")
        self.local_only_default_check = QCheckBox("Default to Local only")
        form.addRow("Theme:", self.theme_combo)
        form.addRow("Default run mode:", self.default_mode_combo)
        form.addRow("Default permission profile:", self.default_profile_combo)
        form.addRow("Run/data directory:", self.data_dir_edit)
        self.max_run_spin = QSpinBox()
        self.max_run_spin.setRange(0, 86400)
        self.max_run_spin.setSpecialValueText("No limit")
        self.max_run_spin.setSuffix(" s")
        self.max_run_spin.setToolTip(
            "Wall-clock limit for a whole run. 'No limit' lets a task run until it "
            "finishes, is cancelled, or reaches a step/resource bound."
        )
        form.addRow("Time limit per run:", self.max_run_spin)

        self.unlimited_check = QCheckBox("No token or time limits (run until finished)")
        self.unlimited_check.setToolTip(
            "When enabled, runs have no token budget, no per-call timeout and no "
            "turn/tool-call cap. Disable to let AgentBetta bound and adapt resources."
        )
        self.unlimited_check.toggled.connect(self.max_run_spin.setDisabled)
        form.addRow("Limits:", self.unlimited_check)
        form.addRow("", self.privacy_check)
        form.addRow("", self.local_only_default_check)

        self.provider_fallback_check = QCheckBox(
            "Fall back to another configured model if the selected model fails"
        )
        form.addRow("Reliability:", self.provider_fallback_check)

        self.auto_update_check = QCheckBox("Check for updates on startup")
        self.update_channel_combo = QComboBox()
        self.update_channel_combo.addItem("Stable", "stable")
        self.update_channel_combo.addItem("Pre-release", "prerelease")
        self.update_repo_edit = QLineEdit()
        self.update_repo_edit.setPlaceholderText("owner/repo on GitHub, e.g. yourname/AgentBetta")
        self.update_status = QLabel("")
        self.update_status.setObjectName("Muted")
        self.update_check_button = QPushButton("Check for updates now")
        self.update_check_button.setObjectName("Ghost")
        self.update_check_button.clicked.connect(self.check_updates_now)
        form.addRow("Updates:", self.auto_update_check)
        form.addRow("Update channel:", self.update_channel_combo)
        form.addRow("Update source:", self.update_repo_edit)
        form.addRow("", self.update_check_button)
        form.addRow("", self.update_status)
        return widget

    def _build_providers_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.provider_table = QTableWidget(0, 5)
        self.provider_table.setHorizontalHeaderLabels(["Name", "Type", "Endpoint", "Cloud", "Enabled"])
        self.provider_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.provider_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.provider_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.provider_table)
        row = QHBoxLayout()
        for label, slot in (
            ("Add", self.add_provider),
            ("Edit", self.edit_provider),
            ("Remove", self.remove_provider),
            ("Toggle enabled", self.toggle_provider),
            ("Test connection", self.test_provider),
            ("Refresh models", self.refresh_models),
        ):
            button = QPushButton(label)
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch(1)
        layout.addLayout(row)
        self.provider_status = QLabel("")
        layout.addWidget(self.provider_status)
        return widget

    def _build_local_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.ollama_endpoint_edit = QLineEdit("http://127.0.0.1:11434")
        form.addRow("Ollama endpoint:", self.ollama_endpoint_edit)
        layout.addLayout(form)
        row = QHBoxLayout()
        test_button = QPushButton("Test Ollama")
        test_button.clicked.connect(self.test_ollama)
        refresh_button = QPushButton("Refresh installed models")
        refresh_button.clicked.connect(self.refresh_ollama)
        add_button = QPushButton("Add selected to catalog")
        add_button.clicked.connect(self.add_selected_ollama_models)
        row.addWidget(test_button)
        row.addWidget(refresh_button)
        row.addWidget(add_button)
        row.addStretch(1)
        layout.addLayout(row)
        self.ollama_models = QListWidget()
        layout.addWidget(self.ollama_models)
        self.ollama_status = QLabel("")
        layout.addWidget(self.ollama_status)
        return widget

    def _build_tiers_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.tier_combos: dict[int, QComboBox] = {}
        for tier, label in ((0, "Tier 0 — economical"), (1, "Tier 1 — standard"), (2, "Tier 2 — high capability")):
            combo = QComboBox()
            self.tier_combos[tier] = combo
            form.addRow(label + ":", combo)
        note = QLabel("Auto (AgentBetta) selects the model mapped to the active model tier.")
        note.setWordWrap(True)
        form.addRow(note)
        return widget

    def _build_permissions_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.permission_profile_combo = QComboBox()
        for key, profile in PROFILES.items():
            self.permission_profile_combo.addItem(profile.label, key)
        form.addRow("Default profile:", self.permission_profile_combo)
        self.auto_approve_check = QCheckBox(
            "Automatically approve high-risk actions (no prompts)"
        )
        self.auto_approve_check.setToolTip(
            "When enabled, high-risk actions (delete, shell, downloads, …) run without "
            "a prompt for any profile. The Full Computer profile already does this."
        )
        form.addRow("Approvals:", self.auto_approve_check)
        layout.addLayout(form)
        self.permissions_view = QTextBrowser()
        layout.addWidget(self.permissions_view)
        warning = QLabel("Full Computer grants broad access but never bypasses Windows security, UAC or hard denies.")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        return widget

    def _build_browser_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.browser_enabled_check = QCheckBox("Browser tools enabled")
        self.browser_engine_combo = QComboBox()
        self.browser_engine_combo.addItem("Microsoft Edge", "msedge")
        self.browser_engine_combo.addItem("Chromium (Playwright)", "chromium")
        self.browser_visible_check = QCheckBox("Show the browser window")
        self.download_dir_edit = QLineEdit()
        form.addRow("", self.browser_enabled_check)
        form.addRow("Preferred engine:", self.browser_engine_combo)
        form.addRow("", self.browser_visible_check)
        form.addRow("Download directory:", self.download_dir_edit)
        clear = QPushButton("Clear AgentBetta browser data")
        clear.clicked.connect(self.clear_browser_data)
        form.addRow(clear)
        return widget

    def _build_memory_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        form = QFormLayout()
        self.memory_enabled_check = QCheckBox("Enable global long-term memory")
        self.memory_auto_capture_check = QCheckBox(
            "Automatically capture verified outcomes and explicit 'remember' statements"
        )
        self.memory_max_spin = QSpinBox()
        self.memory_max_spin.setRange(10, 100_000)
        self.memory_retrieve_spin = QSpinBox()
        self.memory_retrieve_spin.setRange(0, 50)
        self.memory_embeddings_check = QCheckBox("Use local Ollama embeddings (optional)")
        self.memory_embedding_model_edit = QLineEdit()
        form.addRow("", self.memory_enabled_check)
        form.addRow("", self.memory_auto_capture_check)
        form.addRow("Maximum stored memories:", self.memory_max_spin)
        form.addRow("Memories injected per run:", self.memory_retrieve_spin)
        form.addRow("", self.memory_embeddings_check)
        form.addRow("Embedding model:", self.memory_embedding_model_edit)
        layout.addLayout(form)

        add_row = QHBoxLayout()
        self.memory_input = QLineEdit()
        self.memory_input.setPlaceholderText("Add a memory, e.g. 'I prefer concise answers'")
        add_button = QPushButton("Add memory")
        add_button.clicked.connect(self.memory_add)
        add_row.addWidget(self.memory_input, 1)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

        self.memory_list = QListWidget()
        layout.addWidget(self.memory_list)
        row = QHBoxLayout()
        for label, slot in (
            ("Refresh", self.refresh_memory),
            ("Forget selected", self.memory_forget_selected),
            ("Clear all", self.memory_clear),
            ("Open memory folder", self.open_memory_folder),
        ):
            button = QPushButton(label)
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch(1)
        layout.addLayout(row)
        self.memory_status = QLabel("")
        layout.addWidget(self.memory_status)
        return widget

    def _build_privacy_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.privacy_view = QLabel("")
        layout.addWidget(self.privacy_view)
        row = QHBoxLayout()
        clear_history = QPushButton("Clear run history")
        clear_history.clicked.connect(self._clear_history)
        open_runs = QPushButton("Open runs folder")
        open_runs.clicked.connect(lambda: self._open(os.fspath(self.services.runs_dir)))
        clear_keys = QPushButton("Delete all stored API keys")
        clear_keys.clicked.connect(self._clear_keys)
        row.addWidget(clear_history)
        row.addWidget(open_runs)
        row.addWidget(clear_keys)
        row.addStretch(1)
        layout.addLayout(row)
        return widget

    def _build_diagnostics_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.diagnostics_view = QTextBrowser()
        layout.addWidget(self.diagnostics_view)
        row = QHBoxLayout()
        open_logs = QPushButton("Open logs folder")
        open_logs.clicked.connect(lambda: self._open(os.fspath(paths.logs_dir())))
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_diagnostics)
        row.addWidget(open_logs)
        row.addWidget(refresh)
        row.addStretch(1)
        layout.addLayout(row)
        return widget

    def _build_guide_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        view = QTextBrowser()
        view.setOpenExternalLinks(True)
        view.setMarkdown(USER_GUIDE)
        layout.addWidget(view)
        return widget

    # -- load/save --------------------------------------------------------
    def reload(self) -> None:
        general = self.services.settings.general
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(general.theme)))
        self.default_mode_combo.setCurrentIndex(max(0, self.default_mode_combo.findData(general.default_mode)))
        self.default_profile_combo.setCurrentIndex(
            max(0, self.default_profile_combo.findData(general.default_permission_profile))
        )
        self.data_dir_edit.setText(general.data_dir or "")
        self.max_run_spin.setValue(int(getattr(general, "max_run_seconds", 0) or 0))
        self.unlimited_check.setChecked(bool(getattr(general, "unlimited", True)))
        self.max_run_spin.setDisabled(self.unlimited_check.isChecked())
        self.privacy_check.setChecked(general.privacy_mode)
        self.local_only_default_check.setChecked(general.local_only_default)
        self.provider_fallback_check.setChecked(general.provider_fallback)
        self.auto_update_check.setChecked(general.auto_check_updates)
        self.update_channel_combo.setCurrentIndex(
            max(0, self.update_channel_combo.findData(general.update_channel))
        )
        self.update_repo_edit.setText(general.update_repo or "")
        self.update_status.setText("")
        self.permission_profile_combo.setCurrentIndex(
            max(0, self.permission_profile_combo.findData(general.default_permission_profile))
        )
        self.auto_approve_check.setChecked(bool(getattr(general, "auto_approve_high_risk", False)))
        self.browser_enabled_check.setChecked(general.browser_enabled)
        self.browser_engine_combo.setCurrentIndex(
            max(0, self.browser_engine_combo.findData(general.browser_engine))
        )
        self.browser_visible_check.setChecked(general.browser_visible)
        self.download_dir_edit.setText(general.browser_download_dir or "")
        self.memory_enabled_check.setChecked(general.memory_enabled)
        self.memory_auto_capture_check.setChecked(general.memory_auto_capture)
        self.memory_max_spin.setValue(general.memory_max_entries)
        self.memory_retrieve_spin.setValue(general.memory_retrieve)
        self.memory_embeddings_check.setChecked(general.memory_embeddings)
        self.memory_embedding_model_edit.setText(general.memory_embedding_model)
        self.refresh_memory()
        self.privacy_view.setText(f"Run records: {self.services.runs_dir}\n(privacy mode redacts task text)")
        self.refresh_provider_table()
        self.refresh_tiers()
        self._render_permissions()
        self.refresh_diagnostics()

    def save(self) -> None:
        general = self.services.settings.general
        general.theme = self.theme_combo.currentData()
        general.default_mode = self.default_mode_combo.currentData()
        general.default_permission_profile = self.default_profile_combo.currentData()
        general.data_dir = self.data_dir_edit.text().strip() or None
        general.unlimited = self.unlimited_check.isChecked()
        general.max_run_seconds = 0 if general.unlimited else self.max_run_spin.value()
        general.auto_approve_high_risk = self.auto_approve_check.isChecked()
        general.privacy_mode = self.privacy_check.isChecked()
        general.local_only_default = self.local_only_default_check.isChecked()
        general.provider_fallback = self.provider_fallback_check.isChecked()
        general.auto_check_updates = self.auto_update_check.isChecked()
        general.update_channel = self.update_channel_combo.currentData()
        general.update_repo = self.update_repo_edit.text().strip()
        general.browser_enabled = self.browser_enabled_check.isChecked()
        general.browser_engine = self.browser_engine_combo.currentData()
        general.browser_visible = self.browser_visible_check.isChecked()
        general.browser_download_dir = self.download_dir_edit.text().strip() or None
        general.memory_enabled = self.memory_enabled_check.isChecked()
        general.memory_auto_capture = self.memory_auto_capture_check.isChecked()
        general.memory_max_entries = self.memory_max_spin.value()
        general.memory_retrieve = self.memory_retrieve_spin.value()
        general.memory_embeddings = self.memory_embeddings_check.isChecked()
        general.memory_embedding_model = self.memory_embedding_model_edit.text().strip() or "nomic-embed-text"
        for tier, combo in self.tier_combos.items():
            uid = combo.currentData()
            if uid:
                self.services.settings.tier_map[str(tier)] = uid
            else:
                self.services.settings.tier_map.pop(str(tier), None)
        self._persist()
        self.refresh_memory()
        self.refresh_diagnostics()
        QMessageBox.information(self, "AgentBetta", "Settings saved.")

    def _persist(self) -> None:
        self.services.save()
        self.settingsChanged.emit()

    # -- updates ----------------------------------------------------------
    def check_updates_now(self) -> None:
        general = self.services.settings.general
        repo = self.update_repo_edit.text().strip()
        if not repo or "/" not in repo:
            self.update_status.setText("Enter a GitHub update source in owner/repo format.")
            return
        general.auto_check_updates = self.auto_update_check.isChecked()
        general.update_channel = self.update_channel_combo.currentData()
        general.update_repo = repo
        self.services.save()
        self.update_check_button.setEnabled(False)
        self.update_status.setText("Checking for updates…")
        self.updateCheckRequested.emit()

    def finish_update_check(self, info: Any, error: str = "") -> None:
        self.update_check_button.setEnabled(True)
        if error:
            self.update_status.setText(f"Check failed: {error}")
        elif info is None:
            self.update_status.setText(f"You are running the latest version ({__version__}).")
        else:
            self.update_status.setText(f"Update available: {info.version}")

    # -- providers --------------------------------------------------------
    def refresh_provider_table(self) -> None:
        self.provider_table.setRowCount(0)
        for profile in self.services.settings.providers:
            row = self.provider_table.rowCount()
            self.provider_table.insertRow(row)
            values = [
                profile.name,
                profile.type,
                profile.base_url,
                "cloud" if profile.is_cloud else "local",
                "yes" if profile.enabled else "no",
            ]
            for index, value in enumerate(values):
                self.provider_table.setItem(row, index, QTableWidgetItem(value))

    def _selected_provider(self) -> ProviderProfile | None:
        row = self.provider_table.currentRow()
        providers = self.services.settings.providers
        if row < 0 or row >= len(providers):
            return None
        return providers[row]

    def add_provider(self) -> None:
        dialog = ProviderDialog(self.services, None, self)
        if dialog.exec() == QDialog.Accepted:
            profile = dialog.result_profile()
            self.services.settings.providers.append(profile)
            dialog.apply_secret()
            self._ensure_default_model(profile)
            self._persist()
            self.refresh_provider_table()

    def edit_provider(self) -> None:
        profile = self._selected_provider()
        if profile is None:
            return
        dialog = ProviderDialog(self.services, profile, self)
        if dialog.exec() == QDialog.Accepted:
            dialog.result_profile()
            dialog.apply_secret()
            self._ensure_default_model(profile)
            self._persist()
            self.refresh_provider_table()

    def _ensure_default_model(self, profile: ProviderProfile) -> None:
        if not profile.default_model:
            return
        uid = f"{profile.id}::{profile.default_model}"
        if any(m.uid == uid for m in self.services.settings.models):
            return
        used_tiers = {m.tier for m in self.services.settings.models}
        tier = next((t for t in (0, 1, 2) if t not in used_tiers), 1)
        self.services.settings.models.append(
            ModelProfile(
                provider_id=profile.id,
                model_id=profile.default_model,
                display_name=profile.default_model,
                tier=tier,
                is_local=not profile.is_cloud,
            )
        )

    def remove_provider(self) -> None:
        profile = self._selected_provider()
        if profile is None:
            return
        self.services.secret_store.delete_secret(profile.secret_ref())
        self.services.settings.providers.remove(profile)
        # Drop the removed provider's catalog models and any tier assignment
        # that pointed at them, so the model selector cannot offer orphans.
        self.services.settings.prune_orphan_models()
        self._persist()
        self.refresh_provider_table()

    def toggle_provider(self) -> None:
        profile = self._selected_provider()
        if profile is None:
            return
        profile.enabled = not profile.enabled
        self._persist()
        self.refresh_provider_table()

    def test_provider(self) -> None:
        profile = self._selected_provider()
        if profile is None:
            self.provider_status.setText("Select a provider first.")
            return
        self.provider_status.setText("Testing...")
        self._start_worker(
            lambda: self.services.test_provider(profile),
            lambda result: self.provider_status.setText(
                ("OK: " if result[0] else "FAILED: ") + result[1]
            ),
            lambda message: self.provider_status.setText("FAILED: " + message),
        )

    def refresh_models(self) -> None:
        profile = self._selected_provider()
        if profile is None:
            self.provider_status.setText("Select a provider first.")
            return
        self.provider_status.setText("Refreshing models...")

        def on_done(models: list[str]) -> None:
            for model_id in models:
                self._add_model(profile.id, model_id, is_local=not profile.is_cloud)
            self.provider_status.setText(f"{len(models)} model(s) added to catalog.")
            self.refresh_tiers()

        self._start_worker(
            lambda: self.services.refresh_models(profile),
            on_done,
            lambda message: self.provider_status.setText("FAILED: " + message),
        )

    # -- local models -----------------------------------------------------
    def test_ollama(self) -> None:
        endpoint = self.ollama_endpoint_edit.text().strip()
        self.ollama_status.setText("Testing...")
        self._start_worker(
            lambda: self.services.ollama_status(endpoint),
            lambda result: self.ollama_status.setText(("OK: " if result[0] else "FAILED: ") + result[1]),
            lambda message: self.ollama_status.setText("FAILED: " + message),
        )

    def refresh_ollama(self) -> None:
        endpoint = self.ollama_endpoint_edit.text().strip()
        self.ollama_status.setText("Refreshing...")

        def on_done(result: tuple[bool, str, list[str]]) -> None:
            ok, message, models = result
            self.ollama_models.clear()
            for model in models:
                self.ollama_models.addItem(model)
            self.ollama_status.setText(("OK: " if ok else "FAILED: ") + message)

        self._start_worker(
            lambda: self.services.ollama_status(endpoint),
            on_done,
            lambda message: self.ollama_status.setText("FAILED: " + message),
        )

    def _ensure_ollama_provider(self) -> ProviderProfile:
        for profile in self.services.settings.providers:
            if profile.type == "ollama":
                return profile
        profile = profile_from_preset("ollama", base_url=self.ollama_endpoint_edit.text().strip() or None)
        self.services.settings.providers.append(profile)
        self._persist()
        self.refresh_provider_table()
        return profile

    def add_selected_ollama_models(self) -> None:
        items = self.ollama_models.selectedItems() or [
            self.ollama_models.item(i) for i in range(self.ollama_models.count())
        ]
        if not items:
            return
        profile = self._ensure_ollama_provider()
        for item in items:
            self._add_model(profile.id, item.text(), is_local=True)
        self.refresh_tiers()

    # -- model catalog ----------------------------------------------------
    def _add_model(self, provider_id: str, model_id: str, *, is_local: bool) -> None:
        existing = [m for m in self.services.settings.models if m.uid == f"{provider_id}::{model_id}"]
        if existing:
            return
        used_tiers = {m.tier for m in self.services.settings.models}
        tier = next((t for t in (0, 1, 2) if t not in used_tiers), 1)
        self.services.settings.models.append(
            ModelProfile(
                provider_id=provider_id,
                model_id=model_id,
                display_name=model_id,
                tier=tier,
                is_local=is_local,
                supports_tools=True,
            )
        )
        self._persist()

    def refresh_tiers(self) -> None:
        choices = [("(none)", None)] + [
            (f"{m.display_name or m.model_id} — {m.model_id}", m.uid) for m in self.services.settings.models
        ]
        for tier, combo in self.tier_combos.items():
            current = self.services.settings.tier_map.get(str(tier))
            combo.clear()
            for label, uid in choices:
                combo.addItem(label, uid)
            if current:
                index = combo.findData(current)
                if index >= 0:
                    combo.setCurrentIndex(index)

    # -- permissions ------------------------------------------------------
    def _render_permissions(self) -> None:
        lines = []
        for key, info in inspect_profiles().items():
            lines.append(f"### {PROFILES[key].label} ({key})")
            lines.append(PROFILES[key].description)
            lines.append(f"- allowed: {', '.join(info['allowed']) or 'none'}")
            lines.append(f"- adaptively eligible: {', '.join(info['eligible']) or 'none'}")
            lines.append(f"- hard denied: {', '.join(info['hard_denied']) or 'none'}")
            lines.append("")
        self.permissions_view.setMarkdown("\n".join(lines))

    # -- privacy/diagnostics ---------------------------------------------
    # -- memory -----------------------------------------------------------
    def refresh_memory(self) -> None:
        self.memory_list.clear()
        entries = self.services.memory_entries()
        for entry in entries:
            self.memory_list.addItem(f"[{entry.get('kind')}] {entry.get('text')}")
        self.memory_status.setText(f"{len(entries)} memory entries")

    def memory_add(self) -> None:
        text = self.memory_input.text().strip()
        if not text:
            return
        try:
            self.services.memory_add(text)
        except ValueError as exc:
            self.memory_status.setText(str(exc))
            return
        self.memory_input.clear()
        self.refresh_memory()

    def memory_forget_selected(self) -> None:
        items = self.memory_list.selectedItems()
        if not items:
            return
        payload = items[0].text().split("] ", 1)[-1]
        self.services.memory_forget(payload)
        self.refresh_memory()

    def memory_clear(self) -> None:
        if QMessageBox.question(self, "AgentBetta", "Delete all long-term memories?") == QMessageBox.Yes:
            removed = self.services.memory_clear()
            self.refresh_memory()
            QMessageBox.information(self, "AgentBetta", f"Deleted {removed} memories.")

    def open_memory_folder(self) -> None:
        self._open(os.fspath(self.services.memory_path().parent))

    def _clear_history(self) -> None:
        if QMessageBox.question(self, "AgentBetta", "Delete all run history?") == QMessageBox.Yes:
            removed = self.services.clear_history()
            QMessageBox.information(self, "AgentBetta", f"Removed {removed} run(s).")

    def _clear_keys(self) -> None:
        if QMessageBox.question(self, "AgentBetta", "Delete all stored API keys?") != QMessageBox.Yes:
            return
        for profile in self.services.settings.providers:
            self.services.secret_store.delete_secret(profile.secret_ref())
        QMessageBox.information(self, "AgentBetta", "Stored API keys deleted.")

    def clear_browser_data(self) -> None:
        import shutil

        target = paths.browser_dir()
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        QMessageBox.information(self, "AgentBetta", "AgentBetta browser data cleared.")

    def refresh_diagnostics(self) -> None:
        from agentbetta.tools.browser import browser_available
        from agentbetta.settings import keyring_available

        browser_ok, browser_message = browser_available()
        lines = [
            f"AgentBetta version: {__version__}",
            f"Python: {os.sys.version.split()[0]}",
            f"Settings: {self.services.settings_store.path}",
            f"Run records: {self.services.runs_dir}",
            f"Logs: {paths.logs_path()}",
            f"Browser profile: {paths.browser_profile_dir()}",
            f"Secret store: {'Windows Credential Manager' if keyring_available() else 'session-only (keyring unavailable)'}",
            f"Browser: {browser_message}",
            f"Configured providers: {len(self.services.settings.providers)}",
            f"Catalog models: {len(self.services.settings.models)}",
        ]
        self.diagnostics_view.setPlainText("\n".join(lines))

    def _open(self, path: str) -> None:
        startfile = getattr(os, "startfile", None)
        if startfile is not None:
            startfile(path)
