import json

import pytest

from agentbetta.settings import (
    AppSettings,
    GeneralSettings,
    ProviderProfile,
    SettingsStore,
    assert_no_secret_values,
)
from agentbetta.settings.models import DEFAULT_UPDATE_REPO


def test_missing_file_returns_defaults(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    settings = store.load()
    assert settings.general.default_mode == "adaptive"
    assert settings.general.update_repo == DEFAULT_UPDATE_REPO
    assert settings.general.update_channel == "prerelease"
    assert settings.providers == []


def test_legacy_update_repo_is_migrated(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"general": {"update_repo": "ashrafulbabu/AgentBetta"}}),
        encoding="utf-8",
    )
    settings = SettingsStore(path).load()
    assert settings.general.update_repo == DEFAULT_UPDATE_REPO
    assert settings.general.update_channel == "prerelease"


def test_null_update_repo_uses_default(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"general": {"update_repo": None}}),
        encoding="utf-8",
    )
    settings = SettingsStore(path).load()
    assert settings.general.update_repo == DEFAULT_UPDATE_REPO


def test_roundtrip_persists(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    settings = AppSettings(general=GeneralSettings(theme="dark", default_mode="fixed"))
    store.save(settings)
    assert store.exists()
    loaded = store.load()
    assert loaded.general.theme == "dark"
    assert loaded.general.default_mode == "fixed"


def test_save_is_valid_json_and_no_temp_left(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    store.save(AppSettings())
    data = json.loads(store.path.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1"
    assert list(tmp_path.glob("*.tmp")) == []


def test_store_refuses_secret_values(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")
    settings = AppSettings()
    settings.providers.append(ProviderProfile(options={"api_key": "sk-should-not-persist"}))
    with pytest.raises(ValueError):
        store.save(settings)


def test_secret_guard_detects_nested_keys():
    with pytest.raises(ValueError):
        assert_no_secret_values({"a": [{"password": "x"}]})
    assert_no_secret_values({"a": [{"password": ""}]})
    assert_no_secret_values({"max_output_tokens": 128})


def test_load_recovers_from_invalid_json(tmp_path):
    # A corrupt settings file must not prevent the app from starting: the store
    # falls back to defaults and preserves the bad file for inspection.
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    settings = SettingsStore(path).load()
    assert settings.general.theme == "system"  # defaults
    assert (tmp_path / "settings.json.corrupt").exists()


def test_load_tolerates_utf8_bom(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"general": {"theme": "dark"}}', encoding="utf-8-sig")
    assert SettingsStore(path).load().general.theme == "dark"
