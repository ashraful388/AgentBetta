import json
from agentbetta.cli import main


def test_direct_cli(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["--provider", "fake", "--json", "Calculate 17 * 23"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["verified"] is True
    assert "391" in data["output"]


def test_run_task_file(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = tmp_path / "task.json"
    p.write_text(json.dumps({"task": "Explain AgentBetta"}))
    code = main(["run", str(p), "--provider", "fake", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["success"] is True
