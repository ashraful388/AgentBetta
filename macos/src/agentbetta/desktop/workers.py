"""Background run worker.

Runs the AgentBetta core on a QThread so the GUI never blocks. Bridges
high-risk tool approvals back to the GUI thread and streams core run events.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal

from agentbetta.core.controller import TaskController
from agentbetta.core.events import RunEventBus
from agentbetta.core.models import AdaptationMode, Task
from agentbetta.permissions import ApprovalDecision, ApprovalService, profile_permission_set


class CallWorker(QThread):
    """Run a blocking callable off the GUI thread."""

    done = Signal(object)
    failed = Signal(str)

    def __init__(self, function: Any, parent: Any = None) -> None:
        super().__init__(parent)
        self._function = function

    def run(self) -> None:
        try:
            self.done.emit(self._function())
        except Exception as exc:  # pragma: no cover - surfaced to the UI
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class RunWorker(QThread):
    event = Signal(object)
    approvalRequired = Signal(object)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, services: Any, request: Any, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        self.request = request
        self._controller: TaskController | None = None

    def cancel(self) -> None:
        if self._controller is not None:
            self._controller.cancel()

    def _approval_callback(self, approval_request: Any) -> ApprovalDecision:
        holder: dict[str, Any] = {}
        done = threading.Event()
        self.approvalRequired.emit((approval_request, holder, done))
        done.wait(timeout=600)
        return holder.get("decision", ApprovalDecision.DENY)

    def run(self) -> None:
        try:
            approvals = ApprovalService(callback=self._approval_callback)
            bus = RunEventBus()
            bus.subscribe(lambda event: self.event.emit(event))
            selection = self.request.selection
            provider = self.services.build_provider(selection, local_only=self.request.local_only)
            runtime = self.services.build_runtime(
                provider, approvals=approvals, event_bus=bus, privacy=self.request.privacy
            )
            controller = TaskController(runtime, event_bus=bus)
            self._controller = controller
            task = Task(
                self.request.objective,
                inputs=list(getattr(self.request, "inputs", []) or []),
                workspace=self.request.workspace,
                permissions=profile_permission_set(self.request.profile),
                mode=AdaptationMode(self.request.mode),
                metadata={"local_only": self.request.local_only},
            )
            result = controller.run(task, mode=self.request.mode)
            usage: dict[str, Any] = {}
            if result.record_path:
                try:
                    record = json.loads(Path(result.record_path).read_text(encoding="utf-8"))
                    usage = self.services.usage_for_record(record)
                except (OSError, json.JSONDecodeError):
                    usage = {}
            summary = self._summarize(result, provider)
            summary["usage"] = usage
            summary["local_only"] = self.request.local_only
            self.completed.emit(summary)
        except Exception as exc:  # never let a worker crash the GUI
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        finally:
            # Release the browser in this worker thread so the next run can
            # start Playwright cleanly on its own thread.
            try:
                self.services.close_browser()
            except Exception:
                pass

    @staticmethod
    def _summarize(result: Any, provider: Any) -> dict[str, Any]:
        evidence = result.verification.evidence or {}
        cancelled = bool(evidence.get("cancelled"))
        error = None
        if not cancelled and result.verification.status.value == "ERROR":
            error = result.verification.reason
        return {
            "run_id": result.run_id,
            "output": result.output,
            "success": result.success,
            "verified": result.verified,
            "cancelled": cancelled,
            "error": error,
            "attempts": result.attempts,
            "record_path": result.record_path,
            "initial_configuration": result.initial_configuration.to_dict()
            if result.initial_configuration
            else None,
            "final_configuration": result.final_configuration.to_dict(),
            "adaptations": [a.to_dict() for a in result.adaptations],
            "tool_results": [t.to_dict() for t in result.tool_results],
            "contraction_candidates": [c.to_dict() for c in result.contraction_candidates],
            "verification": {
                "status": result.verification.status.value,
                "reason": result.verification.reason,
                "evidence": result.verification.evidence,
            },
            "model_id": getattr(provider, "last_model_id", None) or getattr(provider, "model", None),
            "provider": getattr(provider, "last_provider_name", None) or getattr(provider, "name", None),
        }
