"""Update-available dialog: review release notes, download and install."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from agentbetta import __version__
from agentbetta.desktop.widgets.ui import Card, badge, muted
from agentbetta.updates import can_self_update


class DownloadWorker(QThread):
    progress = Signal(int, int)
    done = Signal(object, object)
    failed = Signal(str)

    def __init__(self, services: Any, info: Any, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self.info = info

    def run(self) -> None:
        try:
            path, checksums = self.services.download_update(
                self.info, progress=lambda done, total: self.progress.emit(done, total)
            )
            self.done.emit(path, checksums)
        except Exception as exc:  # surfaced to the dialog
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class UpdateDialog(QDialog):
    def __init__(self, services: Any, info: Any, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self.info = info
        self.worker: DownloadWorker | None = None
        self.setWindowTitle("AgentBetta update")
        self.setMinimumWidth(620)
        self.setMinimumHeight(520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel(f"AgentBetta {info.version} is available")
        title.setObjectName("H2")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(badge("pre-release" if info.prerelease else "stable",
                               "warning" if info.prerelease else "info"))
        layout.addLayout(header)

        layout.addWidget(muted(
            f"You are running {__version__}. A newer release is available on GitHub."
            + (f"  Published {info.published_at[:10]}." if info.published_at else "")
        ))

        notes_card = Card("Release notes")
        notes = QTextBrowser()
        notes.setOpenExternalLinks(True)
        if info.notes.strip():
            notes.setMarkdown(info.notes)
        else:
            notes.setPlainText("No release notes were provided.")
        notes_card.add(notes)
        layout.addWidget(notes_card, 1)

        if not can_self_update():
            layout.addWidget(muted(
                "You are running from source, so AgentBetta cannot replace itself. "
                "Use “Open release page” to download the new build."
            ))

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        self.status = muted("")
        layout.addWidget(self.status)

        buttons = QHBoxLayout()
        self.later_button = QPushButton("Later")
        self.later_button.setObjectName("Ghost")
        self.page_button = QPushButton("Open release page")
        self.page_button.setObjectName("Ghost")
        self.update_button = QPushButton("Update now")
        self.update_button.setObjectName("Primary")
        if not can_self_update():
            self.update_button.setEnabled(False)
        self.later_button.clicked.connect(self.reject)
        self.page_button.clicked.connect(self._open_page)
        self.update_button.clicked.connect(self._start_download)
        buttons.addWidget(self.later_button)
        buttons.addStretch(1)
        buttons.addWidget(self.page_button)
        buttons.addWidget(self.update_button)
        layout.addLayout(buttons)

    # -- actions ----------------------------------------------------------
    def _open_page(self) -> None:
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl

        if self.info.page_url:
            QDesktopServices.openUrl(QUrl(self.info.page_url))

    def _start_download(self) -> None:
        self.update_button.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.status.setText("Downloading update…")
        self.worker = DownloadWorker(self.services, self.info, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.done.connect(self._on_downloaded)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, done: int, total: int) -> None:
        if total > 0:
            self.progress.setRange(0, 100)
            self.progress.setValue(int(done * 100 / total))
            self.status.setText(f"Downloading update… {done * 100 // total}%")
        else:
            self.status.setText(f"Downloading update… {done // 1024} KB")

    def _on_downloaded(self, path: Any, checksums: Any) -> None:
        self.status.setText("Download complete. Installing…")
        try:
            message = self.services.install_update(path, checksums)
        except Exception as exc:
            self._on_failed(f"{type(exc).__name__}: {exc}")
            return
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.status.setText(message)
        if can_self_update():
            QApplication.instance().quit()

    def _on_failed(self, message: str) -> None:
        self.progress.setVisible(False)
        self.update_button.setEnabled(True)
        self.status.setText(f"Update failed: {message}")
