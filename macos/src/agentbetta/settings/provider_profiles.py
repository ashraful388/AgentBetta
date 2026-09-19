"""Provider profile abstraction.

A :class:`ProviderProfile` stores only non-secret metadata. The API key is
referenced by name (``api_key_ref``) and lives in the platform secret store.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


def _filtered(cls: type, data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    names = set(getattr(cls, "__dataclass_fields__", {}))
    return {k: v for k, v in data.items() if k in names}


PROVIDER_TYPES = ("ollama", "openai_compatible")


@dataclass
class ProviderProfile:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = "OpenAI-compatible"
    type: str = "openai_compatible"
    base_url: str = ""
    is_cloud: bool = True
    enabled: bool = True
    default_model: str | None = None
    timeout: int = 120
    tls_verify: bool = True
    api_key_ref: str | None = None
    options: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ProviderProfile":
        return cls(**_filtered(cls, data))

    def secret_ref(self) -> str:
        return self.api_key_ref or f"provider:{self.id}"


@dataclass(frozen=True)
class ProviderPreset:
    key: str
    label: str
    type: str
    base_url: str
    is_cloud: bool
    needs_key: bool
    default_model: str | None = None
    note: str = ""


PRESETS: dict[str, ProviderPreset] = {
    "ollama": ProviderPreset(
        key="ollama",
        label="Ollama (local)",
        type="ollama",
        base_url="http://127.0.0.1:11434",
        is_cloud=False,
        needs_key=False,
        default_model="qwen3:1.7b",
        note="Local Ollama server. No cloud API key required.",
    ),
    "lmstudio": ProviderPreset(
        key="lmstudio",
        label="LM Studio (local, OpenAI-compatible)",
        type="openai_compatible",
        base_url="http://127.0.0.1:1234/v1",
        is_cloud=False,
        needs_key=False,
        note="Enable the local server in LM Studio.",
    ),
    "vllm": ProviderPreset(
        key="vllm",
        label="vLLM (local, OpenAI-compatible)",
        type="openai_compatible",
        base_url="http://127.0.0.1:8000/v1",
        is_cloud=False,
        needs_key=False,
    ),
    "openai": ProviderPreset(
        key="openai",
        label="OpenAI",
        type="openai_compatible",
        base_url="https://api.openai.com/v1",
        is_cloud=True,
        needs_key=True,
        default_model="gpt-4o-mini",
    ),
    "openrouter": ProviderPreset(
        key="openrouter",
        label="OpenRouter",
        type="openai_compatible",
        base_url="https://openrouter.ai/api/v1",
        is_cloud=True,
        needs_key=True,
    ),
    "deepseek": ProviderPreset(
        key="deepseek",
        label="DeepSeek",
        type="openai_compatible",
        base_url="https://api.deepseek.com/v1",
        is_cloud=True,
        needs_key=True,
        default_model="deepseek-chat",
    ),
    "zai_glm": ProviderPreset(
        key="zai_glm",
        label="Z.ai / GLM",
        type="openai_compatible",
        base_url="https://api.z.ai/api/paas/v4",
        is_cloud=True,
        needs_key=True,
        default_model="glm-4-flash",
    ),
    "gemini": ProviderPreset(
        key="gemini",
        label="Google Gemini (OpenAI-compatible endpoint)",
        type="openai_compatible",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        is_cloud=True,
        needs_key=True,
        default_model="gemini-1.5-flash",
    ),
    "custom": ProviderPreset(
        key="custom",
        label="Custom OpenAI-compatible endpoint",
        type="openai_compatible",
        base_url="",
        is_cloud=True,
        needs_key=True,
    ),
}


def preset(key: str) -> ProviderPreset | None:
    return PRESETS.get(key)


def profile_from_preset(key: str, *, name: str | None = None, base_url: str | None = None,
                        is_cloud: bool | None = None) -> ProviderProfile:
    p = PRESETS.get(key)
    if p is None:
        raise KeyError(f"Unknown provider preset: {key}")
    return ProviderProfile(
        name=name or p.label,
        type=p.type,
        base_url=base_url if base_url is not None else p.base_url,
        is_cloud=p.is_cloud if is_cloud is None else is_cloud,
        default_model=p.default_model,
    )
