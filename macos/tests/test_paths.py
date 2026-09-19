from agentbetta.platform import paths


def test_appdata_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTBETTA_APPDATA", str(tmp_path / "roaming"))
    assert paths.app_data_root() == tmp_path / "roaming"
    assert paths.settings_path().name == "settings.json"


def test_localappdata_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTBETTA_LOCALAPPDATA", str(tmp_path / "local"))
    assert paths.local_app_data_root() == tmp_path / "local"
    assert paths.logs_dir() == tmp_path / "local" / "logs"
    assert paths.browser_profile_dir() == tmp_path / "local" / "browser" / "profile"


def test_documents_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTBETTA_DOCUMENTS", str(tmp_path / "docs"))
    assert paths.runs_dir() == tmp_path / "docs" / "runs"


def test_explicit_override_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENTBETTA_APPDATA", str(tmp_path / "roaming"))
    assert paths.app_data_root(tmp_path / "explicit") == tmp_path / "explicit"


def test_ensure_dir_creates(tmp_path):
    target = tmp_path / "a" / "b"
    assert paths.ensure_dir(target) == target
    assert target.is_dir()
