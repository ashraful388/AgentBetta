"""Auditable JSON tool-request fallback protocol.

Some local/compatible models do not expose native tool calling. When tools are
offered, the system prompt documents a single strict JSON envelope. This parser
accepts only that envelope and only tool names that are exposed by the current
configuration. Arbitrary prose is never parsed as an executable command.
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Iterator

from agentbetta.core.models import ToolCall

_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)

TOOL_PROTOCOL_INSTRUCTIONS = (
    "Tool protocol: to call a tool reply with a single JSON object and nothing else:\n"
    '{"action": "tool", "tool": "<tool_name>", "arguments": { ... }}\n'
    'When you have the final answer, reply with {"action": "final", "answer": "<answer>"} '
    "or simply your normal final answer. Only use tools listed by the system."
)


def _candidate_objects(text: str) -> Iterator[str]:
    for match in _FENCE.finditer(text):
        yield match.group(1)
    start = text.find("{")
    while start != -1:
        depth = 0
        for index in range(start, len(text)):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    yield text[start : index + 1]
                    break
        start = text.find("{", start + 1)


def parse_tool_protocol(text: str, allowed_tools: set[str]) -> tuple[ToolCall | None, str | None]:
    """Return ``(tool_call, final_answer)`` parsed from the strict envelope."""

    if not text:
        return None, None
    for blob in _candidate_objects(text):
        try:
            data = json.loads(blob)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        action = str(data.get("action") or "").lower()
        if action in ("final", "answer") or "final" in data:
            answer = data.get("answer", data.get("final"))
            if isinstance(answer, str) and answer.strip():
                return None, answer
        name = data.get("tool") or data.get("tool_name") or data.get("name")
        arguments = data.get("arguments", data.get("args", {}))
        if isinstance(name, str) and name in allowed_tools:
            if not isinstance(arguments, dict):
                arguments = {}
            return ToolCall(call_id="fallback_" + uuid.uuid4().hex[:8], tool_name=name, arguments=arguments), None
    return None, None


__all__ = ["TOOL_PROTOCOL_INSTRUCTIONS", "parse_tool_protocol"]
