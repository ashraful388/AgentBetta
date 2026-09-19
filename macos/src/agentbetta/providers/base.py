from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from agentbetta.core.messages import build_messages
from agentbetta.core.models import AgentConfiguration, ProviderResponse, Task


@dataclass
class LLMRequest:
    """Provider-neutral request.

    ``metadata`` carries runtime objects (``task``, ``config``, ``context``) so
    deterministic test providers can inspect the live configuration without the
    provider interface leaking runtime types.
    """

    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] = field(default_factory=list)
    model: str = ""
    max_tokens: int = 2000
    timeout: int = 60
    temperature: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelProvider(Protocol):
    name: str
    is_cloud: bool

    def generate(self, task: Task, config: AgentConfiguration, context: str) -> ProviderResponse: ...


class BaseProvider:
    """Default provider behaviour built on the normalized ``chat`` interface."""

    name = "base"
    is_cloud = False
    model = ""
    supports_native_tools = True

    def chat(self, request: LLMRequest) -> ProviderResponse:
        raise NotImplementedError

    def generate(self, task: Task, config: AgentConfiguration, context: str) -> ProviderResponse:
        request = LLMRequest(
            messages=build_messages(task, config, context),
            tools=[],
            model=self.model,
            max_tokens=config.token_budget,
            timeout=config.max_seconds,
            metadata={"task": task, "config": config, "context": context},
        )
        return self.chat(request)

    def list_models(self) -> list[str]:
        return []

    def test_connection(self) -> tuple[bool, str]:
        return (False, "Connection test is not implemented for this provider.")
