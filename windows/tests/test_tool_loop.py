import json
from pathlib import Path

from agentbetta import AgentBetta, RuntimeConfig
from agentbetta.core.cancellation import CancellationToken
from agentbetta.core.models import ProviderResponse, ToolCall
from agentbetta.providers.base import BaseProvider
from agentbetta.providers.fake import FakeProvider


def _agent(tmp_path, **kwargs):
    return AgentBetta(
        FakeProvider(),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"), **kwargs),
    )


class _StubProvider(BaseProvider):
    name = "stub"
    is_cloud = False
    model = "stub"

    def __init__(self, tool_name: str, arguments: dict | None = None):
        self.tool_name = tool_name
        self.arguments = arguments or {}

    def chat(self, request):
        return ProviderResponse(
            "",
            finish_reason="tool_calls",
            tool_calls=[ToolCall("call_x", self.tool_name, self.arguments)],
        )


def test_calculator_tool_loop(tmp_path):
    result = _agent(tmp_path).run("Calculate 17 * 23")
    assert result.success and result.verified
    assert "391" in result.output
    assert len(result.tool_results) == 1
    assert result.tool_results[0].tool_name == "calculator"
    assert result.tool_results[0].ok


def test_explicit_tool_call_with_json_args(tmp_path):
    result = _agent(tmp_path).run('[call-tool:calculator]{"expression": "10 / 4"}')
    assert result.verified
    assert "2.5" in result.output


def test_run_record_contains_tool_calls_and_initial_config(tmp_path):
    result = _agent(tmp_path).run("Calculate 17 * 23")
    record = json.loads(Path(result.record_path).read_text(encoding="utf-8"))
    assert record["initial_configuration"] is not None
    assert record["tool_calls"][0]["tool_name"] == "calculator"
    assert record["tool_calls"][0]["ok"] is True


def test_unknown_tool_becomes_structured_error(tmp_path):
    result = AgentBetta(
        _StubProvider("does_not_exist"),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs")),
    ).run("do a thing")
    assert any("Unknown tool" in (r.error or "") for r in result.tool_results)
    assert not result.verified


def test_tool_permission_denied_is_recorded(tmp_path):
    result = AgentBetta(
        _StubProvider("write_text_file", {"path": "x.txt", "content": "y"}),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs")),
    ).run("Write a file")
    assert result.tool_results[0].ok is False
    assert "permission_denied" in (result.tool_results[0].error or "")


def test_tool_call_bound_is_enforced_per_attempt(tmp_path):
    result = AgentBetta(
        _StubProvider("calculator", {"expression": "1+1"}),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"), max_adaptations=0),
    ).run("Calculate 1 + 1")
    assert result.attempts == 1
    assert len(result.tool_results) <= 3


def test_system_prompt_states_granted_capabilities():
    from agentbetta.core.messages import build_messages
    from agentbetta.core.models import AgentConfiguration, PermissionSet, Task

    config = AgentConfiguration(
        permissions=PermissionSet(
            allowed=frozenset({"file_read"}), eligible=frozenset({"file_read"})
        ),
        tools=("read_text_file_global",),
    )
    messages = build_messages(Task("hi"), config, "", tool_names=list(config.tools))
    system = str(messages[0]["content"])
    assert "GRANTED CAPABILITIES" in system
    assert "file_read" in system
    assert "read_text_file_global" in system


def test_pre_cancelled_run_returns_cancelled_result(tmp_path):
    token = CancellationToken()
    token.cancel()
    agent = AgentBetta(
        FakeProvider(),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs")),
        cancel_token=token,
    )
    result = agent.run("Explain AgentBetta")
    assert result.success is False
    assert result.verification.evidence.get("cancelled") is True
