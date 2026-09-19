import json
from pathlib import Path

import pytest

from agentbetta import AgentBetta, RuntimeConfig
from agentbetta.core.models import AgentConfiguration, ProviderResponse
from agentbetta.desktop.services import AppServices
from agentbetta.providers import FakeProvider, TieredProvider
from agentbetta.providers.base import BaseProvider, LLMRequest
from agentbetta.settings import InMemorySecretStore, ModelProfile, ProviderProfile, SettingsStore


class _MarkerProvider(BaseProvider):
    is_cloud = False

    def __init__(self, name: str, marker: str):
        self.name = name
        self.marker = marker
        self.model = marker

    def chat(self, request: LLMRequest) -> ProviderResponse:
        config = (request.metadata or {}).get("config")
        task = (request.metadata or {}).get("task")
        text = getattr(task, "objective", "") or ""
        if "[require-model-tier-2]" in text and config is not None and config.model_tier < 2:
            return ProviderResponse("", raw={"failure": "model_insufficient"})
        return ProviderResponse(f"answered-by:{self.marker}")


def _services(tmp_path) -> AppServices:
    return AppServices(
        settings_store=SettingsStore(tmp_path / "settings.json"),
        secret_store=InMemorySecretStore(),
        runs_dir=tmp_path / "runs",
    )


def test_tiered_provider_routes_by_config_tier():
    tiered = TieredProvider({0: _MarkerProvider("p0", "m0"), 2: _MarkerProvider("p2", "m2")})
    request = LLMRequest(messages=[], metadata={"config": AgentConfiguration(model_tier=2)})
    assert tiered.chat(request).text == "answered-by:m2"
    request0 = LLMRequest(messages=[], metadata={"config": AgentConfiguration(model_tier=0)})
    assert tiered.chat(request0).text == "answered-by:m0"


def test_adaptive_model_tier_changes_actual_model(tmp_path):
    tiered = TieredProvider(
        {0: _MarkerProvider("p0", "m0"), 1: _MarkerProvider("p1", "m1"), 2: _MarkerProvider("p2", "m2")}
    )
    agent = AgentBetta(tiered, runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs")))
    result = agent.run("[require-model-tier-2] solve")
    assert result.success and "m2" in result.output
    record = json.loads(Path(result.record_path).read_text(encoding="utf-8"))
    model_ids = [attempt["provider_usage"].get("model_id") for attempt in record["attempts"]]
    assert model_ids == ["m0", "m1", "m2"]


def test_local_only_mode_blocks_cloud_tier():
    cloud = _MarkerProvider("cloud", "cm")
    cloud.is_cloud = True
    tiered = TieredProvider({0: cloud}, local_only=True)
    with pytest.raises(PermissionError):
        tiered.chat(LLMRequest(messages=[], metadata={"config": AgentConfiguration()}))


def test_services_auto_uses_tier_map(tmp_path):
    services = _services(tmp_path)
    profile = ProviderProfile(name="Ollama", type="ollama", base_url="http://127.0.0.1:11434", is_cloud=False)
    services.settings.providers.append(profile)
    services.settings.models.append(
        ModelProfile(provider_id=profile.id, model_id="qwen3:1.7b", is_local=True)
    )
    services.settings.tier_map = {"1": f"{profile.id}::qwen3:1.7b"}
    provider = services.build_provider("auto")
    assert isinstance(provider, TieredProvider)
    assert provider.provider_for(AgentConfiguration(model_tier=1)).model == "qwen3:1.7b"


def test_services_auto_local_only_rejects_cloud_only(tmp_path):
    services = _services(tmp_path)
    profile = ProviderProfile(name="OpenAI", type="openai_compatible",
                              base_url="https://api.openai.com/v1", is_cloud=True)
    services.settings.providers.append(profile)
    services.settings.models.append(ModelProfile(provider_id=profile.id, model_id="gpt-4o-mini"))
    services.settings.tier_map = {"0": f"{profile.id}::gpt-4o-mini"}
    with pytest.raises((ValueError, PermissionError)):
        services.build_provider("auto", local_only=True)


def test_services_auto_fills_unmapped_tiers_from_catalog(tmp_path):
    services = _services(tmp_path)
    cloud = ProviderProfile(name="Cloud", type="openai_compatible",
                            base_url="https://api.example.com/v1", is_cloud=True)
    local = ProviderProfile(name="Ollama", type="ollama",
                            base_url="http://127.0.0.1:11434", is_cloud=False)
    services.settings.providers.extend([cloud, local])
    services.settings.models.append(ModelProfile(provider_id=cloud.id, model_id="cloud-model", tier=0))
    services.settings.models.append(ModelProfile(provider_id=local.id, model_id="local-model", tier=1))
    services.settings.tier_map = {"0": f"{cloud.id}::cloud-model"}
    provider = services.build_provider("auto")
    assert isinstance(provider, TieredProvider)
    assert provider.provider_for(AgentConfiguration(model_tier=0)).model == "cloud-model"
    assert provider.provider_for(AgentConfiguration(model_tier=1)).model == "local-model"


def test_model_choices_include_provider_defaults(tmp_path):
    services = _services(tmp_path)
    cloud = ProviderProfile(name="BAI", type="openai_compatible",
                            base_url="https://api.b.ai/v1", is_cloud=True,
                            default_model="qwen3.8-flash")
    services.settings.providers.append(cloud)
    uids = [uid for uid, _ in services.model_choices()]
    assert f"{cloud.id}::qwen3.8-flash" in uids
    cloud.enabled = False
    uids = [uid for uid, _ in services.model_choices()]
    assert f"{cloud.id}::qwen3.8-flash" not in uids


def test_services_fake_selection(tmp_path):
    assert isinstance(_services(tmp_path).build_provider("fake"), FakeProvider)


def test_api_key_never_written_to_settings_file(tmp_path):
    services = _services(tmp_path)
    profile = ProviderProfile(name="OpenAI", is_cloud=True)
    services.settings.providers.append(profile)
    services.secret_store.set_secret(profile.secret_ref(), "sk-super-secret")
    services.save()
    text = (tmp_path / "settings.json").read_text(encoding="utf-8")
    assert "sk-super-secret" not in text


def test_ollama_status_handles_unreachable_endpoint(tmp_path):
    ok, message, models = _services(tmp_path).ollama_status("http://127.0.0.1:9")
    assert ok is False
    assert models == []
