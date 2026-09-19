"""Desktop application service boundary around the AgentBetta core.

``TaskController`` owns a run's cancellation token and event stream. The GUI
calls this controller; it never calls the scientific policy engine directly.
"""

from __future__ import annotations

from typing import Any

from agentbetta.core.cancellation import CancellationToken
from agentbetta.core.events import RunEventBus, RunEventType
from agentbetta.core.models import AdaptationMode, PermissionSet, Result, Task


class TaskController:
    def __init__(self, runtime: Any, *, event_bus: RunEventBus | None = None) -> None:
        self.runtime = runtime
        self.events = event_bus or RunEventBus()
        self._token: CancellationToken | None = None

    @property
    def current_token(self) -> CancellationToken | None:
        return self._token

    def cancel(self) -> None:
        if self._token is not None:
            self._token.cancel()

    def run(
        self,
        task: str | Task,
        *,
        workspace: str | None = None,
        permissions: PermissionSet | None = None,
        mode: str | AdaptationMode | None = None,
        cancel_token: CancellationToken | None = None,
    ) -> Result:
        token = cancel_token or CancellationToken()
        self._token = token
        objective = task if isinstance(task, str) else task.objective
        self.events.emit_type(
            RunEventType.RUN_STARTED,
            task=objective,
            mode=str(mode or (task.mode.value if isinstance(task, Task) else "adaptive")),
        )
        try:
            result = self.runtime.run(
                task, workspace=workspace, permissions=permissions, mode=mode,
                cancel_token=token,
            )
        except Exception as exc:
            self.events.emit_type(
                RunEventType.RUN_FAILED, error=f"{type(exc).__name__}: {exc}"
            )
            raise
        if token.cancelled:
            self.events.emit_type(
                RunEventType.RUN_CANCELLED, run_id=result.run_id
            )
        else:
            self.events.emit_type(
                RunEventType.RUN_COMPLETED,
                run_id=result.run_id,
                success=result.success,
                verified=result.verified,
                attempts=result.attempts,
                output=result.output,
                record_path=result.record_path,
            )
        return result
