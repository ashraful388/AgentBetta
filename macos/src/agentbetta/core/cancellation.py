"""Cooperative cancellation token shared by the runtime, tools and GUI."""

from __future__ import annotations

import threading


class CancelledError(Exception):
    """Raised when a run is cancelled at a cooperative checkpoint."""


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise CancelledError("Run cancelled")

    def wait(self, timeout: float | None = None) -> bool:
        return self._event.wait(timeout=timeout)
