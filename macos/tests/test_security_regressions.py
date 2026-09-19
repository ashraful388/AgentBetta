"""Regression tests for issues found during physical GUI testing.

1. A model could execute a tool that was not exposed by the active
   AgentConfiguration ("hidden capability").
2. A denied approval was re-prompted on the next adaptive attempt.
3. Task characterization missed filenames/paths (e.g. ``notes.txt``), so file
   tools were not exposed for obvious file tasks.
"""

from agentbetta import AgentBetta, RuntimeConfig
from agentbetta.core.characterize import characterize
from agentbetta.core.models import (
    ProviderResponse,
    Task,
    ToolCall,
    VerificationResult,
    VerificationStatus,
)
from agentbetta.permissions import ApprovalDecision, ApprovalService, profile_permission_set
from agentbetta.policy.engine import diagnose
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
            return ProviderResponse(f"done: {tool_messages[-1].get('content')}")
        return ProviderResponse(
            "",
            finish_reason="tool_calls",
            tool_calls=[ToolCall("c1", self.tool_name, self.arguments)],
        )


def test_tool_outside_configuration_is_blocked(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("TOPSECRET-VALUE", encoding="utf-8")
    agent = AgentBetta(
        _ToolThenAnswer("read_text_file_global", {"path": str(secret)}),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"), max_adaptations=0),
    )
    # A calculation task does not expose global filesystem tools.
    result = agent.run("Calculate 1 + 1", permissions=profile_permission_set("safe"))
    assert result.tool_results
    assert result.tool_results[0].ok is False
    assert "not exposed" in (result.tool_results[0].error or "")
    assert "TOPSECRET-VALUE" not in result.output
    assert not result.verified


def test_denied_action_is_not_reprompted():
    calls = {"n": 0}

    def callback(request):
        calls["n"] += 1
        return ApprovalDecision.DENY

    service = ApprovalService(callback=callback)
    first = service.request_tool(
        tool_name="delete_path", arguments={}, permission="file_delete", risk="high", reason="x"
    )
    second = service.request_tool(
        tool_name="delete_path", arguments={}, permission="file_delete", risk="high", reason="x"
    )
    assert first is False and second is False
    assert calls["n"] == 1


def test_allow_for_run_is_cached():
    calls = {"n": 0}

    def callback(request):
        calls["n"] += 1
        return ApprovalDecision.ALLOW_RUN

    service = ApprovalService(callback=callback)
    for _ in range(3):
        assert service.request_tool(
            tool_name="run_powershell", arguments={}, permission="shell_exec",
            risk="high", reason="x",
        ) is True
    assert calls["n"] == 1


def test_characterize_detects_filenames_and_paths():
    assert characterize(Task("read notes.txt")).needs_files
    assert characterize(Task(r"open C:\data\report")).needs_files
    assert characterize(Task("summarize ~/Documents/report.md")).needs_files
    assert not characterize(Task("say hello")).needs_files


def test_approval_denial_is_terminal_for_adaptation():
    verification = VerificationResult(
        VerificationStatus.FAIL, "A required action was not approved", {"approval_denied": True}
    )
    assert diagnose(verification) == ()
