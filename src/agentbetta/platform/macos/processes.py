"""Process and shell primitives for macOS.

AgentBetta never auto-elevates. Commands run as the current user with bounded
timeouts and capped output. Only processes started by AgentBetta may be
terminated without a separate explicit approval.
"""

from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

DEFAULT_OUTPUT_CAP = 20_000
_STARTED_PIDS: set[int] = set()


class ProcessError(RuntimeError):
    pass


def _cap(value: object, cap: int = DEFAULT_OUTPUT_CAP) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    text = str(value)
    return text if len(text) <= cap else text[:cap] + f"\n...[truncated {len(text) - cap} chars]"


def run_command(args: list[str], *, timeout: int = 60, cwd: str | None = None,
                cap: int = DEFAULT_OUTPUT_CAP) -> dict[str, object]:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            shell=False,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": None,
            "timeout": True,
            "stdout": _cap(exc.stdout, cap),
            "stderr": _cap(exc.stderr, cap),
            "duration": round(time.monotonic() - started, 3),
        }
    except FileNotFoundError as exc:
        raise ProcessError(f"Executable not found: {exc}") from exc
    return {
        "exit_code": proc.returncode,
        "timeout": False,
        "stdout": _cap(proc.stdout, cap),
        "stderr": _cap(proc.stderr, cap),
        "duration": round(time.monotonic() - started, 3),
    }


def _login_shell() -> str:
    shell = os.environ.get("SHELL")
    if shell and Path(shell).exists():
        return shell
    return "/bin/zsh" if Path("/bin/zsh").exists() else "/bin/bash"


def run_shell(command: str, *, timeout: int = 60, cwd: str | None = None,
              cap: int = DEFAULT_OUTPUT_CAP) -> dict[str, object]:
    args = [_login_shell(), "-lc", command]
    return run_command(args, timeout=timeout, cwd=cwd, cap=cap)


# Backward-compatible alias; on macOS the shell tool is exposed as run_shell.
run_powershell = run_shell


def shell_tool_name() -> str:
    return "run_shell"


def preferred_browser_engine() -> str:
    return "chromium"


def start_process(args: list[str], *, cwd: str | None = None) -> int:
    proc = subprocess.Popen(args, cwd=cwd, shell=False)
    _STARTED_PIDS.add(proc.pid)
    return proc.pid


def list_processes(*, max_rows: int = 200) -> list[dict[str, object]]:
    try:
        result = run_command(["ps", "-axo", "pid=,comm="], timeout=20)
    except ProcessError:
        return []
    rows: list[dict[str, object]] = []
    for line in str(result.get("stdout") or "").splitlines():
        line = line.strip()
        if not line:
            continue
        pid, _, name = line.partition(" ")
        rows.append({"name": name.strip(), "pid": pid, "session": "", "mem": ""})
        if len(rows) >= max_rows:
            break
    return rows


def is_started_by_agentbetta(pid: int) -> bool:
    return pid in _STARTED_PIDS


def terminate_process(pid: int) -> bool:
    if pid not in _STARTED_PIDS:
        raise PermissionError("Only processes started by AgentBetta may be terminated automatically")
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return False
    _STARTED_PIDS.discard(pid)
    return True


def open_with_default(path: str) -> None:
    subprocess.Popen(["open", str(path)])


def reveal_in_explorer(path: str) -> None:
    subprocess.Popen(["open", "-R", str(path)])


def open_url(url: str) -> None:
    subprocess.Popen(["open", url])


def platform_shell() -> str:
    return _login_shell()
