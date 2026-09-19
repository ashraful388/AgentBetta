"""Hybrid retrieval scoring (keyword + optional embedding + recency/importance).

A dependency-free approximation of the multi-signal retrieval used by mem0:
semantic signal when embeddings exist, otherwise a BM25-like keyword score,
fused with recency, importance and usage.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone

from agentbetta.memory.models import MemoryEntry

_WORD = re.compile(r"[a-z0-9_]+")
_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "was", "were", "be", "been", "with", "without", "this", "that", "these",
    "those", "it", "its", "as", "at", "by", "from", "you", "your", "i", "we",
    "our", "my", "me", "please",
}


def normalize_text(text: str) -> str:
    return " ".join(_WORD.findall((text or "").lower()))


def tokens(text: str) -> set[str]:
    return {word for word in _WORD.findall((text or "").lower()) if len(word) > 2 and word not in _STOP}


def age_days(iso: str | None) -> float:
    if not iso:
        return 365.0
    try:
        moment = datetime.fromisoformat(iso)
    except ValueError:
        return 365.0
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - moment).total_seconds() / 86400.0)


def keyword_score(query_tokens: set[str], entry: MemoryEntry) -> float:
    entry_tokens = tokens(entry.text + " " + " ".join(entry.tags))
    if not query_tokens or not entry_tokens:
        return 0.0
    overlap = len(query_tokens & entry_tokens)
    return overlap / math.sqrt(len(query_tokens))


def cosine(a: list[float] | None, b: list[float] | None) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def score(entry: MemoryEntry, query_tokens: set[str], query_embedding: list[float] | None = None) -> float:
    keyword = keyword_score(query_tokens, entry)
    has_embedding = bool(query_embedding and entry.embedding)
    semantic = cosine(query_embedding, entry.embedding) if has_embedding else 0.0
    base = (0.55 * semantic + 0.25 * keyword) if has_embedding else (0.8 * keyword)
    recency = math.exp(-age_days(entry.updated_at or entry.created_at) / 45.0)
    importance = max(0.0, min(1.0, entry.importance))
    usage = min(1.0, math.log1p(entry.use_count) / 3.0)
    return base + 0.12 * recency + 0.15 * importance + 0.05 * usage
