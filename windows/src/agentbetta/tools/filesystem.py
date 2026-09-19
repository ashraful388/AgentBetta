"""Global filesystem tools (absolute paths, no workspace boundary).

Every operation is permission-checked and canonicalized. UNC/network paths
require the separate ``network_share`` permission.
"""

from __future__ import annotations

from typing import Any

from agentbetta.permissions import policy
from agentbetta.platform import filesystem as fs
from agentbetta.tools.guards import requires
from agentbetta.tools.registry import ToolContext


def _resolve(ctx: ToolContext, raw: str) -> Any:
    path = fs.canonical_path(raw)
    if fs.is_network_path(path) and not ctx.permissions.permits(policy.NETWORK_SHARE):
        raise PermissionError("network_share permission is required for UNC/network paths")
    return path


def _approve_overwrite(ctx: ToolContext, path: Any) -> None:
    if not path.exists():
        return
    if ctx.approvals is None:
        raise PermissionError("approval_required: overwriting an existing file needs approval")
    approved = ctx.approvals.request_tool(
        tool_name="write_text_file_global",
        arguments={"path": str(path)},
        permission=policy.FILE_WRITE,
        risk="high",
        reason=f"Overwrite existing file: {path}",
    )
    if not approved:
        raise PermissionError("approval_denied: overwrite not approved")


@requires(policy.FILE_READ)
def list_drives(*, ctx: ToolContext) -> list[dict[str, object]]:
    return fs.list_drives()


@requires(policy.FILE_READ)
def list_directory_global(*, ctx: ToolContext, path: str, max_entries: int = 500) -> list[dict[str, Any]]:
    target = _resolve(ctx, path)
    if not target.is_dir():
        raise NotADirectoryError(f"Not a directory: {target}")
    entries: list[dict[str, Any]] = []
    for child in sorted(target.iterdir(), key=lambda c: c.name.lower()):
        if len(entries) >= max_entries:
            break
        try:
            stat = child.stat()
            entries.append(
                {
                    "name": child.name,
                    "type": "dir" if child.is_dir() else "file",
                    "size": None if child.is_dir() else stat.st_size,
                    "modified": stat.st_mtime,
                }
            )
        except OSError:
            entries.append({"name": child.name, "type": "unknown", "size": None, "modified": None})
    return entries


@requires(policy.FILE_READ)
def file_stat(*, ctx: ToolContext, path: str) -> dict[str, Any]:
    target = _resolve(ctx, path)
    stat = target.stat()
    return {
        "path": str(target),
        "exists": True,
        "is_dir": target.is_dir(),
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "created": stat.st_ctime,
        "suffix": target.suffix,
    }


@requires(policy.FILE_READ)
def read_text_file_global(*, ctx: ToolContext, path: str, max_chars: int = 100_000) -> str:
    target = _resolve(ctx, path)
    if target.is_dir():
        raise IsADirectoryError(f"Is a directory: {target}")
    return target.read_text(encoding="utf-8", errors="replace")[:max_chars]


@requires(policy.FILE_READ)
def search_files(*, ctx: ToolContext, root: str, pattern: str, max_results: int = 200,
                 recursive: bool = True) -> list[str]:
    target = _resolve(ctx, root)
    return fs.search_files(target, pattern, max_results=max_results, recursive=recursive)


@requires(policy.FILE_READ)
def grep_files(*, ctx: ToolContext, root: str, query: str, max_results: int = 100) -> list[dict[str, object]]:
    target = _resolve(ctx, root)
    return fs.grep_files(target, query, max_results=max_results)


@requires(policy.FILE_READ)
def file_hash(*, ctx: ToolContext, path: str, algorithm: str = "sha256") -> dict[str, str]:
    target = _resolve(ctx, path)
    return {"path": str(target), "algorithm": algorithm, "hash": fs.file_hash(target, algorithm)}


@requires(policy.FILE_WRITE)
def create_directory(*, ctx: ToolContext, path: str) -> dict[str, Any]:
    target = _resolve(ctx, path)
    target.mkdir(parents=True, exist_ok=True)
    return {"path": str(target), "created": True}


@requires(policy.FILE_WRITE)
def write_text_file_global(*, ctx: ToolContext, path: str, content: str,
                           overwrite: bool = True) -> dict[str, Any]:
    target = _resolve(ctx, path)
    if target.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {target}")
    if target.exists():
        _approve_overwrite(ctx, target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target), "chars": len(content), "overwritten": True}


@requires(policy.FILE_WRITE)
def append_text_file(*, ctx: ToolContext, path: str, content: str) -> dict[str, Any]:
    target = _resolve(ctx, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(content)
    return {"path": str(target), "appended": len(content)}


@requires(policy.FILE_WRITE)
def copy_path(*, ctx: ToolContext, source: str, destination: str) -> dict[str, Any]:
    src = _resolve(ctx, source)
    dst = _resolve(ctx, destination)
    if src.is_dir():
        import shutil

        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        import shutil

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return {"source": str(src), "destination": str(dst)}


@requires(policy.FILE_WRITE)
def move_path(*, ctx: ToolContext, source: str, destination: str) -> dict[str, Any]:
    src = _resolve(ctx, source)
    dst = _resolve(ctx, destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    import shutil

    shutil.move(str(src), str(dst))
    return {"source": str(src), "destination": str(dst)}


@requires(policy.FILE_DELETE)
def delete_path(*, ctx: ToolContext, path: str, recursive: bool = False) -> dict[str, Any]:
    target = _resolve(ctx, path)
    if not target.exists():
        raise FileNotFoundError(f"Path does not exist: {target}")
    if target.is_dir():
        import shutil

        if recursive:
            shutil.rmtree(target)
        else:
            target.rmdir()
    else:
        target.unlink()
    return {"path": str(target), "deleted": True, "recursive": recursive}


__all__ = [
    "append_text_file",
    "copy_path",
    "create_directory",
    "delete_path",
    "file_hash",
    "file_stat",
    "grep_files",
    "list_directory_global",
    "list_drives",
    "move_path",
    "read_text_file_global",
    "search_files",
    "write_text_file_global",
]
