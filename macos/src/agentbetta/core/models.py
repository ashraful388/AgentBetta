from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Any


class VerificationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ERROR = "ERROR"


class AdaptationMode(str, Enum):
    ADAPTIVE = "adaptive"
    FIXED = "fixed"
    WHOLESALE = "wholesale"


@dataclass(frozen=True)
class PermissionSet:
    allowed: frozenset[str] = frozenset({"file_read"})
    eligible: frozenset[str] = frozenset({"file_read"})
    hard_denied: frozenset[str] = frozenset()

    def permits(self, permission: str) -> bool:
        return permission in self.allowed

    def is_eligible(self, permission: str) -> bool:
        return permission in self.eligible and permission not in self.hard_denied

    def with_permission(self, permission: str) -> "PermissionSet":
        if permission in self.hard_denied:
            raise PermissionError(f"Permission is hard-denied: {permission}")
        if permission not in self.eligible:
            raise PermissionError(f"Permission is not eligible for adaptive activation: {permission}")
        return replace(self, allowed=frozenset(set(self.allowed) | {permission}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": sorted(self.allowed),
            "eligible": sorted(self.eligible),
            "hard_denied": sorted(self.hard_denied),
        }


@dataclass(frozen=True)
class AgentConfiguration:
    schema_version: str = "0.1"
    model_tier: int = 0
    context_chars: int = 8_000
    tools: tuple[str, ...] = ()
    permissions: PermissionSet = field(default_factory=PermissionSet)
    memory_items: int = 0
    token_budget: int = 2_000
    max_seconds: int = 180
    max_turns: int = 3
    max_tool_calls: int = 3

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["permissions"] = self.permissions.to_dict()
        return d

    def changed_dimensions(self, other: "AgentConfiguration") -> tuple[str, ...]:
        dims=[]
        for name in ("model_tier", "context_chars", "tools", "permissions", "memory_items",
                     "token_budget", "max_seconds", "max_turns", "max_tool_calls"):
            if getattr(self, name) != getattr(other, name):
                dims.append(name)
        return tuple(dims)


@dataclass(frozen=True)
class TaskFeatures:
    needs_files: bool = False
    needs_write: bool = False
    needs_code: bool = False
    needs_calculation: bool = False
    needs_network: bool = False
    needs_shell: bool = False
    needs_process: bool = False
    needs_delete: bool = False
    needs_memory: bool = False
    reasoning_level: int = 0
    requested_structured_output: bool = False
    estimated_input_chars: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Task:
    objective: str
    inputs: list[str] = field(default_factory=list)
    workspace: str | None = None
    permissions: PermissionSet = field(default_factory=PermissionSet)
    mode: AdaptationMode = AdaptationMode.ADAPTIVE
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    status: VerificationStatus
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == VerificationStatus.PASS


@dataclass
class AdaptationEvent:
    attempt: int
    reason: str
    evidence: dict[str, Any]
    before: AgentConfiguration
    after: AgentConfiguration
    changed_dimensions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "reason": self.reason,
            "evidence": self.evidence,
            "before": self.before.to_dict(),
            "after": self.after.to_dict(),
            "changed_dimensions": list(self.changed_dimensions),
        }


@dataclass
class ToolCall:
    """A normalized request from a model to run a tool."""

    call_id: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"call_id": self.call_id, "tool_name": self.tool_name, "arguments": self.arguments}


@dataclass
class ToolResult:
    """Structured, auditable outcome of one tool execution."""

    call_id: str
    tool_name: str
    ok: bool
    output: str = ""
    error: str | None = None
    permission: str | None = None
    risk: str = "low"
    arguments_summary: str = ""
    started_at: str = ""
    ended_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProviderResponse:
    text: str
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    finish_reason: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class RuntimeConfig:
    research_mode: bool = False
    record_runs: bool = True
    run_dir: str = ".agentbetta/runs"
    privacy_mode: bool = False
    max_adaptations: int = 3
    allow_contraction_proposals: bool = True
    max_total_seconds: int = 600
    memory_items: int | None = None


@dataclass
class Result:
    run_id: str
    output: str
    success: bool
    verified: bool
    verification: VerificationResult
    attempts: int
    final_configuration: AgentConfiguration
    adaptations: list[AdaptationEvent] = field(default_factory=list)
    contraction_candidates: list[AgentConfiguration] = field(default_factory=list)
    record_path: str | None = None
    initial_configuration: AgentConfiguration | None = None
    tool_results: list[ToolResult] = field(default_factory=list)


@dataclass
class RunRecord:
    run_id: str
    started_at: str
    ended_at: str
    task: dict[str, Any]
    task_features: dict[str, Any]
    mode: str
    provider: str
    attempts: list[dict[str, Any]]
    adaptations: list[dict[str, Any]]
    final_configuration: dict[str, Any]
    verification: dict[str, Any]
    success: bool
    contraction_candidates: list[dict[str, Any]]
    wall_seconds: float
    version: str = "0.1.0.dev0"
    initial_configuration: dict[str, Any] | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    model_id: str | None = None
    provider_id: str | None = None
    cancelled: bool = False
    error: str | None = None
    output: str = ""
