import hashlib
import sys
from pathlib import Path

import pytest

from agentbetta.core.models import PermissionSet
from agentbetta.permissions import ApprovalDecision, ApprovalService, profile_permission_set
from agentbetta.platform import filesystem as pfs
from agentbetta.platform import paths as ppaths
from agentbetta.tools import ToolContext
from agentbetta.tools import filesystem as fst

IS_MAC = sys.platform == "darwin"
DEVICE_PATH = "/dev/disk0" if IS_MAC else "\\\\.\\PhysicalDrive0"
NETWORK_PATH = "//server/share/file.txt" if IS_MAC else "\\\\server\\share\\file.txt"
LOCAL_PATH = "/tmp/file.txt" if IS_MAC else "C:\\temp\\file.txt"


def _ctx(profile: str = "full", approvals=None) -> ToolContext:
    return ToolContext(permissions=profile_permission_set(profile), approvals=approvals)


def test_canonical_path_blocks_device_namespace():
    with pytest.raises(pfs.UnsafePathError):
        pfs.canonical_path(DEVICE_PATH)
    if not IS_MAC:
        with pytest.raises(pfs.UnsafePathError):
            pfs.canonical_path("\\\\?\\C:\\secret")


def test_network_path_detection():
    assert pfs.is_network_path(NETWORK_PATH)
    assert not pfs.is_network_path(LOCAL_PATH)


def test_known_folders_reported():
    folders = ppaths.known_folders()
    assert "desktop" in folders and "documents" in folders and "downloads" in folders
    assert folders["user_profile"]


def test_folder_alias_resolves_to_real_desktop():
    resolved = pfs.canonical_path("desktop/agentbetta_alias_test.txt")
    assert resolved.name == "agentbetta_alias_test.txt"
    assert str(resolved.parent).lower() == str(Path(ppaths.known_folders()["desktop"])).lower()


def test_runtime_exposes_system_paths_for_file_tasks():
    from agentbetta import AgentBetta
    from agentbetta.core.characterize import characterize
    from agentbetta.core.models import Task
    from agentbetta.policy.engine import initial_configuration
    from agentbetta.providers.fake import FakeProvider

    agent = AgentBetta(FakeProvider())
    config = initial_configuration(
        characterize(Task("write a file to my desktop")),
        profile_permission_set("full"),
        has_workspace=False,
    )
    block = agent._system_paths(config)
    assert "Desktop" in block and "never guess the user name" in block


def test_unc_path_requires_network_share(tmp_path):
    perms = PermissionSet(allowed=frozenset({"file_read"}), eligible=frozenset({"file_read"}))
    ctx = ToolContext(permissions=perms)
    with pytest.raises(PermissionError):
        fst.read_text_file_global(ctx=ctx, path=NETWORK_PATH)


def test_read_and_write_outside_workspace(tmp_path):
    target = tmp_path / "outside.txt"
    ctx = _ctx("full")
    fst.write_text_file_global(ctx=ctx, path=str(target), content="hello")
    assert target.read_text(encoding="utf-8") == "hello"
    assert fst.read_text_file_global(ctx=ctx, path=str(target)) == "hello"
    stat = fst.file_stat(ctx=ctx, path=str(target))
    assert stat["size"] == 5


def test_read_denied_without_permission(tmp_path):
    target = tmp_path / "x.txt"
    target.write_text("secret", encoding="utf-8")
    ctx = ToolContext(permissions=PermissionSet(allowed=frozenset(), eligible=frozenset()))
    with pytest.raises(PermissionError):
        fst.read_text_file_global(ctx=ctx, path=str(target))


def test_write_file_denied_by_workspace_registry(tmp_path):
    from agentbetta.tools.registry import default_registry

    ctx = ToolContext(permissions=PermissionSet(allowed=frozenset({"file_read"}), eligible=frozenset({"file_read"})))
    with pytest.raises(PermissionError):
        default_registry().execute_ctx("write_text_file", {"path": "x.txt", "content": "y"}, ctx)


def test_delete_requires_permission(tmp_path):
    target = tmp_path / "gone.txt"
    target.write_text("x", encoding="utf-8")
    ctx = ToolContext(permissions=PermissionSet(allowed=frozenset({"file_read"}), eligible=frozenset({"file_read"})))
    with pytest.raises(PermissionError):
        fst.delete_path(ctx=ctx, path=str(target))
    assert target.exists()


def test_recursive_delete(tmp_path):
    folder = tmp_path / "tree"
    (folder / "sub").mkdir(parents=True)
    (folder / "sub" / "a.txt").write_text("a", encoding="utf-8")
    fst.delete_path(ctx=_ctx("full"), path=str(folder), recursive=True)
    assert not folder.exists()


def test_search_and_hash(tmp_path):
    (tmp_path / "a.txt").write_text("needle", encoding="utf-8")
    (tmp_path / "b.log").write_text("other", encoding="utf-8")
    found = fst.search_files(ctx=_ctx("full"), root=str(tmp_path), pattern="*.txt")
    assert any(p.endswith("a.txt") for p in found)
    hits = fst.grep_files(ctx=_ctx("full"), root=str(tmp_path), query="needle")
    assert hits and hits[0]["line"] == 1
    result = fst.file_hash(ctx=_ctx("full"), path=str(tmp_path / "a.txt"))
    assert result["hash"] == hashlib.sha256(b"needle").hexdigest()


def test_overwrite_requires_approval(tmp_path):
    target = tmp_path / "exists.txt"
    target.write_text("old", encoding="utf-8")
    with pytest.raises(PermissionError):
        fst.write_text_file_global(ctx=_ctx("full"), path=str(target), content="new")
    assert target.read_text(encoding="utf-8") == "old"


def test_overwrite_allowed_with_approval(tmp_path):
    target = tmp_path / "exists.txt"
    target.write_text("old", encoding="utf-8")
    approvals = ApprovalService(callback=lambda req: ApprovalDecision.ALLOW_ONCE)
    ctx = _ctx("full", approvals=approvals)
    fst.write_text_file_global(ctx=ctx, path=str(target), content="new")
    assert target.read_text(encoding="utf-8") == "new"


def test_copy_and_move(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("data", encoding="utf-8")
    ctx = _ctx("full")
    fst.copy_path(ctx=ctx, source=str(src), destination=str(tmp_path / "copy.txt"))
    assert (tmp_path / "copy.txt").read_text(encoding="utf-8") == "data"
    fst.move_path(ctx=ctx, source=str(tmp_path / "copy.txt"), destination=str(tmp_path / "moved.txt"))
    assert (tmp_path / "moved.txt").exists()
    assert not (tmp_path / "copy.txt").exists()
