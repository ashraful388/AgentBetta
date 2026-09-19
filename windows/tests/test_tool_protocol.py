from agentbetta.core.models import ProviderResponse
from agentbetta.core.tool_protocol import parse_tool_protocol
from agentbetta.providers.base import BaseProvider


def test_parse_fenced_tool_call():
    text = 'Sure\n```json\n{"action": "tool", "tool": "calculator", "arguments": {"expression": "2+2"}}\n```'
    call, answer = parse_tool_protocol(text, {"calculator"})
    assert call is not None and call.tool_name == "calculator"
    assert call.arguments == {"expression": "2+2"}
    assert answer is None


def test_parse_inline_tool_call():
    call, _ = parse_tool_protocol('{"action":"tool","tool":"calculator","arguments":{"expression":"1+1"}}', {"calculator"})
    assert call is not None


def test_parse_final_answer_envelope():
    call, answer = parse_tool_protocol('{"action": "final", "answer": "the result is 4"}', {"calculator"})
    assert call is None and answer == "the result is 4"


def test_parse_ignores_prose_and_unknown_tools():
    assert parse_tool_protocol("Just some text", {"calculator"}) == (None, None)
    call, answer = parse_tool_protocol('{"tool": "delete_everything", "arguments": {}}', {"calculator"})
    assert call is None and answer is None


class _JsonProtocolProvider(BaseProvider):
    name = "json-protocol"
    is_cloud = False
    model = "json"

    def __init__(self):
        self.calls = 0

    def chat(self, request):
        self.calls += 1
        if any(m.get("role") == "tool" for m in request.messages):
            return ProviderResponse('{"action":"final","answer":"done: 4"}')
        return ProviderResponse('```json\n{"action":"tool","tool":"calculator","arguments":{"expression":"2+2"}}\n```')


def test_loop_executes_json_fallback_tool(tmp_path):
    from agentbetta import AgentBetta, RuntimeConfig

    agent = AgentBetta(
        _JsonProtocolProvider(), runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"))
    )
    result = agent.run("Calculate 2 + 2")
    assert result.verified
    assert "4" in result.output
    assert result.tool_results and result.tool_results[0].tool_name == "calculator"
