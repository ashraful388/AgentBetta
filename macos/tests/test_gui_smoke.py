import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication  # noqa: E402

from agentbetta.desktop.services import AppServices  # noqa: E402
from agentbetta.providers import FakeProvider  # noqa: E402
from agentbetta.settings import InMemorySecretStore, SettingsStore  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _services(tmp_path) -> AppServices:
    from agentbetta.desktop.chats import ChatStore
    from agentbetta.desktop.projects import ProjectStore

    return AppServices(
        settings_store=SettingsStore(tmp_path / "settings.json"),
        secret_store=InMemorySecretStore(),
        runs_dir=tmp_path / "runs",
        chats_store=ChatStore(tmp_path / "chats.json"),
        projects_store=ProjectStore(tmp_path / "projects.json"),
    )


def test_auto_falls_back_to_fake_when_unconfigured(tmp_path):
    services = _services(tmp_path)
    assert isinstance(services.build_provider("auto"), FakeProvider)


def test_service_save_and_reload(tmp_path):
    services = _services(tmp_path)
    services.settings.general.theme = "dark"
    services.save()
    reloaded = SettingsStore(tmp_path / "settings.json").load()
    assert reloaded.general.theme == "dark"


def test_main_window_builds(qapp, tmp_path):
    from agentbetta.desktop.main_window import MainWindow

    window = MainWindow(_services(tmp_path))
    # Navigation grew in the GUI rebuild: Tasks, Projects, Agents, Memory,
    # History, Settings, About.
    assert window.nav.count() >= 6
    assert window.inspector is not None


def test_gui_run_offline_completes(qapp, tmp_path):
    from agentbetta.desktop.main_window import MainWindow

    window = MainWindow(_services(tmp_path))
    window.task_view.composer.setPlainText("Calculate 17 * 23")
    window.task_view.run_task()
    assert window.task_view.worker is not None
    window.task_view.worker.wait(30_000)
    for _ in range(20):
        qapp.processEvents()
    text = window.task_view.output.toPlainText()
    assert "391" in text
    window.chats_view.refresh()
    assert window.chats_view.table.rowCount() >= 1


def test_settings_view_renders_profiles(qapp, tmp_path):
    from agentbetta.desktop.views.settings_view import SettingsView

    view = SettingsView(_services(tmp_path))
    assert view.tabs.count() >= 8
    assert "hard denied" in view.permissions_view.toPlainText().lower()


def test_theme_light_and_dark_differ(qapp):
    from agentbetta.desktop.theme import apply_theme, current_tokens

    apply_theme(qapp, "light")
    light = current_tokens().bg
    apply_theme(qapp, "dark")
    dark = current_tokens().bg
    assert light != dark
    apply_theme(qapp, "system")


def test_all_navigation_views_build(qapp, tmp_path):
    from agentbetta.desktop.main_window import MainWindow

    window = MainWindow(_services(tmp_path))
    for row in range(window.nav.count()):
        window.nav.setCurrentRow(row)
        qapp.processEvents()
        assert window.stack.currentIndex() == row


def test_inspector_populates_from_summary(qapp):
    from agentbetta.desktop.widgets.inspector import InspectorPanel

    inspector = InspectorPanel()
    inspector.set_summary(
        {
            "run_id": "run_x",
            "verified": True,
            "attempts": 2,
            "provider": "ollama",
            "model_id": "qwen3:1.7b",
            "final_configuration": {
                "model_tier": 1,
                "context_chars": 8000,
                "tools": ["read_text_file_global"],
                "permissions": {"allowed": ["file_read"], "eligible": [], "hard_denied": ["shell_exec"]},
                "memory_items": 3,
                "token_budget": 2000,
                "max_seconds": 180,
                "max_turns": 3,
                "max_tool_calls": 3,
            },
            "verification": {"status": "PASS", "reason": "ok"},
            "adaptations": [],
            "tool_results": [],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20},
        }
    )
    assert inspector.verification_badge.text() == "PASS"
    assert inspector.status.text() == "VERIFIED"


def test_memory_view_reads_governed_store(qapp, tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTBETTA_LOCALAPPDATA", str(tmp_path))
    from agentbetta.desktop.views.memory_view import MemoryView

    services = _services(tmp_path)
    services.memory_add("The user prefers concise answers", kind="preference")
    view = MemoryView(services)
    view.refresh()
    assert view.table.rowCount() == 1
    assert view.tile_semantic.value_label.text() == "1"


def test_result_markdown_cancelled_and_provider_error():
    from agentbetta.desktop.widgets.report import build_result_markdown

    cancelled = build_result_markdown(
        {"cancelled": True, "verification": {"status": "ERROR", "evidence": {"cancelled": True}}}
    )
    assert "CANCELLED" in cancelled

    provider_error = build_result_markdown(
        {
            "verified": False,
            "verification": {
                "status": "FAIL",
                "reason": "Structured failure: provider_error",
                "evidence": {"provider_error": True},
            },
        }
    )
    assert "provider" in provider_error.lower()


def test_chat_store_roundtrip(tmp_path):
    from agentbetta.desktop.chats import ChatStore, Conversation

    store = ChatStore(tmp_path / "chats.json")
    conversation = Conversation(title="Budget", project="Finance")
    conversation.add("user", "read notes.txt")
    conversation.add("agent", "The budget is 42000")
    store.upsert(conversation)
    loaded = store.get(conversation.id)
    assert loaded is not None
    assert loaded.title == "Budget" and loaded.project == "Finance"
    assert len(loaded.messages) == 2
    assert store.for_project("Finance")[0].id == conversation.id
    store.remove(conversation.id)
    assert store.all() == []


def test_task_view_uses_single_run_stop_button(qapp, tmp_path):
    from agentbetta.desktop.main_window import MainWindow

    window = MainWindow(_services(tmp_path))
    assert window.task_view.run_button.text() == "Run"
    assert not hasattr(window.task_view, "stop_button")
    assert window.nav.count() >= 8


def test_followup_detection_needs_prior_output():
    from agentbetta.desktop.views.task_view import _is_followup

    assert _is_followup("now run it", True)
    assert not _is_followup("now run it", False)
    assert not _is_followup("", True)
    assert _is_followup("Calculate 17 * 23", True)
    long_standalone = "Write a comprehensive report on renewable energy. " * 20
    assert not _is_followup(long_standalone, True)
    assert _is_followup(long_standalone + " Update it to include solar.", True)


def test_project_store_roundtrip(tmp_path):
    from agentbetta.desktop.projects import Project, ProjectStore

    store = ProjectStore(tmp_path / "projects.json")
    project = store.add(Project(name="Alpha", folder=str(tmp_path)))
    store.update(project)
    reloaded = store.load()
    assert len(reloaded) == 1
    assert reloaded[0].name == "Alpha"
    store.remove(project.id)
    assert store.load() == []
