import os
import threading

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


def test_update_available_highlights_header(qapp, tmp_path):
    from agentbetta.desktop.main_window import MainWindow
    from agentbetta.updates import UpdateInfo

    services = _services(tmp_path)
    services.settings.general.auto_check_updates = False
    window = MainWindow(services)
    info = UpdateInfo(version="9.9.9", tag="v9.9.9")
    window._on_update_checked(info, silent=True)
    assert window.update_button.text() == "Update 9.9.9"
    assert window.update_button.objectName() == "Primary"
    assert window._pending_update is info


def test_first_update_click_opens_available_release(qapp, tmp_path, monkeypatch):
    from agentbetta.desktop.main_window import MainWindow
    from agentbetta.updates import UpdateInfo

    services = _services(tmp_path)
    services.settings.general.auto_check_updates = False
    window = MainWindow(services)
    info = UpdateInfo(version="9.9.9", tag="v9.9.9")
    shown = []

    def check(**kwargs):
        window._on_update_checked(info, silent=kwargs["silent"])

    monkeypatch.setattr(window, "_check_updates", check)
    monkeypatch.setattr(window, "_show_update_dialog", shown.append)
    window._open_update_dialog()
    assert shown == [info]


def test_pending_update_is_rechecked_after_source_change(qapp, tmp_path, monkeypatch):
    from agentbetta.desktop.main_window import MainWindow
    from agentbetta.updates import UpdateInfo

    services = _services(tmp_path)
    services.settings.general.auto_check_updates = False
    window = MainWindow(services)
    window._on_update_checked(UpdateInfo(version="9.9.9", tag="v9.9.9"), silent=True)
    services.settings.general.update_repo = "other/AgentBetta"
    checks = []
    monkeypatch.setattr(window, "_check_updates", lambda **kwargs: checks.append(kwargs))
    window._open_update_dialog()
    assert window._pending_update is None
    assert window._open_dialog_after_check is True
    assert checks == [{"silent": False}]


def test_stale_in_flight_result_is_discarded(qapp, tmp_path, monkeypatch):
    from agentbetta.desktop.main_window import MainWindow
    from agentbetta.updates import UpdateInfo

    services = _services(tmp_path)
    services.settings.general.auto_check_updates = False
    window = MainWindow(services)
    window._open_dialog_after_check = True
    checks = []
    monkeypatch.setattr(window, "_check_updates", lambda **kwargs: checks.append(kwargs))
    window._on_update_checked(
        UpdateInfo(version="9.9.9", tag="v9.9.9"),
        silent=False,
        context=("old/AgentBetta", "stable"),
    )
    assert window._pending_update is None
    assert window.update_button.text() == "Updates"
    assert checks == [{"silent": False}]


def test_overlapping_settings_and_header_checks_share_result(qapp, tmp_path, monkeypatch):
    from agentbetta.desktop.main_window import MainWindow
    from agentbetta.updates import UpdateInfo

    services = _services(tmp_path)
    services.settings.general.auto_check_updates = False
    window = MainWindow(services)
    started = threading.Event()
    release = threading.Event()
    calls = []
    shown = []
    info = UpdateInfo(version="9.9.9", tag="v9.9.9")

    def check_for_updates(repo, channel):
        calls.append((repo, channel))
        started.set()
        assert release.wait(5000)
        return info

    monkeypatch.setattr(services, "check_for_updates", check_for_updates)
    monkeypatch.setattr(window, "_show_update_dialog", shown.append)
    window.settings_view.check_updates_now()
    assert started.wait(2000)
    worker = window._update_worker
    window._open_update_dialog()
    assert window._update_worker is worker
    release.set()
    assert worker.wait(5000)
    for _ in range(20):
        qapp.processEvents()
    assert calls == [("ashraful388/AgentBetta", "prerelease")]
    assert shown == [info]
    assert window._open_dialog_after_check is False
    assert window._settings_update_check_pending is False
    assert window.settings_view.update_check_button.isEnabled()


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


def test_settings_update_check_saves_current_fields(qapp, tmp_path):
    from agentbetta.desktop.views.settings_view import SettingsView

    services = _services(tmp_path)
    view = SettingsView(services)
    requested = []
    view.updateCheckRequested.connect(lambda: requested.append(True))
    view.update_repo_edit.setText("example/AgentBetta")
    view.update_channel_combo.setCurrentIndex(view.update_channel_combo.findData("prerelease"))
    view.check_updates_now()
    assert requested == [True]
    assert not view.update_check_button.isEnabled()
    assert services.settings_store.load().general.update_repo == "example/AgentBetta"
    view.finish_update_check(None)
    assert view.update_check_button.isEnabled()


def test_source_update_dialog_has_download_action(qapp, monkeypatch):
    from agentbetta.desktop.widgets import update_dialog
    from agentbetta.updates import ReleaseAsset, UpdateInfo

    info = UpdateInfo(
        version="9.9.9",
        tag="v9.9.9",
        page_url="https://github.com/ashraful388/AgentBetta/releases/tag/v9.9.9",
        assets=[ReleaseAsset("AgentBetta-Setup.exe", "https://example.invalid/setup.exe")],
    )
    monkeypatch.setattr(update_dialog, "can_self_update", lambda: False)
    monkeypatch.setattr(update_dialog, "select_asset", lambda value: value.assets[0])
    dialog = update_dialog.UpdateDialog(object(), info)
    assert dialog.update_button.isEnabled()
    assert dialog.update_button.text() == "Download & install"


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
