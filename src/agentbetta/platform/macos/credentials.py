"""macOS credential backend helpers.

Thin macOS-facing wrapper over :mod:`agentbetta.settings.secrets`. The core
never stores secrets in files; ``keyring`` uses the macOS Keychain.
"""

from __future__ import annotations

from agentbetta.settings.secrets import (
    SERVICE_NAME,
    KeyringSecretStore,
    SecretStore,
    create_secret_store,
    keyring_available,
)


def is_available() -> bool:
    return keyring_available()


def backend_name() -> str:
    if keyring_available():
        return KeyringSecretStore().backend_name
    return "unavailable"


def create_store() -> SecretStore:
    return create_secret_store()


__all__ = [
    "SERVICE_NAME",
    "backend_name",
    "create_store",
    "is_available",
]
