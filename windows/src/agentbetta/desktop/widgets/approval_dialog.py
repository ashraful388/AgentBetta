"""High-risk action approval dialog.

Shows the concrete action, target, permission, risk class and reason, and
offers Allow once / Allow for run / Deny. This is the only authorization
mechanism for high-risk actions: the model cannot approve itself.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from agentbetta.desktop.widgets.ui import Card, badge, divider, muted
from agentbetta.permissions import ApprovalDecision

_RISK_TONE = {"low": "muted", "medium": "info", "high": "danger", "destructive": "danger"}


class ApprovalDialog(QDialog):
    def __init__(self, request: Any, parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("AgentBetta permission request")
        self.setMinimumWidth(560)
        self._decision = ApprovalDecision.DENY

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("High-risk action requested")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(badge(str(getattr(request, "risk", "high")).upper(),
                               _RISK_TONE.get(str(getattr(request, "risk", "")), "danger")))
        layout.addLayout(header)

        layout.addWidget(muted(
            "AgentBetta needs your approval before performing this action. Review the exact "
            "tool and arguments below."
        ))

        card = Card()
        rows = [
            ("Tool", getattr(request, "tool_name", "—")),
            ("Permission", getattr(request, "permission", None) or "none"),
            ("Risk class", getattr(request, "risk", "—")),
            ("Reason", getattr(request, "reason", "—")),
        ]
        for key, value in rows:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10)
            key_label = QLabel(str(key))
            key_label.setObjectName("FieldLabel")
            key_label.setMinimumWidth(90)
            value_label = QLabel(str(value))
            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            row_layout.addWidget(key_label)
            row_layout.addWidget(value_label, 1)
            card.add(row)
        card.add(divider())
        args_label = QLabel("Arguments")
        args_label.setObjectName("FieldLabel")
        card.add(args_label)
        args_view = QPlainTextEdit()
        args_view.setReadOnly(True)
        args_view.setPlainText(self._format_args(getattr(request, "arguments", {})))
        args_view.setMaximumHeight(120)
        card.add(args_view)
        layout.addWidget(card)

        buttons = QHBoxLayout()
        deny = QPushButton("Deny")
        deny.setObjectName("Danger")
        allow_once = QPushButton("Allow once")
        allow_run = QPushButton("Allow for run")
        allow_run.setObjectName("Primary")
        deny.clicked.connect(lambda: self._choose(ApprovalDecision.DENY))
        allow_once.clicked.connect(lambda: self._choose(ApprovalDecision.ALLOW_ONCE))
        allow_run.clicked.connect(lambda: self._choose(ApprovalDecision.ALLOW_RUN))
        buttons.addWidget(deny)
        buttons.addStretch(1)
        buttons.addWidget(allow_once)
        buttons.addWidget(allow_run)
        layout.addLayout(buttons)

    @staticmethod
    def _format_args(arguments: dict[str, Any]) -> str:
        if not arguments:
            return "(none)"
        return "\n".join(f"{key}: {value}" for key, value in sorted(arguments.items()))

    def _choose(self, decision: ApprovalDecision) -> None:
        self._decision = decision
        self.accept()

    def decision(self) -> ApprovalDecision:
        return self._decision
