"""Bounded shell tool. Never auto-elevates.

The concrete shell is platform-specific (PowerShell on Windows, the user's
login shell on macOS) and is provided by ``agentbetta.platform.processes``.
"""

from __future__ import annotations

from typing import Any

from agentbetta.permissions import policy
from agentbetta.platform import filesystem as fs
from agentbetta.platform import processes as proc
from agentbetta.tools.guards import requires
from agentbetta.tools.registry import ToolContext


@requires(policy.SHELL_EXEC)
def run_shell(*, ctx: ToolContext, command: str, timeout: int = 60,
              cwd: str | None = None) -> dict[str, Any]:
    workdir = str(fs.canonical_path(cwd)) if cwd else None
    result = proc.run_shell(command, timeout=timeout, cwd=workdir)
    result["command"] = command
    result["cwd"] = workdir
    return result


# Backward-compatible alias used by the Windows tool catalog and tests.
run_powershell = run_shell


__all__ = ["run_powershell", "run_shell"]
