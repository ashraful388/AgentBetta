from pathlib import Path

from agentbetta import AgentBetta, RuntimeConfig
from agentbetta.core.models import PermissionSet, ProviderResponse, ToolCall
from agentbetta.permissions import (
    ApprovalDecision,
    ApprovalService,
    profile_permission_set,
)
from agentbetta.providers.base import BaseProvider


class _ToolThenAnswer(BaseProvider):
    name = "tool-answer"
    is_cloud = False
    model = "stub"

    def __init__(self, tool_name: str, arguments: dict):
        self.tool_name = tool_name
        self.arguments = arguments

    def chat(self, request):
        tool_messages = [m for m in request.messages if m.get("role") == "tool"]
        if tool_messages:
            observation = str(tool_messages[-1].get("content", ""))
            return ProviderResponse(f"Task complete. Observation: {observation}")
        return ProviderResponse(
            "",
            finish_reason="tool_calls",
            tool_calls=[ToolCall("c1", self.tool_name, self.arguments)],
        )


def _run(tmp_path, provider, permissions, task="perform the operation", **kwargs):
    return AgentBetta(
        provider,
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs")),
        **kwargs,
    ).run(task, permissions=permissions)


def test_read_absolute_path_outside_workspace(tmp_path):
    target = tmp_path / "outside.txt"
    target.write_text("absolute-content", encoding="utf-8")
    perms = PermissionSet(allowed=frozenset({"file_read"}), eligible=frozenset({"file_read"}))
    result = _run(
        tmp_path,
        _ToolThenAnswer("read_text_file_global", {"path": str(target)}),
        perms,
        task="read the file at the given path",
    )
    assert result.verified
    assert "absolute-content" in result.output
    assert result.tool_results[0].ok


def test_permission_escalation_activates_only_eligible_permission(tmp_path):
    target = tmp_path / "to-delete.txt"
    target.write_text("bye", encoding="utf-8")
    perms = profile_permission_set("standard")
    assert "file_delete" not in perms.allowed and perms.is_eligible("file_delete")
    approvals = ApprovalService(callback=lambda req: ApprovalDecision.ALLOW_ONCE)
    result = _run(
        tmp_path,
        _ToolThenAnswer("delete_path", {"path": str(target)}),
        perms,
        approvals=approvals,
    )
    assert result.verified
    assert not target.exists()
    assert result.final_configuration.permissions.permits("file_delete")
    assert any("permissions" in a.changed_dimensions for a in result.adaptations)


def test_hard_denied_permission_cannot_be_bypassed(tmp_path):
    target = tmp_path / "keep.txt"
    target.write_text("keep", encoding="utf-8")
    perms = PermissionSet(
        allowed=frozenset({"file_read"}),
        eligible=frozenset({"file_read", "file_delete"}),
        hard_denied=frozenset({"file_delete"}),
    )
    approvals = ApprovalService(callback=lambda req: ApprovalDecision.ALLOW_ONCE)
    result = _run(
        tmp_path,
        _ToolThenAnswer("delete_path", {"path": str(target)}),
        perms,
        approvals=approvals,
    )
    assert not result.verified
    assert target.exists()
    assert not result.final_configuration.permissions.permits("file_delete")


def test_high_risk_without_approval_is_denied(tmp_path):
    target = tmp_path / "data.txt"
    target.write_text("data", encoding="utf-8")
    perms = profile_permission_set("full")
    result = _run(
        tmp_path,
        _ToolThenAnswer("delete_path", {"path": str(target)}),
        perms,
        task="delete the file at the given path",
    )
    assert target.exists()
    assert result.tool_results[0].ok is False
    assert "approval" in (result.tool_results[0].error or "").lower()
