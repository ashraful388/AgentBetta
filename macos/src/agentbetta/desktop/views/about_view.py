"""About screen."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from agentbetta import __version__
from agentbetta.desktop.assets import full_logo_pixmap
from agentbetta.desktop.widgets.ui import Card, KeyValueGrid, SectionHeader, badge, muted
from agentbetta.platform import PLATFORM_NAME

_IS_MAC = PLATFORM_NAME == "macos"


class AboutView(QWidget):
    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(14)

        logo = QLabel()
        logo.setPixmap(full_logo_pixmap(340))
        logo.setAlignment(Qt.AlignLeft)
        outer.addWidget(logo)

        header = QHBoxLayout()
        header.addWidget(
            SectionHeader(
                "AgentBetta™",
                "An adaptive AI nano-agent for efficient, verified task completion.",
            )
        )
        header.addStretch(1)
        version_badge = badge(f"v{__version__}", "accent")
        header.addWidget(version_badge, 0, Qt.AlignTop)
        outer.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(14)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        overview = Card("How it works")
        overview.add(muted(
            "AgentBetta configures its intelligence, context, tools, permissions, memory and "
            "computational resources for each task, verifies the outcome, and selectively "
            "expands only the dimensions that were insufficient. It does not silently escalate "
            "permissions, and it cannot certify success from model text alone when an "
            "independent validator is available."
        ))
        layout.addWidget(overview)

        developer = Card("Developer")
        dev_grid = KeyValueGrid()
        dev_grid.set_rows(
            [
                ("Name", "Dr. Md. Ashraful Babu"),
                ("Role", "Associate Professor of Mathematics"),
                ("Department", "Department of Physical Sciences"),
                ("University", "Independent University, Bangladesh (IUB)"),
                ("Location", "Dhaka, Bangladesh"),
            ]
        )
        developer.add(dev_grid)
        links = QLabel()
        links.setTextFormat(Qt.RichText)
        links.setOpenExternalLinks(True)
        links.setWordWrap(True)
        links.setText(
            '<a href="https://iub.ac.bd/academics/departments/ps/faculty-and-staff/ashraful388">'
            "IUB faculty profile</a> &nbsp;·&nbsp; "
            '<a href="https://scholar.google.com/citations?hl=en&user=kAz9guAAAAAJ&view_op=list_works&sortby=pubdate">'
            "Google Scholar</a> &nbsp;·&nbsp; "
            '<a href="https://www.scopus.com/pages/authors/57212215763">Scopus</a>'
        )
        developer.add(links)
        layout.addWidget(developer)

        details = Card("Build")
        grid = KeyValueGrid()
        grid.set_rows(
            [
                ("Version", __version__),
                ("Target", "macOS 11+ (Intel / Apple silicon)" if _IS_MAC else "Windows 10/11 x64"),
                ("GUI", "PySide6 / Qt 6"),
                ("Providers", "Ollama (local) · OpenAI-compatible (local or cloud)"),
                (
                    "Browser",
                    "Playwright + Chromium, dedicated profile"
                    if _IS_MAC
                    else "Playwright + Microsoft Edge, dedicated profile",
                ),
                ("Core", "Shared AgentBetta core (same engine as the CLI)"),
                ("License", "MIT"),
                ("Copyright", "© 2026 Dr. Md. Ashraful Babu"),
                ("Trademark", "AgentBetta™ is a trademark of Dr. Md. Ashraful Babu"),
            ]
        )
        details.add(grid)
        layout.addWidget(details)

        safety = Card("Safety posture")
        safety.add(muted(
            "Local-first and deny-by-default. The permission profile governs every action. "
            "Full Computer grants broad access but never bypasses OS security, UAC or "
            "hard-denied rules. API keys are stored in "
            + ("the macOS Keychain" if _IS_MAC else "Windows Credential Manager")
            + ", never in plain settings files or logs."
        ))
        layout.addWidget(safety)
        layout.addStretch(1)
