import json
from pathlib import Path

import pytest

from agentbetta import AgentBetta, RuntimeConfig
from agentbetta.core.models import ProviderResponse
from agentbetta.memory import MemoryManager, MemoryStore
from agentbetta.memory.extract import extract_explicit
from agentbetta.permissions import profile_permission_set
from agentbetta.providers.base import BaseProvider
from agentbetta.providers.fake import FakeProvider
from agentbetta.tools import ToolContext
from agentbetta.tools.memory import recall, remember


def _manager(tmp_path, **kwargs):
    return MemoryManager(MemoryStore(tmp_path / "memory.jsonl"), **kwargs)


class _CaptureProvider(BaseProvider):
    name = "capture"
    is_cloud = False
    model = "stub"

    def __init__(self):
        self.last_messages = None

    def chat(self, request):
        self.last_messages = request.messages
        return ProviderResponse("done")


def test_store_persists_across_managers(tmp_path):
    mgr = _manager(tmp_path)
    mgr.add("User prefers dark mode", kind="preference")
    reloaded = _manager(tmp_path)
    assert reloaded.count() == 1


def test_add_dedupes_and_updates(tmp_path):
    mgr = _manager(tmp_path)
    first = mgr.add("User likes tea", importance=0.4)
    second = mgr.add("user likes tea", importance=0.9)
    assert first.id == second.id
    assert mgr.count() == 1
    assert second.importance == 0.9


def test_empty_memory_rejected(tmp_path):
    with pytest.raises(ValueError):
        _manager(tmp_path).add("   ")


def test_retrieval_ranks_relevance(tmp_path):
    mgr = _manager(tmp_path, auto_capture=False)
    mgr.add("User prefers dark mode", kind="preference", importance=0.6)
    mgr.add("The staging server is in Frankfurt", kind="fact")
    top = mgr.search("what theme preference does the user have", k=1)
    assert "dark mode" in top[0].text


def test_context_block_contains_memory(tmp_path):
    mgr = _manager(tmp_path, auto_capture=False)
    mgr.add("User's project is called AgentBetta")
    block = mgr.context_block("project name", k=1)
    assert "LONG-TERM MEMORY" in block and "AgentBetta" in block


def test_max_entries_prunes(tmp_path):
    mgr = _manager(tmp_path, max_entries=2)
    for i in range(5):
        mgr.add(f"memory number {i}", importance=0.1 * i)
    assert mgr.count() == 2


def test_forget_and_clear(tmp_path):
    mgr = _manager(tmp_path)
    entry = mgr.add("temporary note")
    assert mgr.forget(entry.id) is True
    assert mgr.count() == 0
    mgr.add("another")
    assert mgr.clear() == 1
    assert mgr.count() == 0


def test_runtime_injects_memory_into_context(tmp_path):
    mgr = _manager(tmp_path, auto_capture=False)
    mgr.add("The user's preferred editor is Neovim", kind="preference")
    provider = _CaptureProvider()
    agent = AgentBetta(
        provider,
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"), memory_items=3),
        memory=mgr,
    )
    agent.run("Which editor do I like?")
    user = [m for m in provider.last_messages if m["role"] == "user"][-1]["content"]
    assert "LONG-TERM MEMORY" in user
    assert "Neovim" in user


def test_auto_capture_on_verified_success(tmp_path):
    mgr = _manager(tmp_path, auto_capture=True)
    agent = AgentBetta(
        FakeProvider(),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"), memory_items=3),
        memory=mgr,
    )
    agent.run("remember that I prefer green tea in the afternoon")
    assert any("green tea" in entry.text for entry in mgr.all())


def test_privacy_mode_does_not_capture(tmp_path):
    mgr = _manager(tmp_path, auto_capture=True)
    agent = AgentBetta(
        FakeProvider(),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"), privacy_mode=True),
        memory=mgr,
    )
    agent.run("remember that my secret code is 1234")
    assert mgr.count() == 0


def test_extract_explicit_patterns():
    found = extract_explicit("Remember that I use Windows 11. I prefer concise answers.")
    texts = [text for text, _ in found]
    assert any("Windows 11" in t for t in texts)
    assert any("concise answers" in t for t in texts)


def test_memory_tools_with_permission(tmp_path):
    mgr = _manager(tmp_path)
    ctx = ToolContext(permissions=profile_permission_set("standard"), memory=mgr)
    remember(ctx=ctx, text="The user's dog is named Rex", kind="fact")
    results = recall(ctx=ctx, query="dog name", k=3)
    assert any("Rex" in item["text"] for item in results)


def test_memory_write_denied_in_safe_profile(tmp_path):
    mgr = _manager(tmp_path)
    ctx = ToolContext(permissions=profile_permission_set("safe"), memory=mgr)
    with pytest.raises(PermissionError):
        remember(ctx=ctx, text="should not be stored")


def test_memory_tools_require_enabled_memory(tmp_path):
    ctx = ToolContext(permissions=profile_permission_set("full"), memory=None)
    with pytest.raises(PermissionError):
        remember(ctx=ctx, text="x")
