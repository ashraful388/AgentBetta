"""A provider that falls back to others when the primary fails.

Used so a transient provider error (timeout, 5xx) or a per-model rejection does
not end the run when another configured model is available. Fallbacks are chosen
by the caller (see ``AppServices``) and honour local-only mode.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from agentbetta.core.models import ProviderResponse
from agentbetta.providers.base import BaseProvider, LLMRequest


class FallbackProvider(BaseProvider):
    def __init__(self, primary: Any, fallbacks: list[Any]) -> None:
        self.primary = primary
        self.fallbacks = [f for f in fallbacks if f is not None]
        self.is_cloud = getattr(primary, "is_cloud", False)
        self.model = getattr(primary, "model", "")
        self.last_model_id = getattr(primary, "model", None)
        self.last_provider_name = getattr(primary, "name", None)
        self.used_fallback = False

    def _chain(self) -> list[Any]:
        return [self.primary, *self.fallbacks]

    def chat(self, request: LLMRequest) -> ProviderResponse:
        last: Exception | None = None
        for index, provider in enumerate(self._chain()):
            try:
                target = request
                if index > 0:
                    target = replace(request, model=getattr(provider, "model", "") or request.model)
                response = provider.chat(target)
                self.last_model_id = getattr(provider, "model", None)
                self.last_provider_name = getattr(provider, "name", None)
                self.used_fallback = index > 0
                return response
            except Exception as exc:
                last = exc
                continue
        if last is not None:
            raise last
        raise RuntimeError("No provider is available")

    def list_models(self) -> list[str]:
        models: list[str] = []
        for provider in self._chain():
            try:
                models.extend(provider.list_models())
            except Exception:
                pass
        return models

    def test_connection(self) -> tuple[bool, str]:
        return self.primary.test_connection()


__all__ = ["FallbackProvider"]
