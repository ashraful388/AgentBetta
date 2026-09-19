"""Run event stream shared by the core and the desktop client.

The core emits events; the GUI subscribes. The core must never import GUI
modules, so this module defines only plain data and a tiny synchronous bus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class RunEventType(str, Enum):
    RUN_STARTED = "run_started"
    ATTEMPT_STARTED = "attempt_started"
    PROVIDER_STARTED = "provider_started"
    PROVIDER_OUTPUT_DELTA = "provider_output_delta"
    TOOL_REQUESTED = "tool_requested"
    APPROVAL_REQUIRED = "approval_required"
    TOOL_STARTED = "tool_started"
    TOOL_FINISHED = "tool_finished"
    VERIFICATION_UPDATED = "verification_updated"
    ADAPTATION_RECORDED = "adaptation_recorded"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    RUN_CANCELLED = "run_cancelled"


@dataclass
class RunEvent:
    type: str
    run_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


Listener = Callable[[RunEvent], None]


class RunEventBus:
    """A minimal synchronous pub/sub bus.

    Subscriber exceptions are swallowed so a faulty GUI listener can never break
    a core run.
    """

    def __init__(self) -> None:
        self._listeners: list[Listener] = []

    def subscribe(self, listener: Listener) -> Listener:
        self._listeners.append(listener)
        return listener

    def unsubscribe(self, listener: Listener) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def emit(self, event: RunEvent) -> None:
        for listener in list(self._listeners):
            try:
                listener(event)
            except Exception:
                pass

    def emit_type(self, event_type: str | RunEventType, *, run_id: str = "",
                  **data: Any) -> None:
        value = event_type.value if isinstance(event_type, RunEventType) else event_type
        self.emit(RunEvent(type=value, run_id=run_id, data=data))
