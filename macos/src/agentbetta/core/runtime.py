from __future__ import annotations
import time
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from agentbetta.core.cancellation import CancelledError, CancellationToken
from agentbetta.core.characterize import characterize
from agentbetta.core.events import RunEventBus, RunEventType
from agentbetta.core.models import (
    AdaptationEvent, AdaptationMode, AgentConfiguration, PermissionSet, ProviderResponse, Result,
    RunRecord, RuntimeConfig, Task, VerificationResult, VerificationStatus,
)
from agentbetta.core.tool_loop import run_tool_loop
from agentbetta.policy.engine import (
    contraction_candidates, diagnose, initial_configuration, selective_expand, wholesale_expand,
)
from agentbetta.records.store import FrontierStore, RunRecorder
from agentbetta.tools.catalog import full_registry
from agentbetta.tools.registry import ToolContext, ToolRegistry
from agentbetta.tools.workspace import Workspace
from agentbetta.validation.basic import BasicValidator

class AgentBetta:
    def __init__(self, provider, *, runtime_config: RuntimeConfig | None=None,
                 tools: ToolRegistry | None=None, validator: Any | None=None,
                 event_bus: RunEventBus | None=None, cancel_token: CancellationToken | None=None,
                 approvals: Any | None=None, tool_context: ToolContext | None=None,
                 memory: Any | None=None):
        self.provider=provider
        self.runtime_config=runtime_config or RuntimeConfig()
        self.tools=tools or full_registry()
        self.validator=validator or BasicValidator()
        self.event_bus=event_bus or RunEventBus()
        self.cancel_token=cancel_token or CancellationToken()
        self.approvals=approvals
        self.tool_context=tool_context
        self.memory=memory

    def run(self, task: str | Task, *, workspace: str | None=None,
            permissions: PermissionSet | None=None, mode: str | AdaptationMode | None=None,
            cancel_token: CancellationToken | None=None) -> Result:
        if cancel_token is not None:
            self.cancel_token=cancel_token
        if isinstance(task, str):
            task=Task(task, workspace=workspace, permissions=permissions or PermissionSet())
        else:
            if workspace is not None: task.workspace=workspace
            if permissions is not None: task.permissions=permissions
        if mode is not None: task.mode=AdaptationMode(mode)
        if not task.objective.strip(): raise ValueError("Task objective must not be empty")
        if self.provider.is_cloud and task.metadata.get("local_only"):
            raise PermissionError("Cloud provider cannot be used for a local-only task")

        run_id=uuid.uuid4().hex[:16]
        started=time.time(); started_at=_now()
        features=characterize(task)
        initial=initial_configuration(features, task.permissions, has_workspace=bool(task.workspace))
        if self.runtime_config.memory_items is not None:
            initial=replace(initial, memory_items=self.runtime_config.memory_items)
        config=initial
        context=self._build_context(task, config)
        attempts=[]; adaptations=[]; final_response=None; verification=None
        all_tool_results=[]; cancelled=False; error=None

        max_attempts=1 if task.mode == AdaptationMode.FIXED else 1 + self.runtime_config.max_adaptations
        run_deadline=time.monotonic()+self.runtime_config.max_total_seconds
        try:
            for attempt in range(1, max_attempts+1):
                self.cancel_token.raise_if_cancelled()
                if time.monotonic() > run_deadline:
                    verification=VerificationResult(VerificationStatus.ERROR, "Run time budget exceeded", {"time_budget":True})
                    break
                self.event_bus.emit_type(
                    RunEventType.ATTEMPT_STARTED, run_id=run_id, attempt=attempt,
                    configuration=config.to_dict(),
                )
                ctx=self.tool_context or ToolContext()
                ctx.permissions=config.permissions
                ctx.cancel_token=self.cancel_token
                if ctx.approvals is None and self.approvals is not None:
                    ctx.approvals=self.approvals
                if ctx.memory is None and self.memory is not None:
                    ctx.memory=self.memory
                deadline=min(time.monotonic()+config.max_seconds, run_deadline)
                response, tool_results=run_tool_loop(
                    provider=self.provider, task=task, config=config, context=context,
                    tools=self.tools, event_bus=self.event_bus, cancel_token=self.cancel_token,
                    tool_context=ctx, deadline=deadline,
                )
                # A cancellation may arrive while a blocking provider call is in
                # flight; the provider cannot be interrupted, so honour the
                # cancelled token before accepting the response as a success.
                if self.cancel_token.cancelled:
                    raise CancelledError()
                all_tool_results.extend(tool_results)
                try:
                    verification=self.validator.verify(response, tool_results=tool_results)
                except TypeError:
                    verification=self.validator.verify(response)
                attempts.append({"attempt":attempt,"configuration":config.to_dict(),
                                 "provider_usage":response.usage,
                                 "tool_calls":[r.to_dict() for r in tool_results],
                                 "verification":{"status":verification.status.value,"reason":verification.reason,
                                                 "evidence":verification.evidence},
                                 "output_chars":len(response.text)})
                self.event_bus.emit_type(
                    RunEventType.VERIFICATION_UPDATED, run_id=run_id, attempt=attempt,
                    status=verification.status.value, reason=verification.reason,
                )
                final_response=response
                if verification.passed: break
                if attempt >= max_attempts: break
                before=config
                if task.mode == AdaptationMode.WHOLESALE:
                    config=wholesale_expand(config, features, has_workspace=bool(task.workspace))
                    reason="wholesale baseline escalation"
                    evidence=verification.evidence
                else:
                    dims=diagnose(verification)
                    config=selective_expand(config, dims, features, verification.evidence, has_workspace=bool(task.workspace))
                    reason=f"selective expansion: {', '.join(dims) if dims else 'none'}"
                    evidence=verification.evidence
                changed=before.changed_dimensions(config)
                if not changed: break
                adaptations.append(AdaptationEvent(attempt, reason, evidence, before, config, changed))
                self.event_bus.emit_type(
                    RunEventType.ADAPTATION_RECORDED, run_id=run_id, attempt=attempt,
                    changed_dimensions=list(changed), reason=reason,
                )
                context=self._build_context(task, config)
        except CancelledError:
            cancelled=True
            verification=VerificationResult(VerificationStatus.ERROR, "Run cancelled", {"cancelled":True})
            self.event_bus.emit_type(RunEventType.RUN_CANCELLED, run_id=run_id)
        except Exception as exc:
            error=f"{type(exc).__name__}: {exc}"
            verification=VerificationResult(VerificationStatus.ERROR, error, {"error":type(exc).__name__})

        if final_response is None: final_response=ProviderResponse("")
        success=bool(verification and verification.passed)
        if success and self.memory is not None and not self.runtime_config.privacy_mode:
            try:
                from agentbetta.memory.extract import capture_from_run
                already = any(r.tool_name == "remember" and r.ok for r in all_tool_results)
                capture_from_run(
                    self.memory, task=task, output=final_response.text, run_id=run_id,
                    features=features, already_remembered=already,
                )
            except Exception:
                pass
        contractions=[]
        if success and self.runtime_config.research_mode and self.runtime_config.allow_contraction_proposals:
            contractions=contraction_candidates(config)
        ended=time.time(); ended_at=_now()
        record=RunRecord(
            run_id=run_id, started_at=started_at, ended_at=ended_at,
            task=self._safe_task(task), task_features=features.to_dict(), mode=task.mode.value,
            provider=self.provider.name, attempts=attempts,
            adaptations=[a.to_dict() for a in adaptations], final_configuration=config.to_dict(),
            verification={"status":verification.status.value,"reason":verification.reason,"evidence":verification.evidence},
            success=success, contraction_candidates=[x.to_dict() for x in contractions],
            wall_seconds=round(ended-started,6), initial_configuration=initial.to_dict(),
            tool_calls=[r.to_dict() for r in all_tool_results],
            model_id=getattr(self.provider,"last_model_id",None) or getattr(self.provider,"model",None) or None,
            provider_id=getattr(self.provider,"name",None), cancelled=cancelled, error=error,
            output="" if self.runtime_config.privacy_mode else final_response.text,
        )
        record_path=None
        if self.runtime_config.record_runs:
            record_path=str(RunRecorder(self.runtime_config.run_dir).save(record))
            FrontierStore(str(Path(self.runtime_config.run_dir).parent/"frontier.jsonl")).append({
                "run_id":run_id,"features":features.to_dict(),"configuration":config.to_dict(),
                "success":success,"verified":verification.passed,"wall_seconds":record.wall_seconds,
            })
        return Result(run_id, final_response.text, success, verification.passed if verification else False,
                      verification or VerificationResult(VerificationStatus.ERROR,"no result",{}),
                      len(attempts), config, adaptations, contractions, record_path,
                      initial, all_tool_results)

    def _build_context(self, task: Task, config: AgentConfiguration) -> str:
        chunks=[]
        paths_block=self._system_paths(config)
        if paths_block:
            chunks.append(paths_block)
        if self.memory is not None and config.memory_items and config.memory_items > 0:
            try:
                memory_block=self.memory.context_block(task.objective, k=config.memory_items)
            except Exception:
                memory_block=""
            if memory_block:
                chunks.append(memory_block)
        if task.workspace:
            ws=Workspace(task.workspace)
            if "list_directory" in config.tools and task.permissions.permits("file_read"):
                try:
                    listing=self.tools.execute("list_directory", {"path":"."}, workspace=ws, permissions=config.permissions)
                    chunks.append("WORKSPACE FILES:\n"+"\n".join(listing))
                except Exception as e:
                    chunks.append(f"WORKSPACE LIST ERROR: {type(e).__name__}: {e}")
        for inp in task.inputs:
            p=Path(inp)
            if task.workspace and not p.is_absolute():
                ws=Workspace(task.workspace)
                try:
                    txt=self.tools.execute("read_text_file", {"path":inp,"max_chars":config.context_chars}, workspace=ws, permissions=config.permissions)
                    chunks.append(f"INPUT {inp}:\n{txt}")
                except Exception as e:
                    chunks.append(f"INPUT ERROR {inp}: {type(e).__name__}: {e}")
            elif p.exists() and p.is_file() and task.permissions.permits("file_read"):
                # Absolute or out-of-workspace input is intentionally not read implicitly.
                chunks.append(f"INPUT {inp}: explicit workspace required to read this path")
        return "\n\n".join(chunks)[:config.context_chars]

    def _system_paths(self, config: AgentConfiguration) -> str:
        filesystem_tools = {
            "list_drives", "list_directory_global", "file_stat", "read_text_file_global",
            "search_files", "grep_files", "file_hash", "create_directory",
            "write_text_file_global", "append_text_file", "copy_path", "move_path",
            "delete_path", "open_path", "reveal_path",
        }
        if not filesystem_tools.intersection(config.tools):
            return ""
        try:
            from agentbetta.platform import paths as platform_paths

            folders = platform_paths.known_folders()
        except Exception:
            return ""
        lines = [
            "SYSTEM PATHS (use these exact paths; never guess the user name):",
        ]
        for label, key in (
            ("User profile", "user_profile"),
            ("Desktop", "desktop"),
            ("Documents", "documents"),
            ("Downloads", "downloads"),
        ):
            if folders.get(key):
                lines.append(f"- {label}: {folders[key]}")
        lines.append("You may also use 'desktop\\filename', 'documents\\filename', "
                     "'downloads\\filename' or '~\\filename' and AgentBetta will resolve them.")
        return "\n".join(lines)

    def _safe_task(self, task: Task) -> dict[str,Any]:
        return {"objective":"<redacted>" if self.runtime_config.privacy_mode else task.objective,
                "inputs":[] if self.runtime_config.privacy_mode else list(task.inputs),
                "workspace":task.workspace,"permissions":task.permissions.to_dict(),"metadata":{}}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
