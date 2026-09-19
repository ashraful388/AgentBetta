from agentbetta import AgentBetta, RuntimeConfig
from agentbetta.providers.fake import FakeProvider

def test_fixed_mode_does_not_adapt(tmp_path):
    a=AgentBetta(FakeProvider(), runtime_config=RuntimeConfig(run_dir=str(tmp_path/"runs")))
    r=a.run("[require-model-tier-2] solve", mode="fixed")
    assert not r.success and r.attempts == 1 and not r.adaptations

def test_wholesale_mode_expands_multiple_dimensions(tmp_path):
    a=AgentBetta(FakeProvider(), runtime_config=RuntimeConfig(run_dir=str(tmp_path/"runs")))
    r=a.run("[require-model-tier-2] solve", mode="wholesale")
    assert r.success
    assert any(len(e.changed_dimensions) > 1 for e in r.adaptations)
