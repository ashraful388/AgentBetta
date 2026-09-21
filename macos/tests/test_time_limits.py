"""A run must not be killed by a wall-clock time limit by default."""

import time

from agentbetta import AgentBetta, RuntimeConfig
from agentbetta.core.models import AgentConfiguration, ProviderResponse
from agentbetta.providers.base import BaseProvider


class _SlowProvider(BaseProvider):
    name = "slow"
    is_cloud = False
    model = "slow"

    def __init__(self, delay: float = 0.4) -> None:
        self.delay = delay

    def chat(self, request):
        time.sleep(self.delay)
        return ProviderResponse("done", usage={"model_calls": 1})


def test_runtime_config_defaults_to_no_time_limit():
    assert RuntimeConfig().max_total_seconds == 0
    # The per-call timeout is generous and is not a run limit.
    assert AgentConfiguration().max_seconds >= 600


def test_interaction_bounds_are_generous():
    # Real multi-step tasks must not be cut off by a tiny tool-call/turn bound.
    config = AgentConfiguration()
    assert config.max_tool_calls >= 40
    assert config.max_turns >= 25
    assert RuntimeConfig().max_adaptations >= 5


def test_run_completes_without_a_time_limit(tmp_path):
    result = AgentBetta(
        _SlowProvider(),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"), max_total_seconds=0),
    ).run("do a thing")
    assert result.success
    assert result.verified
    assert result.verification.status.value == "PASS"
