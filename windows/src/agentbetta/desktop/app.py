"""PySide6 desktop application entry point."""

from __future__ import annotations

import os
import sys

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
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
