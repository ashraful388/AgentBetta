import json
from pathlib import Path
from agentbetta import AgentBetta, RuntimeConfig
from agentbetta.providers.fake import FakeProvider

def test_offline_e2e_and_record(tmp_path):
    agent=AgentBetta(FakeProvider(), runtime_config=RuntimeConfig(run_dir=str(tmp_path/"runs"),research_mode=True))
    r=agent.run("Explain AgentBetta")
    assert r.success and r.verified and r.output
    assert r.record_path and Path(r.record_path).exists()
    data=json.loads(Path(r.record_path).read_text())
    assert data["provider"] == "fake" and data["success"] is True
    assert isinstance(data["contraction_candidates"], list)

def test_calculation_fake_provider(tmp_path):
    r=AgentBetta(FakeProvider(), runtime_config=RuntimeConfig(run_dir=str(tmp_path/"runs"))).run("Calculate 17 * 23")
    assert "391" in r.output


def test_previous_output_is_included_in_context(tmp_path):
    from agentbetta.core.models import AgentConfiguration, Task

    agent = AgentBetta(
        FakeProvider(), runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"))
    )
    task = Task("now run it", metadata={"previous_output": "OLD-CODE-HERE"})
    context = agent._build_context(task, AgentConfiguration())
    assert "PREVIOUS ASSISTANT OUTPUT" in context
    assert "OLD-CODE-HERE" in context
