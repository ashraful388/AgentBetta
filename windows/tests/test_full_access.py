"""Full Computer access and working-directory validation."""

import subprocess

import pytest

from agentbetta.permissions import ApprovalDecision, ApprovalService, profile_permission_set
from agentbetta.tools import shell as shellt
from agentbetta.tools import processes as proct
from agentbetta.tools.registry import ToolContext


def test_full_computer_auto_approves_high_risk_without_callback():
    calls = {"n": 0}

    def callback(request):
        calls["n"] += 1
        return ApprovalDecision.DENY

    service = ApprovalService(callback=callback, auto_approve_all=True)
    assert service.request_tool(
        tool_name="delete_path", arguments={}, permission="file_delete",
        risk="high", reason="x",
    ) is True
    assert calls["n"] == 0  # no prompt
    assert service.history[-1]["decision"] == "auto_all"


def test_default_service_still_prompts_for_high_risk():
    calls = {"n": 0}

    def callback(request):
        calls["n"] += 1
        return ApprovalDecision.ALLOW_ONCE

    service = ApprovalService(callback=callback)
    assert service.request_tool(
        tool_name="delete_path", arguments={}, permission="file_delete",
        risk="high", reason="x",
    ) is True
    assert calls["n"] == 1


def test_resolve_cwd_rejects_file_and_missing(tmp_path):
    file_path = tmp_path / "a.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        shellt.resolve_cwd(str(file_path))
    with pytest.raises(ValueError):
        shellt.resolve_cwd(str(tmp_path / "does-not-exist"))
    assert shellt.resolve_cwd(None) is None
    assert shellt.resolve_cwd(str(tmp_path)) == str(tmp_path.resolve())


def test_run_executable_rejects_bad_cwd(tmp_path):
    file_path = tmp_path / "b.txt"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        proct.run_executable(
            ctx=ToolContext(permissions=profile_permission_set("full")),
            executable="cmd.exe", args=["/c", "echo", "hi"], cwd=str(file_path),
        )


def test_subprocess_spawns_hide_the_console():
    seen: list[dict] = []
    original = subprocess.run

    def spy(*args, **kwargs):
        seen.append(kwargs)
        return original(*args, **kwargs)

    subprocess.run = spy
    try:
        shellt.run_shell(
            ctx=ToolContext(permissions=profile_permission_set("full")),
            command="echo agentbetta-console-check",
        )
    finally:
        subprocess.run = original
    assert seen, "subprocess.run was not called"
    assert seen[-1].get("creationflags", 0) & 0x08000000  # CREATE_NO_WINDOW
    assert seen[-1].get("startupinfo") is not None
