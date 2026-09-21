"""Desktop application service layer.

Wires settings, secrets, provider construction, runtime construction and run
history. Contains no Qt imports so it can be unit-tested headlessly. The GUI
never implements adaptation logic; it delegates to :class:`AgentBetta`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentbetta.core.models import RuntimeConfig
from agentbetta.desktop.chats import ChatStore
from agentbetta.desktop.projects import ProjectStore
from agentbetta.diagnostics import get_logger
from agentbetta.memory import MemoryManager, MemoryStore, OllamaEmbedder, default_memory_path
from agentbetta.platform import paths
from agentbetta.providers import (
    FakeProvider,
    FallbackProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
    TieredProvider,
)
from agentbetta.settings import AppSettings, SecretStore, SettingsStore, create_secret_store
from agentbetta.tools.browser import BrowserConfig, BrowserSession
from agentbetta.tools.registry import ToolContext

LOCAL_ENDPOINTS = {
    "ollama": "http://127.0.0.1:11434",
}


@dataclass
class RunRequest:
    objective: str
    selection: str = "auto"
    profile: str = "safe"
    mode: str = "adaptive"
    local_only: bool = False
    privacy: bool = False
    workspace: str | None = None
    inputs: list[str] = field(default_factory=list)
    # Previous assistant output in this conversation, attached when the task
    # looks like a follow-up ("run it") so pronouns resolve.
    previous_output: str | None = None


class AppServices:
    def __init__(self, *, settings_store: SettingsStore | None = None,
                 secret_store: SecretStore | None = None,
                 runs_dir: str | Path | None = None,
                 chats_store: ChatStore | None = None,
                 projects_store: ProjectStore | None = None) -> None:
        self.settings_store = settings_store or SettingsStore(paths.settings_path())
        self.secret_store = secret_store or create_secret_store()
        self.settings: AppSettings = self.settings_store.load()
        self._runs_dir_override = Path(runs_dir) if runs_dir else None
        self.log = get_logger("services")
        # Self-heal settings written by older builds: drop catalog models whose
        # provider no longer exists (and stale tier assignments) so the model
        # selector cannot offer unreachable models.
        removed_models, removed_tiers = self.settings.prune_orphan_models()
        if removed_models or removed_tiers:
            self.log.info(
                "pruned %s orphaned model(s) and %s stale tier assignment(s)",
                removed_models, removed_tiers,
            )
            self.settings_store.save(self.settings)
        self.browser: BrowserSession | None = None
        self.projects = projects_store or ProjectStore(
            paths.local_app_data_root() / "projects.json"
        )
        self.chats = chats_store or ChatStore(paths.local_app_data_root() / "chats.json")

    # -- settings ---------------------------------------------------------
    def save(self) -> None:
        self.settings_store.save(self.settings)

    @property
    def runs_dir(self) -> Path:
        if self._runs_dir_override:
            return self._runs_dir_override
        if self.settings.general.data_dir:
            return Path(self.settings.general.data_dir)
        return paths.runs_dir()

    # -- providers --------------------------------------------------------
    def enabled_providers(self) -> list[Any]:
        return [p for p in self.settings.providers if p.enabled]

    def model_choices(self) -> list[tuple[str, str]]:
        """Return selectable models: every enabled provider's models.

        Includes catalog models and each enabled provider's default model even
        if it has not been added to the catalog, so all providers are reachable.
        """

        choices: list[tuple[str, str]] = [("auto", "Auto (AgentBetta)")]
        seen: set[str] = set()
        for model in self.settings.models:
            provider = self.settings.provider(model.provider_id)
            if provider is None or not provider.enabled:
                # Skip models whose provider was removed or disabled so the
                # selector never offers an unreachable model.
                continue
            label = model.display_name or model.model_id
            choices.append((model.uid, f"{label} — {provider.name}"))
            seen.add(model.uid)
        for provider in self.enabled_providers():
            if provider.default_model:
                uid = f"{provider.id}::{provider.default_model}"
                if uid not in seen:
                    choices.append(
                        (uid, f"{provider.default_model} — {provider.name} (provider default)")
                    )
                    seen.add(uid)
        return choices

    def build_provider(self, selection: str, *, local_only: bool = False) -> Any:
        if selection in ("fake", ""):
            return FakeProvider()
        if selection == "auto":
            if not self.settings.providers and not self.settings.models:
                # Nothing configured yet: stay usable offline with the deterministic provider.
                return FakeProvider()
            return self._build_auto(local_only=local_only)
        provider_id, _, model_id = selection.partition("::")
        profile = self.settings.provider(provider_id)
        if profile is None:
            raise ValueError(f"Unknown provider id: {provider_id}")
        provider = self._provider_for_profile(
            profile, model_id or profile.default_model, local_only=local_only
        )
        if self.settings.general.provider_fallback:
            fallbacks = self._fallback_providers(profile, local_only=local_only)
            if fallbacks:
                return FallbackProvider(provider, fallbacks)
        return provider

    def _fallback_providers(self, primary: Any, *, local_only: bool) -> list[Any]:
        """Other enabled providers to try if the primary fails (local first)."""

        others = [p for p in self.enabled_providers() if p.id != primary.id]
        cloud = [p for p in others if p.is_cloud]
        local = [p for p in others if not p.is_cloud]
        if local_only:
            ordered = local
        elif primary.is_cloud:
            # Match the primary's locality first: a cloud task should fall back
            # to another (capable) cloud model before dropping to a small local
            # model, which would produce poor results on complex tasks.
            ordered = cloud + local
        else:
            ordered = local + cloud
        fallbacks: list[Any] = []
        for profile in ordered:
            try:
                fallbacks.append(
                    self._provider_for_profile(
                        profile, profile.default_model, local_only=local_only
                    )
                )
            except Exception:
                continue
            if len(fallbacks) >= 3:
                break
        # Always keep a local model as a last resort when one is available, even
        # if several cloud fallbacks were already added. A small local model is
        # better than failing outright when every cloud provider is unreachable.
        if not local_only and local and not any(
            not getattr(f, "is_cloud", True) for f in fallbacks
        ):
            try:
                fallbacks.append(
                    self._provider_for_profile(
                        local[0], local[0].default_model, local_only=local_only
                    )
                )
            except Exception:
                pass
        return fallbacks

    def _build_auto(self, *, local_only: bool) -> TieredProvider:
        tiers: dict[int, Any] = {}
        for tier in (0, 1, 2):
            model = self.settings.model_for_tier(tier)
            if model is None:
                continue
            profile = self.settings.provider(model.provider_id)
            if profile is None or not profile.enabled:
                continue
            if local_only and profile.is_cloud:
                continue
            tiers[tier] = self._provider_for_profile(profile, model.model_id, local_only=local_only)
        # Fill unmapped tiers from catalog models by their assigned tier so that
        # Auto works even if the user has not mapped every tier explicitly.
        for tier in (0, 1, 2):
            if tier in tiers:
                continue
            for model in self.settings.models:
                if model.tier != tier:
                    continue
                profile = self.settings.provider(model.provider_id)
                if profile is None or not profile.enabled:
                    continue
                if local_only and profile.is_cloud:
                    continue
                tiers[tier] = self._provider_for_profile(profile, model.model_id, local_only=local_only)
                break
        if not tiers:
            for profile in self.enabled_providers():
                if local_only and profile.is_cloud:
                    continue
                tiers[0] = self._provider_for_profile(profile, profile.default_model, local_only=local_only)
                break
        if not tiers:
            raise ValueError(
                "No usable model configured for Auto mode. Install Ollama or add a provider in Settings."
            )
        return TieredProvider(tiers, local_only=local_only)

    def _provider_for_profile(self, profile: Any, model: str | None, *, local_only: bool = False) -> Any:
        if profile.is_cloud and local_only:
            raise PermissionError("Local-only run cannot use a cloud provider")
        if profile.type == "ollama":
            return OllamaProvider(
                model=model or profile.default_model or "qwen3:1.7b",
                base_url=profile.base_url or LOCAL_ENDPOINTS["ollama"],
                timeout=profile.timeout,
            )
        api_key = self.secret_store.get_secret(profile.secret_ref()) if profile.is_cloud else None
        return OpenAICompatibleProvider(
            model=model or profile.default_model or "",
            base_url=profile.base_url,
            api_key=api_key,
            timeout=profile.timeout,
            tls_verify=profile.tls_verify,
        )

    def test_provider(self, profile: Any) -> tuple[bool, str]:
        try:
            provider = self._provider_for_profile(profile, profile.default_model)
            return provider.test_connection()
        except Exception as exc:  # sanitized, no key
            return (False, f"{type(exc).__name__}: {exc}")

    def refresh_models(self, profile: Any) -> list[str]:
        provider = self._provider_for_profile(profile, profile.default_model)
        return provider.list_models()

    def ollama_status(self, endpoint: str | None = None) -> tuple[bool, str, list[str]]:
        provider = OllamaProvider(base_url=endpoint or LOCAL_ENDPOINTS["ollama"])
        ok, message = provider.test_connection()
        models = provider.list_models() if ok else []
        return ok, message, models

    # -- runtime ----------------------------------------------------------
    def browser_session(self) -> BrowserSession:
        if self.browser is None:
            general = self.settings.general
            self.browser = BrowserSession(
                BrowserConfig(
                    engine=general.browser_engine,
                    headless=not general.browser_visible,
                    downloads_dir=general.browser_download_dir,
                )
            )
        return self.browser

    def close_browser(self) -> None:
        """Close the browser session.

        Playwright's sync API is bound to the thread that started it, and each
        run executes on a fresh worker thread. Closing the session after every
        run lets the next run start Playwright cleanly in its own thread. The
        on-disk browser profile is preserved.
        """

        if self.browser is not None:
            try:
                self.browser.close()
            except Exception:  # never let browser teardown break a run
                pass

    def build_runtime(self, provider: Any, *, approvals: Any, event_bus: Any,
                      privacy: bool = False, run_dir: str | Path | None = None) -> Any:
        from agentbetta.core.runtime import AgentBetta

        browser = self.browser_session() if self.settings.general.browser_enabled else None
        memory = self.build_memory()
        ctx = ToolContext(approvals=approvals, browser=browser, memory=memory)
        return AgentBetta(
            provider,
            runtime_config=RuntimeConfig(
                record_runs=True,
                run_dir=str(run_dir or self.runs_dir),
                privacy_mode=privacy,
                memory_items=self.settings.general.memory_retrieve if memory else 0,
                max_total_seconds=self.settings.general.max_run_seconds,
                unlimited=bool(getattr(self.settings.general, "unlimited", True)),
            ),
            event_bus=event_bus,
            approvals=approvals,
            tool_context=ctx,
            memory=memory,
        )

    # -- long-term memory -------------------------------------------------
    def memory_path(self) -> Path:
        return default_memory_path(paths.local_app_data_root())

    def build_memory(self) -> MemoryManager | None:
        general = self.settings.general
        if not getattr(general, "memory_enabled", True):
            return None
        embedder = None
        if getattr(general, "memory_embeddings", False):
            embedder = OllamaEmbedder(model=general.memory_embedding_model)
        return MemoryManager(
            MemoryStore(self.memory_path()),
            max_entries=general.memory_max_entries,
            default_k=general.memory_retrieve,
            auto_capture=general.memory_auto_capture,
            embedder=embedder,
        )

    def memory_entries(self) -> list[dict[str, Any]]:
        manager = self.build_memory()
        if manager is None:
            return []
        return [entry.to_dict() for entry in manager.all()]

    def memory_add(self, text: str, *, kind: str = "fact", tags: list[str] | None = None) -> Any:
        manager = self.build_memory()
        if manager is None:
            raise ValueError("Long-term memory is disabled")
        return manager.add(text, kind=kind, tags=tags, source="explicit")

    def memory_forget(self, identifier: str) -> bool:
        manager = self.build_memory()
        if manager is None:
            return False
        return manager.forget(identifier)

    def memory_clear(self) -> int:
        manager = self.build_memory()
        if manager is None:
            return 0
        return manager.clear()

    # -- updates ----------------------------------------------------------
    def check_for_updates(self) -> Any:
        from agentbetta import __version__
        from agentbetta.updates import check_for_update

        general = self.settings.general
        info = check_for_update(
            __version__, general.update_repo, channel=general.update_channel
        )
        return info

    def download_update(self, info: Any, progress: Any = None) -> Path:
        from agentbetta.updates import download_asset, download_checksums, select_asset

        asset = select_asset(info)
        if asset is None:
            raise RuntimeError("This release has no installer for your platform.")
        path = download_asset(asset, progress=progress)
        checksums = download_checksums(info)
        return path, checksums

    def install_update(self, path: Path, checksums: dict[str, str] | None = None) -> str:
        from agentbetta.updates import install_update, verify_checksum

        expected = (checksums or {}).get(path.name.lower())
        if expected and not verify_checksum(path, expected):
            raise RuntimeError("Downloaded update failed its SHA-256 check; aborting.")
        return install_update(path)

    # -- tools ------------------------------------------------------------
    def tool_catalog(self) -> list[dict[str, Any]]:
        from agentbetta.tools.catalog import full_registry

        registry = full_registry()
        catalog: list[dict[str, Any]] = []
        for name in registry.names():
            spec = registry.spec(name)
            if spec is None:
                continue
            catalog.append(
                {
                    "name": spec.name,
                    "permission": spec.permission,
                    "risk": spec.risk,
                    "description": spec.description,
                }
            )
        return catalog

    # -- usage ------------------------------------------------------------
    def usage_for_record(self, record: dict[str, Any] | None) -> dict[str, Any]:
        """Aggregate provider usage across attempts of a stored run record."""

        usage: dict[str, Any] = {}
        if not record:
            return usage
        for attempt in record.get("attempts") or []:
            provider_usage = attempt.get("provider_usage") or {}
            for key in ("prompt_tokens", "completion_tokens", "total_tokens",
                        "prompt_eval_count", "eval_count", "cost_usd"):
                value = provider_usage.get(key)
                if isinstance(value, (int, float)):
                    usage[key] = usage.get(key, 0) + value
            if provider_usage.get("model_calls"):
                usage["model_calls"] = usage.get("model_calls", 0) + provider_usage["model_calls"]
        return usage

    # -- history ----------------------------------------------------------
    def list_runs(self, limit: int | None = None) -> list[dict[str, Any]]:
        directory = self.runs_dir
        if not directory.exists():
            return []
        runs: list[dict[str, Any]] = []
        for path in directory.glob("*.json"):
            try:
                runs.append(json.loads(path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        runs.sort(key=lambda r: str(r.get("started_at", "")), reverse=True)
        return runs[: limit or self.settings.general.history_limit]

    def load_run(self, run_id: str) -> dict[str, Any] | None:
        path = self.runs_dir / f"{run_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def clear_history(self) -> int:
        directory = self.runs_dir
        if not directory.exists():
            return 0
        removed = 0
        for path in directory.glob("*.json"):
            try:
                path.unlink()
                removed += 1
            except OSError:
                continue
        frontier = directory.parent / "frontier.jsonl"
        if frontier.exists():
            try:
                frontier.unlink()
            except OSError:
                pass
        return removed
