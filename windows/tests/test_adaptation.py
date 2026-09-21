from agentbetta import AgentBetta, PermissionSet, RuntimeConfig
from agentbetta.providers.fake import FakeProvider

def test_selective_model_expansion_changes_only_model_and_records_event(tmp_path):
    agent=AgentBetta(FakeProvider(), runtime_config=RuntimeConfig(run_dir=str(tmp_path/"runs"), max_adaptations=3))
    r=agent.run("[require-model-tier-2] solve this")
    assert r.success and r.final_configuration.model_tier == 2
    assert len(r.adaptations) == 2
    for event in r.adaptations:
        assert event.changed_dimensions == ("model_tier",)

def test_no_permission_escalation_when_not_eligible(tmp_path):
    agent=AgentBetta(FakeProvider(), runtime_config=RuntimeConfig(run_dir=str(tmp_path/"runs"), max_adaptations=2))
    r=agent.run("[require-write] write this", permissions=PermissionSet(frozenset({"file_read"}),frozenset({"file_read"})))
    assert not r.success
    assert not r.final_configuration.permissions.permits("file_write")

def test_permission_activation_only_when_eligible(tmp_path):
    agent=AgentBetta(FakeProvider(), runtime_config=RuntimeConfig(run_dir=str(tmp_path/"runs"), max_adaptations=2))
    p=PermissionSet(frozenset({"file_read"}),frozenset({"file_read","file_write"}))
    r=agent.run("[require-write] write this", permissions=p)
    assert r.success
    assert r.final_configuration.permissions.permits("file_write")


def test_token_limit_raises_budget_and_recovers(tmp_path):
    from agentbetta.core.models import ProviderResponse
    from agentbetta.providers.base import BaseProvider, LLMRequest

    class _Budget(BaseProvider):
        is_cloud = False
        model = "budget"

        def chat(self, request: LLMRequest) -> ProviderResponse:
            if request.max_tokens < 16000:
                return ProviderResponse(
                    "", raw={"failure": "token_limit", "message": "reasoning ate the budget"}
                )
            return ProviderResponse("final answer")

    agent = AgentBetta(
        _Budget(),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"), max_adaptations=3),
    )
    result = agent.run("solve a hard reasoning problem")
    assert result.success
    assert result.final_configuration.token_budget == 16000
