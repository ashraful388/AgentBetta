"""Lightweight project store for the desktop client.

A project is optional task context (a name plus a folder). It is deliberately
*not* a filesystem security boundary: the permission profile still governs all
access. Stored as plain JSON with no secrets.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Project:
    name: str
    folder: str = ""
    profile: str = ""
    model: str = ""
    notes: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(default_factory=_now)
    last_used_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        names = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in (data or {}).items() if k in names})


class ProjectStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> list[Project]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return [Project.from_dict(item) for item in (data.get("projects") or [])]

    def save(self, projects: list[Project]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"projects": [p.to_dict() for p in projects]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add(self, project: Project) -> Project:
        projects = self.load()
        projects.append(project)
        self.save(projects)
        return project

    def update(self, project: Project) -> None:
        projects = [project if p.id == project.id else p for p in self.load()]
        self.save(projects)

    def remove(self, project_id: str) -> None:
        self.save([p for p in self.load() if p.id != project_id])

    def touch(self, project_id: str) -> None:
        projects = self.load()
        for project in projects:
            if project.id == project_id:
                project.last_used_at = _now()
        self.save(projects)


__all__ = ["Project", "ProjectStore"]
