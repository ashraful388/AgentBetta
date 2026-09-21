import json

from agentbetta.providers.base import LLMRequest
from agentbetta.providers.ollama import OllamaProvider
from agentbetta.providers.openai_compatible import OpenAICompatibleProvider


def _request() -> LLMRequest:
    return LLMRequest(
        messages=[{"role": "user", "content": "hi"}],
        tools=[{"type": "function", "function": {"name": "calculator", "parameters": {}}}],
        max_tokens=100,
        timeout=5,
    )


def test_ollama_parses_tool_calls(monkeypatch):
    captured = {}

    def fake_post(url, payload, **kwargs):
        captured["url"] = url
        return {
            "message": {
                "content": "",
                "tool_calls": [
                    {"function": {"name": "calculator", "arguments": json.dumps({"expression": "1+1"})}}
                ],
            },
            "done_reason": "stop",
            "prompt_eval_count": 12,
            "eval_count": 3,
        }

    monkeypatch.setattr("agentbetta.providers.ollama.post_json", fake_post)
    response = OllamaProvider(model="m", base_url="http://x").chat(_request())
    assert captured["url"].endswith("/api/chat")
    assert response.tool_calls[0].tool_name == "calculator"
    assert response.tool_calls[0].arguments == {"expression": "1+1"}
    assert response.usage["eval_count"] == 3


def test_openai_parses_tool_calls_and_finish_reason(monkeypatch):
    def fake_post(url, payload, **kwargs):
        return {
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {"id": "abc", "function": {"name": "read_text_file", "arguments": '{"path": "a"}'}}
                        ],
                    },
                }
            ],
            "usage": {"total_tokens": 10},
        }

    monkeypatch.setattr("agentbetta.providers.openai_compatible.post_json", fake_post)
    response = OpenAICompatibleProvider(model="m", base_url="http://x", api_key="sk-secret").chat(_request())
    assert response.finish_reason == "tool_calls"
    assert response.tool_calls[0].call_id == "abc"
    assert response.usage["total_tokens"] == 10


def test_openai_reasoning_only_response_is_token_limit(monkeypatch):
    def fake_post(url, payload, **kwargs):
        return {
            "choices": [{"finish_reason": "length", "message": {"content": ""}}],
            "usage": {
                "completion_tokens": 6000,
                "completion_tokens_details": {"reasoning_tokens": 5991},
            },
        }

    monkeypatch.setattr("agentbetta.providers.openai_compatible.post_json", fake_post)
    response = OpenAICompatibleProvider("m", "http://x").chat(_request())
    assert response.text == ""
    assert response.raw.get("failure") == "token_limit"
    assert response.finish_reason == "length"


def test_openai_empty_stop_is_not_token_limit(monkeypatch):
    def fake_post(url, payload, **kwargs):
        return {"choices": [{"finish_reason": "stop", "message": {"content": ""}}]}

    monkeypatch.setattr("agentbetta.providers.openai_compatible.post_json", fake_post)
    response = OpenAICompatibleProvider("m", "http://x").chat(_request())
    assert response.raw.get("failure") is None


def test_openai_omits_max_tokens_and_timeout_when_unlimited(monkeypatch):
    captured = {}

    def fake_post(url, payload, **kwargs):
        captured["payload"] = payload
        captured["timeout"] = kwargs.get("timeout")
        return {"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]}

    monkeypatch.setattr("agentbetta.providers.openai_compatible.post_json", fake_post)
    OpenAICompatibleProvider("m", "http://x").chat(
        LLMRequest(messages=[{"role": "user", "content": "hi"}], max_tokens=0, timeout=0)
    )
    assert "max_tokens" not in captured["payload"]
    assert captured["timeout"] == 0


def test_ollama_omits_num_predict_when_unlimited(monkeypatch):
    captured = {}

    def fake_post(url, payload, **kwargs):
        captured["payload"] = payload
        return {"message": {"content": "ok"}, "done_reason": "stop"}

    monkeypatch.setattr("agentbetta.providers.ollama.post_json", fake_post)
    OllamaProvider(model="m", base_url="http://x").chat(
        LLMRequest(messages=[{"role": "user", "content": "hi"}], max_tokens=0, timeout=0)
    )
    assert "num_predict" not in captured["payload"]["options"]


def test_server_closed_connection_has_actionable_message(monkeypatch):
    import http.client

    from agentbetta.providers.http import ProviderHTTPError, post_json

    def boom(req, timeout=None):
        raise http.client.RemoteDisconnected("Remote end closed connection")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    try:
        post_json("http://x/chat", {"a": 1}, timeout=10)
    except ProviderHTTPError as exc:
        assert "closed the connection" in str(exc)
    else:
        raise AssertionError("expected ProviderHTTPError")


def test_openai_list_models(monkeypatch):
    monkeypatch.setattr(
        "agentbetta.providers.openai_compatible.get_json",
        lambda url, headers=None, timeout=30: {"data": [{"id": "m1"}, {"id": "m2"}]},
    )
    assert OpenAICompatibleProvider("m", "http://x").list_models() == ["m1", "m2"]


def test_ollama_list_models(monkeypatch):
    monkeypatch.setattr(
        "agentbetta.providers.ollama.get_json",
        lambda url, timeout=10: {"models": [{"name": "qwen3:1.7b"}]},
    )
    assert OllamaProvider().list_models() == ["qwen3:1.7b"]


def test_openai_connection_error_redacts_key(monkeypatch):
    def boom(url, headers=None, timeout=30):
        raise RuntimeError("HTTP 401 with sk-supersecret in body")

    monkeypatch.setattr("agentbetta.providers.openai_compatible.get_json", boom)
    provider = OpenAICompatibleProvider("m", "http://x", api_key="sk-supersecret")
    ok, message = provider.test_connection()
    assert ok is False
    assert "sk-supersecret" not in message


def test_openai_serializes_tool_call_arguments_as_string(monkeypatch):
    captured = {}

    def fake_post(url, payload, **kwargs):
        captured["payload"] = payload
        return {"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]}

    monkeypatch.setattr("agentbetta.providers.openai_compatible.post_json", fake_post)
    messages = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {"id": "c1", "type": "function",
                 "function": {"name": "calculator", "arguments": {"expression": "1+1"}}}
            ],
        },
        {"role": "tool", "tool_call_id": "c1", "content": "2"},
    ]
    OpenAICompatibleProvider("m", "http://x").chat(
        LLMRequest(messages=messages, tools=[], max_tokens=10, timeout=5)
    )
    sent = captured["payload"]["messages"][1]["tool_calls"][0]["function"]["arguments"]
    assert isinstance(sent, str)
    assert json.loads(sent) == {"expression": "1+1"}
