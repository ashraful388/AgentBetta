from __future__ import annotations
from pathlib import Path

class WorkspaceEscapeError(PermissionError): pass

class Workspace:
    def __init__(self, root: str | Path):
        self.root=Path(root).expanduser().resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"Workspace does not exist: {self.root}")
    def resolve(self, relative: str | Path) -> Path:
        candidate=(self.root / relative).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as e:
            raise WorkspaceEscapeError(f"Path escapes approved workspace: {relative}") from e
        return candidate
