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


def test_unlimited_runtime_has_no_caps(tmp_path):
    result = AgentBetta(
        _SlowProvider(delay=0),
        runtime_config=RuntimeConfig(run_dir=str(tmp_path / "runs"), unlimited=True),
    ).run("do a thing")
    assert result.success
    config = result.final_configuration
    assert config.token_budget == 0
    assert config.context_chars == 0
    assert config.max_seconds == 0
    assert config.max_turns == 0
    assert config.max_tool_calls == 0


def test_unlimited_context_is_not_truncated():
    from agentbetta.core.messages import build_messages
    from agentbetta.core.models import UNLIMITED, AgentConfiguration, Task

    config = AgentConfiguration(context_chars=UNLIMITED)
    long_context = "x" * 200_000
    messages = build_messages(Task("do"), config, long_context)
    assert long_context in messages[1]["content"]


def test_policy_does_not_reimpose_limits_on_unlimited_config():
    from agentbetta.core.models import UNLIMITED, AgentConfiguration
    from agentbetta.policy.engine import selective_expand

    config = AgentConfiguration(
        token_budget=UNLIMITED,
        context_chars=UNLIMITED,
        max_seconds=UNLIMITED,
        max_turns=UNLIMITED,
        max_tool_calls=UNLIMITED,
    )
    out = selective_expand(
        config,
        ("token_budget", "context_chars", "max_seconds", "max_turns", "max_tool_calls"),
        None,
    )
    assert out.token_budget == UNLIMITED
    assert out.context_chars == UNLIMITED
    assert out.max_seconds == UNLIMITED
    assert out.max_turns == UNLIMITED
    assert out.max_tool_calls == UNLIMITED
