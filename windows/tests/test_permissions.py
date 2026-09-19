import pytest
from agentbetta.core.models import PermissionSet

def test_ineligible_permission_cannot_be_added():
    p=PermissionSet(frozenset({"file_read"}), frozenset({"file_read"}))
    with pytest.raises(PermissionError): p.with_permission("file_write")

def test_eligible_permission_can_be_added():
    p=PermissionSet(frozenset({"file_read"}), frozenset({"file_read","file_write"}))
    assert p.with_permission("file_write").permits("file_write")
