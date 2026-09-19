"""First-run onboarding.

Shown when no usable provider/model is configured, so the user gets guidance
instead of a failing task.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)

from agentbetta.desktop.services import AppServices
from agentbetta.permissions import PROFILES
from agentbetta.settings import ModelProfile, profile_from_preset


class OnboardingDialog(QDialog):
    def __init__(self, services: AppServices, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self.setWindowTitle("Welcome to AgentBetta")
        self.setMinimumWidth(560)
        self._ollama_models: list[str] = []

        layout = QVBoxLayout(self)
        welcome = QLabel(
            "<h2>Welcome to AgentBetta</h2>"
            "<p>Choose a model source. Local Ollama needs no API key.</p>"
        )
        welcome.setWordWrap(True)
        layout.addWidget(welcome)

        row = QHBoxLayout()
        self.endpoint = QLineEdit("http://127.0.0.1:11434")
        detect = QPushButton("Detect Ollama")
        detect.clicked.connect(self.detect_ollama)
        row.addWidget(QLabel("Ollama endpoint:"))
        row.addWidget(self.endpoint, 1)
        row.addWidget(detect)
        layout.addLayout(row)

        self.models = QListWidget()
        layout.addWidget(self.models)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        add_provider = QPushButton("Add a cloud / custom provider...")
        add_provider.setObjectName("secondary")
        add_provider.clicked.connect(self.add_cloud_provider)
        layout.addWidget(add_provider)

        perm_row = QHBoxLayout()
        self.profile_combo = QComboBox()
        for key, profile in PROFILES.items():
            self.profile_combo.addItem(profile.label, key)
        perm_row.addWidget(QLabel("Default permissions:"))
        perm_row.addWidget(self.profile_combo, 1)
        layout.addLayout(perm_row)

        buttons = QHBoxLayout()
        finish = QPushButton("Finish")
        finish.clicked.connect(self.finish)
        buttons.addStretch(1)
        buttons.addWidget(finish)
        layout.addLayout(buttons)

    def detect_ollama(self) -> None:
        endpoint = self.endpoint.text().strip()
        ok, message, models = self.services.ollama_status(endpoint)
        self._ollama_models = models
        self.models.clear()
        for model in models:
            self.models.addItem(model)
        self.status.setText(("Detected. " if ok else "Not available. ") + message)
        if ok and models:
            self._apply_ollama(endpoint, models)

    def _apply_ollama(self, endpoint: str, models: list[str]) -> None:
        settings = self.services.settings
        profile = next((p for p in settings.providers if p.type == "ollama"), None)
        if profile is None:
            profile = profile_from_preset("ollama", base_url=endpoint or None)
            settings.providers.append(profile)
        profile.base_url = endpoint
        for index, model_id in enumerate(models):
            uid = f"{profile.id}::{model_id}"
            if not any(m.uid == uid for m in settings.models):
                settings.models.append(
                    ModelProfile(provider_id=profile.id, model_id=model_id,
                                 display_name=model_id, tier=min(index, 2), is_local=True)
                )
            settings.tier_map.setdefault(str(min(index, 2)), uid)
        self.services.save()

    def add_cloud_provider(self) -> None:
        from agentbetta.desktop.views.settings_view import ProviderDialog

        dialog = ProviderDialog(self.services, None, self)
        if dialog.exec() == QDialog.Accepted:
            profile = dialog.result_profile()
            self.services.settings.providers.append(profile)
            dialog.apply_secret()
            if profile.default_model:
                self.services.settings.models.append(
                    ModelProfile(provider_id=profile.id, model_id=profile.default_model,
                                 display_name=profile.default_model, is_local=not profile.is_cloud)
                )
                self.services.settings.tier_map.setdefault("0", f"{profile.id}::{profile.default_model}")
            self.services.save()

    def finish(self) -> None:
        general = self.services.settings.general
        general.first_run_complete = True
        general.default_permission_profile = self.profile_combo.currentData()
        self.services.save()
        self.accept()
