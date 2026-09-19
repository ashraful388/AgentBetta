import sys

import pytest

from agentbetta.permissions import profile_permission_set
from agentbetta.tools import ToolContext
from agentbetta.tools import processes as proct
from agentbetta.tools import shell as shellt

IS_MAC = sys.platform == "darwin"
ECHO = "echo agentbetta-hello" if IS_MAC else "Write-Output 'agentbetta-hello'"
SLEEP = "sleep 5" if IS_MAC else "Start-Sleep -Seconds 5"


def _ctx(profile: str = "full") -> ToolContext:
    return ToolContext(permissions=profile_permission_set(profile))


def test_shell_runs_and_captures_output():
    result = shellt.run_shell(ctx=_ctx("full"), command=ECHO, timeout=30)
    assert result["exit_code"] == 0
    assert "agentbetta-hello" in str(result["stdout"])


def test_shell_denied_without_shell_permission():
    ctx = ToolContext(permissions=profile_permission_set("standard"))
    with pytest.raises(PermissionError):
        shellt.run_shell(ctx=ctx, command=ECHO)


def test_shell_timeout_is_enforced():
    result = shellt.run_shell(ctx=_ctx("full"), command=SLEEP, timeout=1)
    assert result["timeout"] is True


def test_run_executable_with_structured_args():
    result = proct.run_executable(
        ctx=_ctx("full"), executable=sys.executable, args=["-c", "print(123)"], timeout=30
    )
    assert result["exit_code"] == 0
    assert "123" in str(result["stdout"])


def test_terminate_unknown_process_denied():
    with pytest.raises(PermissionError):
        proct.terminate_process(ctx=_ctx("full"), pid=999999)


def test_list_processes():
    rows = proct.list_processes(ctx=_ctx("full"), max_rows=5)
    assert isinstance(rows, list)


def test_subprocess_calls_hide_console_windows():
    from agentbetta.platform import processes as platform_processes

    helper = getattr(platform_processes, "_hidden_process_kwargs", None)
    if helper is None:
        pytest.skip("platform has no console-hiding helper")
    kwargs = helper()
    if sys.platform == "win32":
        assert kwargs["creationflags"] & 0x08000000  # CREATE_NO_WINDOW
        assert "startupinfo" in kwargs
        assert kwargs["startupinfo"].wShowWindow == 0  # SW_HIDE
