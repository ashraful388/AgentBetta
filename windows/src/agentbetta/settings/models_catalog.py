"""Normalized model catalog and tier mapping.

``model_tier`` in the AgentBetta configuration vector maps, through the user's
tier assignment, to a concrete :class:`ModelProfile` and therefore to a real
provider/model pair.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

TIER_LABELS = {0: "economical", 1: "standard", 2: "high capability"}


def _filtered(cls: type, data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    names = set(getattr(cls, "__dataclass_fields__", {}))
    return {k: v for k, v in data.items() if k in names}


@dataclass
class ModelProfile:
    provider_id: str
    model_id: str
    display_name: str = ""
    tier: int = 1
    supports_tools: bool = True
    supports_streaming: bool = True
    supports_vision: bool = False
    context_window: int | None = None
    max_output_tokens: int | None = None
    input_cost_per_million: float | None = None
    output_cost_per_million: float | None = None
    is_local: bool = False

    @property
    def uid(self) -> str:
        return f"{self.provider_id}::{self.model_id}"

    @property
    def tier_label(self) -> str:
        return TIER_LABELS.get(self.tier, "unknown")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["uid"] = self.uid
        data["tier_label"] = self.tier_label
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ModelProfile":
        return cls(**_filtered(cls, data))


@dataclass
class ModelCatalog:
    models: list[ModelProfile] = field(default_factory=list)

    def add(self, model: ModelProfile) -> ModelProfile:
        self.models = [m for m in self.models if m.uid != model.uid]
        self.models.append(model)
        return model

    def remove(self, uid: str) -> None:
        self.models = [m for m in self.models if m.uid != uid]

    def get(self, uid: str) -> ModelProfile | None:
        return next((m for m in self.models if m.uid == uid), None)

    def for_provider(self, provider_id: str) -> list[ModelProfile]:
        return [m for m in self.models if m.provider_id == provider_id]

    def for_tier(self, tier: int) -> list[ModelProfile]:
        return [m for m in self.models if m.tier == tier]

    def all(self) -> tuple[ModelProfile, ...]:
        return tuple(self.models)
