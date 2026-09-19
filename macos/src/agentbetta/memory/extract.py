"""Automatic memory capture from completed runs.

Two sources (both opt-in via ``MemoryManager.auto_capture``):
- explicit user statements ("remember that ...", "I prefer ...", "my name is ...")
- a compact episodic summary of a verified task outcome.

No model call is used, so capture is deterministic, offline and auditable.
When the model already used the ``remember`` tool, explicit extraction is
skipped to avoid duplicates.
"""

from __future__ import annotations

import re
from typing import Any

from agentbetta.memory.manager import MemoryManager

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"remember that (.+)", re.IGNORECASE), "fact"),
    (re.compile(r"\bi prefer (.+)", re.IGNORECASE), "preference"),
    (re.compile(r"\bmy preferred (.+)", re.IGNORECASE), "preference"),
    (re.compile(r"\bmy (?:name|email|timezone|location|role) is (.+)", re.IGNORECASE), "fact"),
]

_CLAUSE_SPLIT = re.compile(r"\s+and\s+|\.\s+|;\s*")


def _clauses(text: str) -> list[str]:
    parts = _CLAUSE_SPLIT.split(text or "")
    cleaned: list[str] = []
    for part in parts:
        part = re.sub(r"^(?:that|to)\s+", "", part.strip(), flags=re.IGNORECASE)
        part = part.strip().strip(".").strip()
        if len(part) >= 2:
            cleaned.append(part[:300])
    return cleaned


def extract_explicit(text: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for pattern, kind in _PATTERNS:
        for match in pattern.finditer(text or ""):
            for clause in _clauses(match.group(1)):
                key = clause.lower()
                if key in seen:
                    continue
                seen.add(key)
                found.append((clause, kind))
    return found


def capture_from_run(manager: MemoryManager | None, *, task: Any, output: str,
                     run_id: str, features: Any | None = None,
                     already_remembered: bool = False,
                     max_result_chars: int = 400) -> list[str]:
    if manager is None or not manager.auto_capture:
        return []
    captured: list[str] = []
    objective = (getattr(task, "objective", "") or "").strip()
    result = (output or "").strip()

    if not already_remembered:
        for fragment, kind in extract_explicit(objective):
            manager.add(fragment, kind=kind, importance=0.7, source="auto", source_run_id=run_id)
            captured.append(fragment)

    memory_task = bool(getattr(features, "needs_memory", False)) if features is not None else False
    if not memory_task and not already_remembered and len(objective) >= 15 and result:
        summary = f"Completed task: {objective[:160]}. Result: {result[:max_result_chars]}"
        manager.add(summary, kind="episode", importance=0.3, source="auto", source_run_id=run_id)
        captured.append(summary)
    return captured


__all__ = ["capture_from_run", "extract_explicit"]
