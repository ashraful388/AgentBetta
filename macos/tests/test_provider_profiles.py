from agentbetta.settings import ProviderProfile, preset, profile_from_preset


def test_profile_roundtrip_has_no_secret_field():
    profile = ProviderProfile(name="OpenAI", base_url="https://api.openai.com/v1", is_cloud=True)
    data = profile.to_dict()
    assert "api_key" not in data
    assert "secret" not in {k.lower() for k in data}


def test_api_key_ref_is_a_reference_only():
    profile = ProviderProfile(api_key_ref="provider:xyz")
    assert profile.secret_ref() == "provider:xyz"
    assert "sk-" not in str(profile.to_dict())


def test_from_dict_ignores_unknown_fields():
    profile = ProviderProfile.from_dict({"name": "P", "unknown": 1, "api_key": "sk-leak"})
    assert profile.name == "P"
    assert "api_key" not in profile.to_dict()


def test_preset_lookup_and_creation():
    assert preset("ollama").is_cloud is False
    profile = profile_from_preset("ollama")
    assert profile.type == "ollama"
    assert profile.is_cloud is False
    assert profile.base_url == "http://127.0.0.1:11434"


def test_unknown_preset_raises():
    import pytest

    with pytest.raises(KeyError):
        profile_from_preset("does-not-exist")
