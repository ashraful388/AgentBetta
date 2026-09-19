from agentbetta.settings import (
    InMemorySecretStore,
    KeyringSecretStore,
    create_secret_store,
    keyring_available,
    redact,
)


def test_in_memory_roundtrip():
    store = InMemorySecretStore()
    store.set_secret("provider:abc", "sk-123")
    assert store.get_secret("provider:abc") == "sk-123"
    store.set_secret("provider:abc", "sk-456")
    assert store.get_secret("provider:abc") == "sk-456"
    store.delete_secret("provider:abc")
    assert store.get_secret("provider:abc") is None
    store.delete_secret("provider:abc")


def test_redact_replaces_secret():
    assert redact("key=sk-secret end", ["sk-secret"]) == "key=***REDACTED*** end"


def test_create_secret_store_type():
    store = create_secret_store()
    assert isinstance(store, (InMemorySecretStore, KeyringSecretStore))


def test_keyring_available_is_bool():
    assert isinstance(keyring_available(), bool)
