import pytest

from agentbetta.core.models import PermissionSet
from agentbetta.permissions import (
    get_profile,
    inspect_profiles,
    profile_permission_set,
)
from agentbetta.permissions.policy import FILE_DELETE, FILE_READ, FILE_WRITE, DESKTOP_CONTROL


def test_safe_profile_is_read_only():
    perms = profile_permission_set("safe")
    assert perms.permits(FILE_READ)
    assert not perms.permits(FILE_WRITE)
    assert not perms.is_eligible(FILE_WRITE)
    assert not perms.is_eligible(FILE_DELETE)


def test_extended_has_desktop_control_eligible_but_hard_denied():
    perms = profile_permission_set("extended")
    assert DESKTOP_CONTROL in perms.eligible
    assert DESKTOP_CONTROL in perms.hard_denied
    with pytest.raises(PermissionError):
        perms.with_permission(DESKTOP_CONTROL)


def test_full_computer_allows_all():
    perms = profile_permission_set("full")
    assert perms.permits(FILE_DELETE)
    assert perms.permits(DESKTOP_CONTROL)
    assert perms.hard_denied == frozenset()


def test_hard_denied_cannot_be_activated_even_if_eligible():
    perms = PermissionSet(
        allowed=frozenset({FILE_READ}),
        eligible=frozenset({FILE_READ, FILE_DELETE}),
        hard_denied=frozenset({FILE_DELETE}),
    )
    with pytest.raises(PermissionError):
        perms.with_permission(FILE_DELETE)


def test_inspect_profiles_shape():
    data = inspect_profiles()
    assert set(data) == {"safe", "standard", "extended", "full"}
    assert "allowed" in data["safe"]
    assert get_profile("does-not-exist").key == "safe"
