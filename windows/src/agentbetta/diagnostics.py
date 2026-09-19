"""Logging and diagnostics helpers.

Logs rotate and are bounded. Secrets are never logged.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from agentbetta.platform import paths

LOGGER_NAME = "agentbetta"
LOG_FILENAME = "agentbetta.log"


def setup_logging(logs_dir: str | Path | None = None, level: int = logging.INFO) -> logging.Logger:
    target = Path(logs_dir) if logs_dir else paths.logs_dir()
    target.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        handler = RotatingFileHandler(
            target / LOG_FILENAME, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        logger.addHandler(handler)
    return logger


def get_logger(name: str = "") -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{name}" if name else LOGGER_NAME)


def log_path(logs_dir: str | Path | None = None) -> Path:
    return (Path(logs_dir) if logs_dir else paths.logs_dir()) / LOG_FILENAME
