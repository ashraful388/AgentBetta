"""PySide6 desktop application entry point."""

from __future__ import annotations

import logging
import os
import sys

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

from agentbetta import __version__
from agentbetta.desktop.assets import app_icon
from agentbetta.desktop.main_window import MainWindow
from agentbetta.desktop.services import AppServices
from agentbetta.desktop.theme import apply_theme
from agentbetta.diagnostics import get_logger, setup_logging


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    logger = get_logger("app")
    logger.info("AgentBetta %s starting", __version__)
    app = QApplication.instance() or QApplication(argv or sys.argv)
    app.setApplicationName("AgentBetta")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(app_icon())
    if sys.platform.startswith("win"):
        # Give the taskbar its own AppUserModelID so it uses the AgentBetta icon
        # and does not group under python.exe.
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "dev.agentbetta.desktop"
            )
        except Exception:
            pass
    services = AppServices()
    apply_theme(app, services.settings.general.theme)
    smoke = bool(os.environ.get("AGENTBETTA_SMOKE_EXIT"))
    general = services.settings.general
    if not smoke and not general.first_run_complete and not services.settings.providers and not services.settings.models:
        from agentbetta.desktop.widgets.onboarding import OnboardingDialog

        OnboardingDialog(services).exec()
    window = MainWindow(services)
    window.show()
    if smoke:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(1500, app.quit)
    exit_code = app.exec()
    _shutdown(app)
    # A background QThread (e.g. the startup update check) may still be running;
    # destroying it during Qt teardown crashes the process (0xC0000409). Exit
    # the process directly instead, after giving threads a brief moment.
    logging.shutdown()
    os._exit(int(exit_code))


def _shutdown(app: QApplication, timeout_ms: int = 2000) -> None:
    """Ask background threads to stop and wait briefly for them."""

    threads: list[QThread] = list(app.findChildren(QThread))
    for widget in app.topLevelWidgets():
        threads.extend(widget.findChildren(QThread))
    unique: dict[int, QThread] = {id(t): t for t in threads}
    for thread in unique.values():
        if thread.isRunning():
            thread.requestInterruption()
    for thread in unique.values():
        if thread.isRunning():
            thread.wait(timeout_ms)


if __name__ == "__main__":
    raise SystemExit(main())
