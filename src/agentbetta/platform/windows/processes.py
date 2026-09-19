"""Process and shell primitives for Windows.

AgentBetta never auto-elevates. Commands run as the current user with bounded
timeouts and capped output. Only processes started by AgentBetta may be
terminated without a separate explicit approval.
"""

from __future__ import annotations

import csv
import io
import os
import subprocess
import time
from pathlib import Path

DEFAULT_OUTPUT_CAP = 20_000
_STARTED_PIDS: set[int] = set()


class ProcessError(RuntimeError):
    pass


def _hidden_process_kwargs() -> dict:
    """Return subprocess kwargs that suppress console windows on Windows.

    A packaged GUI application (console=False) must never flash a console
    window for the child processes it spawns (shell, tasklist, explorer,
    executables). Without ``CREATE_NO_WINDOW`` and a hidden startupinfo,
    Windows briefly shows a ``cmd``/``conhost`` window for every spawn.
    """

    if os.name != "nt":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
        "startupinfo": startupinfo,
    }


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
            **_hidden_process_kwargs(),
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


def run_powershell(command: str, *, timeout: int = 60, cwd: str | None = None,
                   cap: int = DEFAULT_OUTPUT_CAP) -> dict[str, object]:
    args = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command,
    ]
    return run_command(args, timeout=timeout, cwd=cwd, cap=cap)


def run_shell(command: str, *, timeout: int = 60, cwd: str | None = None,
              cap: int = DEFAULT_OUTPUT_CAP) -> dict[str, object]:
    """Platform shell entry point (PowerShell on Windows)."""

    return run_powershell(command, timeout=timeout, cwd=cwd, cap=cap)


def shell_tool_name() -> str:
    return "run_powershell"


def preferred_browser_engine() -> str:
    return "msedge"


def start_process(args: list[str], *, cwd: str | None = None) -> int:
    proc = subprocess.Popen(args, cwd=cwd, shell=False, **_hidden_process_kwargs())
    _STARTED_PIDS.add(proc.pid)
    return proc.pid


def list_processes(*, max_rows: int = 200) -> list[dict[str, object]]:
    try:
        result = run_command(["tasklist", "/FO", "CSV", "/NH"], timeout=20)
    except ProcessError:
        return []
    rows: list[dict[str, object]] = []
    reader = csv.reader(io.StringIO(str(result.get("stdout") or "")))
    for row in reader:
        if len(row) >= 5:
            rows.append({"name": row[0], "pid": row[1], "session": row[2], "mem": row[4]})
        if len(rows) >= max_rows:
            break
    return rows


def is_started_by_agentbetta(pid: int) -> bool:
    return pid in _STARTED_PIDS


def terminate_process(pid: int) -> bool:
    if pid not in _STARTED_PIDS:
        raise PermissionError("Only processes started by AgentBetta may be terminated automatically")
    try:
        result = run_command(["taskkill", "/PID", str(pid), "/T", "/F"], timeout=15)
    except ProcessError:
        return False
    _STARTED_PIDS.discard(pid)
    return result.get("exit_code") == 0


def open_with_default(path: str) -> None:
    startfile = getattr(os, "startfile", None)
    if startfile is None:
        raise ProcessError("Opening paths is only supported on Windows")
    startfile(path)


def reveal_in_explorer(path: str) -> None:
    target = Path(path)
    if target.is_dir():
        subprocess.Popen(["explorer", str(target)], **_hidden_process_kwargs())
    else:
        subprocess.Popen(["explorer", "/select,", str(target)], **_hidden_process_kwargs())


def open_url(url: str) -> None:
    startfile = getattr(os, "startfile", None)
    if startfile is None:
        raise ProcessError("Opening URLs is only supported on Windows")
    startfile(url)


def platform_shell() -> str:
    return os.environ.get("COMSPEC", "cmd.exe")
