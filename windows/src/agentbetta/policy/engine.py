from __future__ import annotations
from dataclasses import replace
from typing import Any, Iterable

from agentbetta.core.models import (
    AgentConfiguration, PermissionSet, TaskFeatures, VerificationResult,
    VerificationStatus,
)
from agentbetta.permissions import policy as perm_policy

MODEL_MAX=2
CONTEXT_LADDER=(8_000, 24_000, 64_000)
TOKEN_LADDER=(2_000, 6_000, 16_000)
TURN_LADDER=(3, 6, 10)
TIME_LADDER=(180, 420, 900)
TOOLCALL_LADDER=(3, 6, 10, 20)
MEMORY_LADDER=(3, 6, 12)
DEFAULT_MEMORY_ITEMS=3

_WORKSPACE_TOOLS=("list_directory","read_text_file","calculator","write_text_file")


_CORE_READ = ("list_directory_global", "read_text_file_global", "file_stat", "search_files")
_CORE_WRITE = ("create_directory", "write_text_file_global")


def _global_tools(permissions: PermissionSet, features: TaskFeatures | None = None) -> list[str]:
    """Tools exposed by allowed permissions.

    With ``features`` the initial set is gated to the task's detected needs and
    trimmed to a core subset (nano-agent minimalism, which also improves small
    local models). Without features the full set for allowed permissions is used
    for expansion.
    """

    if features is None:
        tools: list[str] = []
        for permission in sorted(permissions.allowed):
            tools.extend(perm_policy.TOOLS_FOR_PERMISSION.get(permission, ()))
        return tools

    tools = []

    def add(permission: str, needed: bool) -> None:
        if needed and permissions.permits(permission):
            tools.extend(perm_policy.TOOLS_FOR_PERMISSION.get(permission, ()))

    if features.needs_files and permissions.permits(perm_policy.FILE_READ):
        tools.extend(_CORE_READ)
    if features.needs_write and permissions.permits(perm_policy.FILE_WRITE):
        tools.extend(_CORE_WRITE)
    add(perm_policy.FILE_DELETE, features.needs_delete)
    add(perm_policy.NETWORK_HTTP, features.needs_network)
    add(perm_policy.BROWSER_READ, features.needs_network)
    add(perm_policy.SHELL_EXEC, features.needs_shell)
    add(perm_policy.PROCESS_LAUNCH, features.needs_process)
    return tools


def _dedupe(items: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))


def initial_configuration(features: TaskFeatures, permissions: PermissionSet,
                          *, has_workspace: bool = False) -> AgentConfiguration:
    tools: list[str] = []
    if has_workspace:
        if features.needs_files:
            tools.extend(["list_directory", "read_text_file"])
        if features.needs_calculation:
            tools.append("calculator")
        if features.needs_write and permissions.permits("file_write"):
            tools.append("write_text_file")
    elif features.needs_calculation:
        tools.append("calculator")
    tools.extend(_global_tools(permissions, features))
    if features.needs_memory:
        if permissions.permits(perm_policy.MEMORY_READ):
            tools.append("recall")
        if permissions.permits(perm_policy.MEMORY_WRITE):
            tools.append("remember")
    model_tier = 1 if features.reasoning_level >= 1 else 0
    context = 24_000 if features.estimated_input_chars > 8_000 else 8_000
    tokens = 6_000 if features.reasoning_level >= 2 else 2_000
    return AgentConfiguration(
        model_tier=model_tier,
        context_chars=context,
        tools=_dedupe(tools),
        permissions=permissions,
        memory_items=DEFAULT_MEMORY_ITEMS,
        token_budget=tokens,
    )


def diagnose(verification: VerificationResult) -> tuple[str, ...]:
    evidence=verification.evidence
    if evidence.get("approval_denied"):
        # A user denial is a terminal decision, not a capability deficiency:
        # do not retry the same action.
        return ()
    if evidence.get("permission_denied"):
        return ("permissions",)
    if evidence.get("missing_tool"):
        return ("tools",)
    if evidence.get("context_truncated"):
        return ("context_chars",)
    if evidence.get("token_limit"):
        return ("token_budget",)
    if evidence.get("timeout"):
        return ("max_seconds",)
    if evidence.get("turn_limit"):
        return ("max_turns",)
    if evidence.get("tool_limit"):
        return ("max_tool_calls",)
    if evidence.get("memory_insufficient"):
        return ("memory_items",)
    if evidence.get("model_insufficient"):
        return ("model_tier",)
    if evidence.get("provider_error"):
        return ()
    if verification.status == VerificationStatus.INSUFFICIENT_EVIDENCE:
        return ("context_chars",)
    if verification.status == VerificationStatus.FAIL:
        return ("model_tier",)
    return ()


