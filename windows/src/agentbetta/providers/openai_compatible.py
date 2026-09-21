from __future__ import annotations

import json
import os

from agentbetta.core.models import ProviderResponse, ToolCall
from agentbetta.providers.base import BaseProvider, LLMRequest
from agentbetta.providers.http import get_json, post_json
from agentbetta.settings.secrets import redact


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


def _budget_exhausted(finish_reason: str | None, usage: dict) -> bool:
    """True when the model consumed its token budget without an answer.

    Reasoning models behind OpenAI-compatible gateways often spend every
    completion token on hidden reasoning and return an empty ``content``. The
    gateway then reports ``finish_reason == "length"`` (and a reasoning-token
    count). This is a token-budget problem, not a provider failure, so the
    runtime should be able to raise the budget instead of reporting "no output".
    """

    if finish_reason == "length":
        return True
    details = usage.get("completion_tokens_details") or {}
    reasoning = details.get("reasoning_tokens")
    completion = usage.get("completion_tokens")
    return bool(reasoning and completion and reasoning >= completion)


class OpenAICompatibleProvider(BaseProvider):
    name = "openai-compatible"
    is_cloud = True

    def __init__(self, model: str, base_url: str, api_key: str | None = None,
                 timeout: int = 120, tls_verify: bool = True) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("AGENTBETTA_API_KEY")
        self.timeout = timeout
        self.tls_verify = tls_verify

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @staticmethod
    def _prepare_messages(messages: list[dict]) -> list[dict]:
        """OpenAI requires tool_call function arguments as a JSON string."""

        prepared: list[dict] = []
        for message in messages:
            current = dict(message)
            if current.get("tool_calls"):
                tool_calls = []
                for call in current["tool_calls"]:
                    call = dict(call)
                    function = dict(call.get("function") or {})
                    arguments = function.get("arguments")
                    if not isinstance(arguments, str):
                        function["arguments"] = json.dumps(arguments or {})
                    call["function"] = function
                    tool_calls.append(call)
                current["tool_calls"] = tool_calls
            if current.get("role") == "assistant" and current.get("content") is None:
                current["content"] = ""
            prepared.append(current)
        return prepared

    def _sanitize(self, message: str) -> str:
        return redact(message, [self.api_key] if self.api_key else [])

    def chat(self, request: LLMRequest) -> ProviderResponse:
        payload: dict = {
            "model": request.model or self.model,
            "messages": self._prepare_messages(request.messages),
        }
        if request.max_tokens and request.max_tokens > 0:
            payload["max_tokens"] = request.max_tokens
        if request.tools:
            payload["tools"] = request.tools
        try:
            data = post_json(
                f"{self.base_url}/chat/completions",
                payload,
                headers=self._headers(),
                timeout=request.timeout if request.timeout is not None else self.timeout,
            )
        except Exception as exc:
            raise type(exc)(self._sanitize(str(exc))) from None
        choices = data.get("choices") or []
        choice = choices[0] if choices else {}
        message = choice.get("message") or {}
        text = str(message.get("content") or "")
        tool_calls = _parse_tool_calls(message.get("tool_calls"))
        usage = data.get("usage") or {}
        finish_reason = choice.get("finish_reason")
        if not text.strip() and not tool_calls and _budget_exhausted(finish_reason, usage):
            return ProviderResponse(
                "",
                usage=usage,
                raw={
                    "failure": "token_limit",
                    "message": (
                        "The model exhausted its token budget (typically on hidden "
                        "reasoning) before producing an answer."
                    ),
                    "finish_reason": finish_reason,
                },
                finish_reason=finish_reason,
            )
        return ProviderResponse(
            text,
            usage=usage,
            raw=data,
            finish_reason=finish_reason,
            tool_calls=tool_calls,
        )

    def list_models(self) -> list[str]:
        data = get_json(f"{self.base_url}/models", headers=self._headers(), timeout=20)
        return [str(m.get("id")) for m in (data.get("data") or []) if m.get("id")]

    def test_connection(self) -> tuple[bool, str]:
        try:
            models = self.list_models()
        except Exception as exc:
            return (False, f"Connection failed: {self._sanitize(str(exc))}")
        return (True, f"Connected. {len(models)} model(s) available.")
