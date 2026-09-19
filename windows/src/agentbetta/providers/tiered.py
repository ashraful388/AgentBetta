"""Auto model selection: routes each request to the provider mapped to the
current ``model_tier``.

This is what makes an adaptive model-tier change select a *different real
model* rather than merely changing an integer.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from agentbetta.core.models import AgentConfiguration, ProviderResponse
from agentbetta.providers.base import BaseProvider, LLMRequest


class TieredProvider(BaseProvider):
    name = "agentbetta-auto"
    model = "auto"

    def __init__(self, tier_providers: dict[int, Any], *, local_only: bool = False) -> None:
        if not tier_providers:
            raise ValueError("TieredProvider requires at least one tier mapping")
        self.tier_providers = dict(sorted(tier_providers.items()))
        self.local_only = local_only
        self.is_cloud = any(getattr(p, "is_cloud", False) for p in self.tier_providers.values())
        self.last_model_id: str | None = None
        self.last_provider_name: str | None = None
        self.last_tier: int | None = None

    def provider_for(self, config: AgentConfiguration | None) -> Any:
        tier = config.model_tier if config is not None else min(self.tier_providers)
        if tier in self.tier_providers:
            return self.tier_providers[tier]
        # nearest available tier
        available = sorted(self.tier_providers)
        chosen = min(available, key=lambda t: abs(t - tier))
        return self.tier_providers[chosen]

    def chat(self, request: LLMRequest) -> ProviderResponse:
        config = (request.metadata or {}).get("config")
        provider = self.provider_for(config)
        if self.local_only and getattr(provider, "is_cloud", False):
            raise PermissionError("Local-only run cannot use a cloud provider")
        # Try the selected tier first, then the other configured tiers.
        candidates = [provider] + [
            p for p in self.tier_providers.values() if p is not provider
        ]
        last: Exception | None = None
        for index, candidate in enumerate(candidates):
            if self.local_only and getattr(candidate, "is_cloud", False):
                continue
            try:
                target = request
                if index > 0:
                    target = replace(request, model=getattr(candidate, "model", "") or request.model)
                response = candidate.chat(target)
                provider = candidate
                break
            except Exception as exc:
                last = exc
                continue
        else:
            if last is not None:
                raise last
            raise RuntimeError("No tier provider is available")
        usage = dict(response.usage or {})
        usage["model_tier"] = config.model_tier if config is not None else None
        usage["model_id"] = getattr(provider, "model", None)
        usage["provider"] = getattr(provider, "name", None)
        response.usage = usage
        self.last_model_id = getattr(provider, "model", None)
        self.last_provider_name = getattr(provider, "name", None)
        self.last_tier = usage["model_tier"]
        return response

    def list_models(self) -> list[str]:
        models: list[str] = []
        for provider in self.tier_providers.values():
            models.extend(provider.list_models())
        return models

    def test_connection(self) -> tuple[bool, str]:
        messages = []
        ok_any = False
        for tier, provider in self.tier_providers.items():
            ok, message = provider.test_connection()
            ok_any = ok_any or ok
            messages.append(f"tier {tier} ({getattr(provider, 'name', '?')}): {message}")
        return ok_any, "; ".join(messages)


__all__ = ["TieredProvider"]
