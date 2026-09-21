from __future__ import annotations
import json
import re
import uuid
from typing import Any

from agentbetta.core.models import ProviderResponse, ToolCall
from agentbetta.providers.base import BaseProvider, LLMRequest

_SIMPLE_CALC = re.compile(r"(?:calculate|compute)\s+([0-9.\s+\-*/()%]+)")


class FakeProvider(BaseProvider):
    """Deterministic offline provider.

    Supports:
    - structured failure hooks used by adaptation tests;
    - an auditable tool-call fixture, either explicit
      (``[call-tool:calculator]{"expression": "17*23"}``) or natural arithmetic;
    - a stable final summary otherwise.
    """

    name = "fake"
    is_cloud = False
    model = "fake-model"

    def chat(self, request: LLMRequest) -> ProviderResponse:
        meta = request.metadata or {}
        config = meta.get("config")
        task = meta.get("task")
        context = str(meta.get("context") or "")
        text = (getattr(task, "objective", "") or "").strip()

        if config is not None:
            # Deterministic failure hooks are useful for adaptation tests.
            if "[require-model-tier-2]" in text and config.model_tier < 2:
                return ProviderResponse("", raw={"failure": "model_insufficient"})
            if "[require-context-24000]" in text and config.context_chars < 24_000:
                return ProviderResponse("", raw={"failure": "context_truncated"})
            if "[require-write]" in text and not config.permissions.permits("file_write"):
                return ProviderResponse("", raw={"failure": "permission_denied"})

        tool_names = {(t.get("function") or {}).get("name") for t in (request.tools or [])}
        tool_messages = [m for m in request.messages if m.get("role") == "tool"]
        if tool_messages:
            observation = str(tool_messages[-1].get("content", ""))
            match = _SIMPLE_CALC.search(text.lower())
            if match:
                expr = match.group(1).strip().rstrip(".?")
                return ProviderResponse(f"{expr} = {observation}", usage={"model_calls": 1})
            return ProviderResponse(f"Tool observation: {observation}", usage={"model_calls": 1})

        explicit = re.search(r"\[call-tool:([a-z_]+)\](?:\s*(\{.*\}))?", text)
        if explicit:
            name = explicit.group(1)
            if name not in tool_names:
                return ProviderResponse("", raw={"failure": "missing_tool"})
            arguments = self._explicit_arguments(name, explicit.group(2))
            return self._tool_call(name, arguments)

        if "calculator" in tool_names:
            match = _SIMPLE_CALC.search(text.lower())
            if match:
                expr = match.group(1).strip().rstrip(".?")
                return self._tool_call("calculator", {"expression": expr})

        summary = (
            "AgentBetta completed the offline deterministic task. "
            "Its runtime uses task-conditioned configuration, runtime verification, "
            "selective adaptation, and research-mode contraction proposals."
        )
        if context:
            limit = (
                config.context_chars
                if config is not None and config.context_chars > 0
                else len(context)
            )
            summary += f" Context supplied: {min(len(context), limit)} characters."
        return ProviderResponse(summary, usage={"model_calls": 1})

    @staticmethod
    def _tool_call(name: str, arguments: dict[str, Any]) -> ProviderResponse:
        return ProviderResponse(
            "",
            finish_reason="tool_calls",
            tool_calls=[ToolCall(call_id="call_" + uuid.uuid4().hex[:8], tool_name=name, arguments=arguments)],
        )

    @staticmethod
    def _explicit_arguments(name: str, raw_json: str | None) -> dict[str, Any]:
        if raw_json:
            try:
                parsed = json.loads(raw_json)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
        if name in ("list_directory", "read_text_file"):
            return {"path": "."}
        if name == "calculator":
            return {"expression": "2+2"}
        return {}
