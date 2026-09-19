from pathlib import Path
import pytest
from agentbetta.tools.workspace import Workspace, WorkspaceEscapeError

def test_workspace_blocks_parent_escape(tmp_path):
    ws=Workspace(tmp_path)
    with pytest.raises(WorkspaceEscapeError): ws.resolve("../secret.txt")

def test_workspace_allows_child(tmp_path):
    p=tmp_path/"a.txt"; p.write_text("ok")
    assert Workspace(tmp_path).resolve("a.txt") == p.resolve()
