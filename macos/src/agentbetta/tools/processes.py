"""Process and open-path tools.

Termination is restricted to processes AgentBetta started; any other target
requires an explicit user approval.
"""

from __future__ import annotations

from typing import Any

from agentbetta.permissions import policy
from agentbetta.platform import filesystem as fs
from agentbetta.platform import processes as proc
from agentbetta.tools.guards import requires
from agentbetta.tools.registry import ToolContext


@requires(policy.PROCESS_LAUNCH)
def run_executable(*, ctx: ToolContext, executable: str, args: list[str] | None = None,
                   timeout: int = 60, cwd: str | None = None) -> dict[str, Any]:
    arguments = [executable, *(args or [])]
    workdir = str(fs.canonical_path(cwd)) if cwd else None
    result = proc.run_command(arguments, timeout=timeout, cwd=workdir)
    result["executable"] = executable
    result["args"] = list(args or [])
    result["cwd"] = workdir
    return result


@requires(policy.PROCESS_LAUNCH)
def list_processes(*, ctx: ToolContext, max_rows: int = 200) -> list[dict[str, object]]:
    return proc.list_processes(max_rows=max_rows)


@requires(policy.PROCESS_LAUNCH)
def terminate_process(*, ctx: ToolContext, pid: int) -> dict[str, Any]:
    return {"pid": pid, "terminated": proc.terminate_process(pid)}


@requires(policy.PROCESS_LAUNCH)
def open_path(*, ctx: ToolContext, path: str) -> dict[str, Any]:
    target = fs.canonical_path(path)
    proc.open_with_default(str(target))
    return {"path": str(target), "opened": True}


@requires(policy.PROCESS_LAUNCH)
def reveal_path(*, ctx: ToolContext, path: str) -> dict[str, Any]:
    target = fs.canonical_path(path)
    proc.reveal_in_explorer(str(target))
    return {"path": str(target), "revealed": True}


@requires(policy.PROCESS_LAUNCH)
def open_url(*, ctx: ToolContext, url: str) -> dict[str, Any]:
    proc.open_url(url)
    return {"url": url, "opened": True}


__all__ = [
    "list_processes",
    "open_path",
    "open_url",
    "reveal_path",
    "run_executable",
    "terminate_process",
]
