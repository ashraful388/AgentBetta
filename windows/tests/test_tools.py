import pytest
from agentbetta.core.models import PermissionSet
from agentbetta.tools import Workspace, default_registry

def test_write_denied_without_permission(tmp_path):
    ws=Workspace(tmp_path); tools=default_registry()
    with pytest.raises(PermissionError):
        tools.execute("write_text_file", {"path":"x.txt","content":"x"}, workspace=ws,
                      permissions=PermissionSet())

def test_write_allowed(tmp_path):
    ws=Workspace(tmp_path); tools=default_registry()
    p=PermissionSet(frozenset({"file_read","file_write"}),frozenset({"file_read","file_write"}))
    tools.execute("write_text_file", {"path":"x.txt","content":"ok"}, workspace=ws, permissions=p)
    assert (tmp_path/"x.txt").read_text() == "ok"
