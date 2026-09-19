"""The real model -> tool -> observation -> model execution loop.

This module contains no vendor-specific parsing. Every provider returns a
normalized :class:`ProviderResponse`; this loop validates tool names and
arguments, enforces permissions/approvals and bounds, executes tools, and feeds
structured observations back to the model.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any

from agentbetta.core.cancellation import CancellationToken
from agentbetta.core.events import RunEventBus, RunEventType
from agentbetta.core.messages import build_messages
from agentbetta.core.models import (
    AgentConfiguration,
    ProviderResponse,
    Task,
    ToolCall,
    ToolResult,
)
from agentbetta.core.tool_protocol import parse_tool_protocol
from agentbetta.providers.base import LLMRequest
from agentbetta.tools.registry import ToolContext, ToolRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarize_arguments(arguments: dict[str, Any]) -> str:
    def fmt(value: Any) -> str:
        text = str(value)
        return text if len(text) <= 120 else text[:117] + "..."

    return ", ".join(f"{key}={fmt(value)}" for key, value in sorted(arguments.items()))


def _stringify(output: Any) -> str:
    if isinstance(output, str):
        return output
    try:
        return json.dumps(output, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(output)


def _execute_tool(
    call: ToolCall, tools: ToolRegistry, ctx: ToolContext, bus: RunEventBus
) -> ToolResult:
    started = _now()
    summary = summarize_arguments(call.arguments)
    spec = tools.spec(call.tool_name)
    if spec is None:
        return ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            ok=False,
            error=f"Unknown tool: {call.tool_name}",
            arguments_summary=summary,
            started_at=started,
            ended_at=_now(),
        )
    bus.emit_type(
        RunEventType.TOOL_STARTED,
        tool_name=call.tool_name,
        call_id=call.call_id,
        arguments_summary=summary,
        risk=spec.risk,
    )
    if spec.permission and not ctx.permissions.permits(spec.permission):
        result = ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            ok=False,
            error=f"permission_denied: {spec.permission}",
            permission=spec.permission,
            risk=spec.risk,
            arguments_summary=summary,
            started_at=started,
            ended_at=_now(),
        )
        bus.emit_type(
            RunEventType.TOOL_FINISHED,
            tool_name=call.tool_name,
            call_id=call.call_id,
            ok=False,
            error=result.error,
        )
        return result
    if ctx.approvals is not None:
        try:
            approved = ctx.approvals.request_tool(
                tool_name=call.tool_name,
                arguments=call.arguments,
                permission=spec.permission,
                risk=spec.risk,
                reason=f"Tool {call.tool_name} requests {spec.permission or 'no permission'}.",
            )
        except Exception:
            approved = False
        if not approved:
            result = ToolResult(
                call_id=call.call_id,
                tool_name=call.tool_name,
                ok=False,
                error="approval_denied",
                permission=spec.permission,
                risk=spec.risk,
                arguments_summary=summary,
                started_at=started,
                ended_at=_now(),
            )
            bus.emit_type(
                RunEventType.TOOL_FINISHED,
                tool_name=call.tool_name,
                call_id=call.call_id,
                ok=False,
                error=result.error,
            )
            return result
    elif spec.risk in ("high", "destructive"):
        # Fail safe: a high-risk action with no approval channel configured is denied.
        result = ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            ok=False,
            error="approval_required: no approval service configured for a high-risk action",
            permission=spec.permission,
            risk=spec.risk,
            arguments_summary=summary,
            started_at=started,
            ended_at=_now(),
        )
        bus.emit_type(
            RunEventType.TOOL_FINISHED,
            tool_name=call.tool_name,
            call_id=call.call_id,
            ok=False,
            error=result.error,
        )
        return result
    try:
        output = tools.execute_ctx(call.tool_name, call.arguments, ctx)
        result = ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            ok=True,
            output=_stringify(output),
            permission=spec.permission,
            risk=spec.risk,
            arguments_summary=summary,
            started_at=started,
            ended_at=_now(),
        )
        bus.emit_type(
            RunEventType.TOOL_FINISHED,
            tool_name=call.tool_name,
            call_id=call.call_id,
            ok=True,
        )
        return result
    except Exception as exc:  # tool failure is structured evidence, not a crash
        result = ToolResult(
            call_id=call.call_id,
            tool_name=call.tool_name,
            ok=False,
            error=f"{type(exc).__name__}: {exc}",
            permission=spec.permission,
            risk=spec.risk,
            arguments_summary=summary,
            started_at=started,
            ended_at=_now(),
        )
        bus.emit_type(
            RunEventType.TOOL_FINISHED,
            tool_name=call.tool_name,
            call_id=call.call_id,
            ok=False,
            error=result.error,
        )
        return result


def run_tool_loop(
    *,
    provider: Any,
    task: Task,
    config: AgentConfiguration,
    context: str,
    tools: ToolRegistry,
    event_bus: RunEventBus | None = None,
    cancel_token: CancellationToken | None = None,
    tool_context: ToolContext | None = None,
    deadline: float | None = None,
) -> tuple[ProviderResponse, list[ToolResult]]:
    bus = event_bus or RunEventBus()
    token = cancel_token or CancellationToken()
    ctx = tool_context or ToolContext()
    ctx.permissions = config.permissions
    ctx.cancel_token = token
    if ctx.workspace is None and task.workspace:
        from agentbetta.tools.workspace import Workspace

        try:
            ctx.workspace = Workspace(task.workspace)
        except Exception:
            ctx.workspace = None

    native_tools = bool(getattr(provider, "supports_native_tools", True))
    messages = build_messages(
        task, config, context, tool_names=list(config.tools), native_tools=native_tools
    )
    schemas = tools.schemas(list(config.tools)) if native_tools else []
    model = getattr(provider, "model", "")
    tool_results: list[ToolResult] = []
    max_turns = max(1, config.max_turns)

    def _is_transient(exc: Exception) -> bool:
        flag = getattr(exc, "transient", None)
        if flag is not None:
            return bool(flag)
        text = str(exc).lower()
        return any(
            key in text
            for key in (
                "timed out", "timeout", "temporarily", "connection",
                "http 429", "http 500", "http 502", "http 503", "http 504", "http 522",
            )
        )

    def _call(request: LLMRequest) -> tuple[ProviderResponse | None, ProviderResponse | None]:
        last: Exception | None = None
        for attempt in range(3):
            try:
                return provider.chat(request), None
            except Exception as exc:  # provider failure becomes structured evidence
                last = exc
                if _is_transient(exc) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                break
        message = f"{type(last).__name__}: {last}" if last is not None else "provider error"
        lowered = message.lower()
        if "timed out" in lowered or "timeout" in lowered:
            return None, ProviderResponse("", raw={"failure": "timeout", "message": message})
        return None, ProviderResponse("", raw={"failure": "provider_error", "message": message})

    turn = 0
    while True:
        token.raise_if_cancelled()
        if deadline is not None and time.monotonic() > deadline:
            return ProviderResponse("", raw={"failure": "timeout"}), tool_results
        if turn >= max_turns:
            return ProviderResponse("", raw={"failure": "turn_limit"}), tool_results
        turn += 1
        bus.emit_type(RunEventType.PROVIDER_STARTED, turn=turn, tools=list(config.tools))
        response, failure = _call(
            LLMRequest(
                messages=messages,
                tools=schemas,
                model=model,
                max_tokens=config.token_budget,
                timeout=config.max_seconds,
                metadata={"task": task, "config": config, "context": context},
            )
        )
        if failure is not None:
            return failure, tool_results
        assert response is not None
        if not response.tool_calls:
            fallback_call, final_answer = parse_tool_protocol(response.text, set(config.tools))
            if fallback_call is not None:
                response.tool_calls = [fallback_call]
            elif final_answer is not None:
                response.text = final_answer
                return response, tool_results
            else:
                return response, tool_results
        messages.append(
            {
                "role": "assistant",
                "content": response.text,
                "tool_calls": [
                    {
                        "id": call.call_id,
                        "type": "function",
                        "function": {"name": call.tool_name, "arguments": call.arguments},
                    }
                    for call in response.tool_calls
                ],
            }
        )
        for call in response.tool_calls:
            token.raise_if_cancelled()
            bus.emit_type(
                RunEventType.TOOL_REQUESTED,
                tool_name=call.tool_name,
                call_id=call.call_id,
                arguments_summary=summarize_arguments(call.arguments),
            )
            if len(tool_results) >= config.max_tool_calls:
                return ProviderResponse("", raw={"failure": "tool_limit"}), tool_results
            spec = tools.spec(call.tool_name)
            permission_ok = spec is None or spec.permission is None or ctx.permissions.permits(
                spec.permission
            )
            if spec is not None and permission_ok and call.tool_name not in config.tools:
                # No hidden capability: a model may only use tools exposed by the
                # current AgentConfiguration. A request outside the configuration
                # is rejected as evidence (and drives tool expansion in adaptive
                # mode), never executed. A missing permission is reported first by
                # the permission layer below so adaptive escalation still works.
                result = ToolResult(
                    call_id=call.call_id,
                    tool_name=call.tool_name,
                    ok=False,
                    error=f"Unknown tool: {call.tool_name} (not exposed in the current configuration)",
                    arguments_summary=summarize_arguments(call.arguments),
                    started_at=_now(),
                    ended_at=_now(),
                )
                bus.emit_type(
                    RunEventType.TOOL_FINISHED,
                    tool_name=call.tool_name,
                    call_id=call.call_id,
                    ok=False,
                    error=result.error,
                )
                tool_results.append(result)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.call_id,
                        "content": f"ERROR: {result.error}",
                    }
                )
                continue
            result = _execute_tool(call, tools, ctx, bus)
            tool_results.append(result)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.call_id,
                    "content": result.output if result.ok else f"ERROR: {result.error}",
                }
            )

