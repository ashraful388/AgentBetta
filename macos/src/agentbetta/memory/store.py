"""JSONL-backed global memory store with atomic rewrites."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from agentbetta.memory.models import MemoryEntry


class MemoryStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> list[MemoryEntry]:
        if not self.path.exists():
            return []
        entries: list[MemoryEntry] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(MemoryEntry.from_dict(json.loads(line)))
            except (json.JSONDecodeError, TypeError):
                continue
        return entries

    def save_all(self, entries: list[MemoryEntry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=self.path.name + ".", suffix=".tmp", dir=str(self.path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                for entry in entries:
                    handle.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    def append(self, entry: MemoryEntry) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
