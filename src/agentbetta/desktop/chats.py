"""Persistent chat conversations.

A conversation is a titled transcript (user / agent / status messages) that can
be associated with an optional project. Stored as plain JSON with no secrets.
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
class ChatMessage:
    role: str  # user | agent | status
    text: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    at: str = field(default_factory=_now)
    rating: int | None = None  # 1 like, -1 dislike, 0 none

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatMessage":
        names = set(cls.__dataclass_fields__)
        return cls(**{k: v for k, v in (data or {}).items() if k in names})


@dataclass
class Conversation:
    title: str = "New chat"
    project: str = ""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    run_id: str | None = None
    verified: bool | None = None
    messages: list[ChatMessage] = field(default_factory=list)

    def add(self, role: str, text: str) -> ChatMessage:
        message = ChatMessage(role=role, text=text)
        self.messages.append(message)
        self.updated_at = _now()
        return message

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["messages"] = [m.to_dict() for m in self.messages]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Conversation":
        names = set(cls.__dataclass_fields__)
        payload = {k: v for k, v in (data or {}).items() if k in names and k != "messages"}
        conversation = cls(**payload)
        conversation.messages = [ChatMessage.from_dict(m) for m in (data.get("messages") or [])]
        return conversation

    @property
    def preview(self) -> str:
        for message in self.messages:
            if message.role == "user":
                return message.text.strip().replace("\n", " ")[:120]
        return self.title


class ChatStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> list[Conversation]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return [Conversation.from_dict(item) for item in (data.get("conversations") or [])]

    def save(self, conversations: list[Conversation]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"conversations": [c.to_dict() for c in conversations]}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def upsert(self, conversation: Conversation) -> Conversation:
        conversations = [c for c in self.load() if c.id != conversation.id]
        conversations.append(conversation)
        self.save(conversations)
        return conversation

    def get(self, conversation_id: str) -> Conversation | None:
        return next((c for c in self.load() if c.id == conversation_id), None)

    def remove(self, conversation_id: str) -> None:
        self.save([c for c in self.load() if c.id != conversation_id])

    def all(self) -> list[Conversation]:
        return sorted(self.load(), key=lambda c: c.updated_at, reverse=True)

    def for_project(self, project: str) -> list[Conversation]:
        return [c for c in self.all() if c.project == project]

    def clear(self) -> int:
        count = len(self.load())
        self.save([])
        return count


__all__ = ["ChatMessage", "ChatStore", "Conversation"]
