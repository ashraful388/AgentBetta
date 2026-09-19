"""Global long-term memory for AgentBetta.

A lightweight, dependency-free memory layer (store + hybrid retrieval +
explicit and automatic capture) in the spirit of mem0 and LangMem. Scope is
global and user-owned; there is a viewer/clear control in Settings.
"""

from __future__ import annotations

from agentbetta.memory.embeddings import OllamaEmbedder
from agentbetta.memory.extract import capture_from_run, extract_explicit
from agentbetta.memory.manager import MemoryManager, default_memory_path
from agentbetta.memory.models import MEMORY_KINDS, MemoryEntry
from agentbetta.memory.store import MemoryStore

__all__ = [
    "MEMORY_KINDS",
    "MemoryEntry",
    "MemoryManager",
    "MemoryStore",
    "OllamaEmbedder",
    "capture_from_run",
    "default_memory_path",
    "extract_explicit",
]
