"""Top-level User Guide / documentation view."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from agentbetta.desktop.guide import USER_GUIDE
from agentbetta.desktop.widgets.ui import SectionHeader


class GuideView(QWidget):
    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)
        layout.addWidget(
            SectionHeader(
                "User Guide",
                "How to configure and use AgentBetta — models, permissions, tasks, "
                "browser, memory, updates and troubleshooting.",
            )
        )
        view = QTextBrowser()
        view.setOpenExternalLinks(True)
        view.setMarkdown(USER_GUIDE)
        layout.addWidget(view, 1)
