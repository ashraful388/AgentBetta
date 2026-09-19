"""Secret storage abstraction.

Secrets are never written to settings files, logs, run records, or diagnostic
bundles. On Windows the default backend is the Windows Credential Manager via
the ``keyring`` package.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

SERVICE_NAME = "AgentBetta"


@runtime_checkable
class SecretStore(Protocol):
    is_persistent: bool

    def set_secret(self, name: str, value: str) -> None: ...

    def get_secret(self, name: str) -> str | None: ...

    def delete_secret(self, name: str) -> None: ...


class InMemorySecretStore:
    """Session-only store used by tests and as a safe fallback."""

    is_persistent = False

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def set_secret(self, name: str, value: str) -> None:
        self._data[name] = value

    def get_secret(self, name: str) -> str | None:
        return self._data.get(name)

    def delete_secret(self, name: str) -> None:
        self._data.pop(name, None)


class KeyringSecretStore:
    """Windows Credential Manager (or the platform keyring) backed store."""

    is_persistent = True

    def __init__(self, service: str = SERVICE_NAME) -> None:
        import keyring  # imported lazily so the core remains import-light

        self._keyring = keyring
        self._service = service

    @property
    def backend_name(self) -> str:
        try:
            return self._keyring.get_keyring().__class__.__name__
        except Exception:  # pragma: no cover - environment dependent
            return "unknown"

    def set_secret(self, name: str, value: str) -> None:
        self._keyring.set_password(self._service, name, value)

    def get_secret(self, name: str) -> str | None:
        return self._keyring.get_password(self._service, name)

    def delete_secret(self, name: str) -> None:
        try:
            self._keyring.delete_password(self._service, name)
        except Exception:
            # Deleting a missing credential is not an error for the caller.
            pass


def keyring_available() -> bool:
    try:
        import keyring

        backend = keyring.get_keyring()
        name = backend.__class__.__name__.lower()
        # keyring's fail backend is named "failkeyring" / "Keyring" with no
        # priority; treat it as unavailable.
        return "fail" not in name
    except Exception:
        return False


def create_secret_store() -> SecretStore:
    """Return the best available secret store.

    Falls back to a session-only in-memory store when no OS keyring backend is
    available; it never falls back to plaintext persistence.
    """

    if keyring_available():
        return KeyringSecretStore()
    return InMemorySecretStore()


def redact(text: str, secrets: list[str] | None = None) -> str:
    """Best-effort redaction helper for logs and error messages."""

    if not text:
        return text
    out = text
    for secret in secrets or []:
        if secret:
            out = out.replace(secret, "***REDACTED***")
    return out