def _next(value: int, ladder: tuple[int, ...]) -> int:
    for item in ladder:
        if item > value:
            return item
    return value


def _add_tools(config: AgentConfiguration, names: Iterable[str]) -> AgentConfiguration:
    return replace(config, tools=_dedupe((*config.tools, *names)))


def selective_expand(config: AgentConfiguration, dimensions: Iterable[str], features: TaskFeatures,
                     evidence: dict[str, Any] | None = None, *, has_workspace: bool = False) -> AgentConfiguration:
    evidence = evidence or {}
    out=config
    for dim in dimensions:
        if dim == "model_tier":
            out=replace(out, model_tier=min(MODEL_MAX, out.model_tier+1))
        elif dim == "context_chars":
            out=replace(out, context_chars=_next(out.context_chars, CONTEXT_LADDER))
        elif dim == "token_budget":
            out=replace(out, token_budget=_next(out.token_budget, TOKEN_LADDER))
        elif dim == "max_seconds":
            out=replace(out, max_seconds=_next(out.max_seconds, TIME_LADDER))
        elif dim == "max_turns":
            out=replace(out, max_turns=_next(out.max_turns, TURN_LADDER))
        elif dim == "max_tool_calls":
            out=replace(out, max_tool_calls=_next(out.max_tool_calls, TOOLCALL_LADDER))
        elif dim == "memory_items":
            out=replace(out, memory_items=_next(out.memory_items, MEMORY_LADDER))
        elif dim == "tools":
            needed=list(out.tools)
            if has_workspace and features.needs_files:
                needed.extend(["list_directory", "read_text_file"])
            if features.needs_calculation:
                needed.append("calculator")
            if has_workspace and features.needs_write and out.permissions.permits("file_write"):
                needed.append("write_text_file")
            needed.extend(_global_tools(out.permissions))
            out=_add_tools(out, needed)
        elif dim == "permissions":
            needed_permission = (
                evidence.get("permission_denied_name")
                or ("file_write" if features.needs_write else None)
            )
            if needed_permission and out.permissions.is_eligible(needed_permission):
                try:
                    out=replace(out, permissions=out.permissions.with_permission(needed_permission))
                except PermissionError:
                    pass
                else:
                    out=_add_tools(out, perm_policy.TOOLS_FOR_PERMISSION.get(needed_permission, ()))
    return out


def wholesale_expand(config: AgentConfiguration, features: TaskFeatures,
                     *, has_workspace: bool = False) -> AgentConfiguration:
    # Baseline: grow all non-authority resource dimensions together. Permissions still obey eligibility/hard-deny.
    perms=config.permissions
    tools=set(_WORKSPACE_TOOLS) if has_workspace else {"calculator"}
    for permission in sorted(perms.eligible):
        if permission in perms.hard_denied:
            continue
        try:
            perms=perms.with_permission(permission)
        except PermissionError:
            continue
    tools.update(_global_tools(perms))
    return replace(config, model_tier=MODEL_MAX, context_chars=CONTEXT_LADDER[-1],
                   token_budget=TOKEN_LADDER[-1], max_seconds=TIME_LADDER[-1],
                   max_turns=TURN_LADDER[-1], max_tool_calls=10,
                   memory_items=max(config.memory_items, 8), tools=tuple(sorted(tools)), permissions=perms)


def contraction_candidates(config: AgentConfiguration) -> list[AgentConfiguration]:
    candidates=[]
    if config.model_tier > 0:
        candidates.append(replace(config, model_tier=config.model_tier-1))
    lower_context=[x for x in CONTEXT_LADDER if x < config.context_chars]
    if lower_context:
        candidates.append(replace(config, context_chars=max(lower_context)))
    lower_tokens=[x for x in TOKEN_LADDER if x < config.token_budget]
    if lower_tokens:
        candidates.append(replace(config, token_budget=max(lower_tokens)))
    if config.tools:
        candidates.append(replace(config, tools=config.tools[:-1]))
    if config.memory_items > 0:
        candidates.append(replace(config, memory_items=max(0, config.memory_items-1)))
    # Never auto-contract permissions here; authority probes need explicit benchmark protocol.
    return candidates
