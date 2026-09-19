"""Hot-path memory tools: the model can explicitly save and recall memories.

Requires the global long-term memory manager to be enabled; otherwise the tools
raise a clear, auditable error.
"""

from __future__ import annotations

from typing import Any

from agentbetta.permissions import policy
from agentbetta.tools.guards import requires
from agentbetta.tools.registry import ToolContext


def _manager(ctx: ToolContext) -> Any:
    if ctx.memory is None:
        raise PermissionError("Long-term memory is not enabled in Settings")
    return ctx.memory


@requires(policy.MEMORY_WRITE)
def remember(*, ctx: ToolContext, text: str, kind: str = "fact",
             tags: list[str] | None = None, importance: float = 0.5) -> dict[str, Any]:
    manager = _manager(ctx)
    entry = manager.add(
        text, kind=kind, tags=list(tags or []), importance=float(importance), source="tool"
    )
    return {"id": entry.id, "kind": entry.kind, "text": entry.text}


@requires(policy.MEMORY_READ)
def recall(*, ctx: ToolContext, query: str, k: int = 5) -> list[dict[str, Any]]:
    manager = _manager(ctx)
    results = manager.search(query, k=int(k))
    return [
        {"kind": entry.kind, "text": entry.text, "created_at": entry.created_at}
        for entry in results
    ]


__all__ = ["recall", "remember"]
