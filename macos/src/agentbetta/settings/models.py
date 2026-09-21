"""Typed application settings for the AgentBetta Windows desktop client.

The settings layer is intentionally secret-free: it stores provider and model
metadata only. Any API key is referenced by name and stored in the platform
secret store (see :mod:`agentbetta.settings.secrets`).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from agentbetta.settings.models_catalog import ModelProfile
from agentbetta.settings.provider_profiles import ProviderProfile

SETTINGS_SCHEMA_VERSION = "1"

THEMES = ("system", "light", "dark")
MODES = ("adaptive", "fixed", "wholesale")
PROVIDER_MODES = ("auto", "specific")
LAUNCH_BEHAVIORS = ("new_task", "last_task")

_SECRET_KEYS = {
    "api_key",
    "apikey",
    "secret",
    "password",
    "passwd",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "bearer",
    "client_secret",
}


def _filtered(cls: type, data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    names = set(getattr(cls, "__dataclass_fields__", {}))
    return {k: v for k, v in data.items() if k in names}


def assert_no_secret_values(obj: Any, _path: str = "$") -> None:
    """Raise ``ValueError`` if a secret-looking key carries a value.

    This guard is used by the settings store to guarantee that persisted
    settings can never accidentally contain a credential.
    """

    if isinstance(obj, dict):
        for key, value in obj.items():
            lowered = str(key).lower()
            suspect = lowered in _SECRET_KEYS or lowered.endswith(
                ("_secret", "_password", "_api_key", "_token")
            )
            if suspect and value not in (None, "", [], {}):
                raise ValueError(f"Refusing to persist secret-like value at {_path}.{key}")
            assert_no_secret_values(value, f"{_path}.{key}")
    elif isinstance(obj, (list, tuple)):
        for index, value in enumerate(obj):
            assert_no_secret_values(value, f"{_path}[{index}]")


@dataclass
class GeneralSettings:
    theme: str = "system"
    default_mode: str = "adaptive"
    default_provider_mode: str = "auto"
    default_model_key: str | None = None
    data_dir: str | None = None
    record_runs: bool = True
    privacy_mode: bool = False
    local_only_default: bool = False
    default_permission_profile: str = "safe"
    # Whole-run wall-clock limit in seconds; 0 means no limit.
    max_run_seconds: int = 0
    # When True, a run has no token budget, per-call timeout or interaction
    # caps: it continues until it succeeds or is cancelled.
    unlimited: bool = True
    # When True, high-risk actions run without a prompt for every profile.
    # (The Full Computer profile always auto-approves.)
    auto_approve_high_risk: bool = False
    history_limit: int = 500
    launch_behavior: str = "new_task"
    first_run_complete: bool = False
    browser_enabled: bool = True
    browser_engine: str = "msedge"
    browser_visible: bool = False
    browser_download_dir: str | None = None
    memory_enabled: bool = True
    memory_auto_capture: bool = True
    memory_max_entries: int = 1000
    memory_retrieve: int = 3
    memory_embeddings: bool = False
    memory_embedding_model: str = "nomic-embed-text"
    provider_fallback: bool = True
    auto_check_updates: bool = True
    update_channel: str = "stable"
    update_repo: str = "ashrafulbabu/AgentBetta"
    last_update_check: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "GeneralSettings":
        return cls(**_filtered(cls, data))


@dataclass
class AppSettings:
    schema_version: str = SETTINGS_SCHEMA_VERSION
    general: GeneralSettings = field(default_factory=GeneralSettings)
    providers: list[ProviderProfile] = field(default_factory=list)
    models: list[ModelProfile] = field(default_factory=list)
    tier_map: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "general": self.general.to_dict(),
            "providers": [p.to_dict() for p in self.providers],
            "models": [m.to_dict() for m in self.models],
            "tier_map": dict(self.tier_map),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AppSettings":
        data = data or {}
        providers = [ProviderProfile.from_dict(p) for p in (data.get("providers") or [])]
        models = [ModelProfile.from_dict(m) for m in (data.get("models") or [])]
        tier_map = {str(k): str(v) for k, v in (data.get("tier_map") or {}).items()}
        return cls(
            schema_version=str(data.get("schema_version") or SETTINGS_SCHEMA_VERSION),
            general=GeneralSettings.from_dict(data.get("general")),
            providers=providers,
            models=models,
            tier_map=tier_map,
        )

    # -- lookup helpers -------------------------------------------------

    def provider(self, provider_id: str) -> ProviderProfile | None:
        return next((p for p in self.providers if p.id == provider_id), None)

    def model(self, uid: str) -> ModelProfile | None:
        return next((m for m in self.models if m.uid == uid), None)

    def models_for_provider(self, provider_id: str) -> list[ModelProfile]:
        return [m for m in self.models if m.provider_id == provider_id]

    def model_for_tier(self, tier: int) -> ModelProfile | None:
        uid = self.tier_map.get(str(tier))
        return self.model(uid) if uid else None

    def prune_orphan_models(self) -> tuple[int, int]:
        """Drop catalog models whose provider no longer exists, plus stale tier
        assignments that point at a removed model.

        Returns ``(models_removed, tiers_removed)``.
        """

        valid_providers = {p.id for p in self.providers}
        kept = [m for m in self.models if m.provider_id in valid_providers]
        models_removed = len(self.models) - len(kept)
        self.models = kept
        valid_uids = {m.uid for m in self.models}
        pruned_map = {tier: uid for tier, uid in self.tier_map.items() if uid in valid_uids}
        tiers_removed = len(self.tier_map) - len(pruned_map)
        self.tier_map = pruned_map
        return models_removed, tiers_removed
