"""Global long-term memory data model.

Inspired by established memory layers (mem0, LangMem): memories are typed
facts/preferences/episodes with provenance, importance and usage metadata.
The store is a single global namespace owned by the user.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

MEMORY_KINDS = ("fact", "preference", "episode", "summary")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryEntry:
    text: str
    kind: str = "fact"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    source: str = "explicit"  # explicit | auto | tool | import
    source_run_id: str | None = None
    use_count: int = 0
    last_used_at: str | None = None
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        names = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in (data or {}).items() if k in names})
