from __future__ import annotations

import json

from agentbetta.core.models import ProviderResponse, ToolCall
from agentbetta.providers.base import BaseProvider, LLMRequest
from agentbetta.providers.http import get_json, post_json


def _parse_tool_calls(raw_calls: list[dict] | None) -> list[ToolCall]:
    calls: list[ToolCall] = []
    for index, call in enumerate(raw_calls or []):
        function = call.get("function") or {}
        arguments = function.get("arguments")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except (json.JSONDecodeError, TypeError):
                arguments = {}
        calls.append(
            ToolCall(
                call_id=str(call.get("id") or f"call_{index}"),
                tool_name=str(function.get("name") or ""),
                arguments=arguments if isinstance(arguments, dict) else {},
            )
        )
    return calls


class OllamaProvider(BaseProvider):
    name = "ollama"
    is_cloud = False

    def __init__(self, model: str = "qwen3:1.7b", base_url: str = "http://127.0.0.1:11434",
                 timeout: int = 120, *, disable_thinking: bool = True) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.disable_thinking = disable_thinking

    def chat(self, request: LLMRequest) -> ProviderResponse:
        options: dict = {}
        if request.max_tokens and request.max_tokens > 0:
            options["num_predict"] = request.max_tokens
        payload: dict = {
            "model": request.model or self.model,
            "messages": request.messages,
            "stream": False,
            "options": options,
        }
        if self.disable_thinking:
            # qwen3-class models support disabling chain-of-thought generation.
            payload["think"] = False
        if request.tools:
            payload["tools"] = request.tools
        data = post_json(
            f"{self.base_url}/api/chat",
            payload,
            timeout=request.timeout if request.timeout is not None else self.timeout,
        )
        message = data.get("message") or {}
        text = str(message.get("content") or "")
        tool_calls = _parse_tool_calls(message.get("tool_calls"))
        return ProviderResponse(
            text,
            usage={
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
                "total_duration": data.get("total_duration"),
            },
            raw=data,
            finish_reason=data.get("done_reason"),
            tool_calls=tool_calls,
        )

    def list_models(self) -> list[str]:
        data = get_json(f"{self.base_url}/api/tags", timeout=10)
        return [str(m.get("name")) for m in (data.get("models") or []) if m.get("name")]

    def test_connection(self) -> tuple[bool, str]:
        try:
            models = self.list_models()
        except Exception as exc:
            return (False, f"Ollama not reachable at {self.base_url}: {type(exc).__name__}: {exc}")
        return (True, f"Ollama reachable. {len(models)} model(s) installed.")
