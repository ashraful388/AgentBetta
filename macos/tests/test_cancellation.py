"""Regression tests for run cancellation.

A previous defect: ``TaskController`` created a cancellation token but never
passed it to the runtime, so Stop only emitted a ``run_cancelled`` event while
the core ran to completion and the run was recorded as successful.
"""

import threading

from agentbetta import AgentBetta, RuntimeConfig
from agentbetta.core.controller import TaskController
from agentbetta.core.models import ProviderResponse
from agentbetta.providers.base import BaseProvider


class _BlockingProvider(BaseProvider):
    name = "blocking"
    is_cloud = False
    model = "blocking-model"

    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()

    def chat(self, request):
        self.started.set()
        self.release.wait(timeout=5)
        return ProviderResponse("late response", usage={"model_calls": 1})


def test_controller_cancel_propagates_to_runtime():
    provider = _BlockingProvider()
    runtime = AgentBetta(provider, runtime_config=RuntimeConfig(record_runs=False))
    controller = TaskController(runtime)

    holder = {}

    def run():
        holder["result"] = controller.run("do something slow")

    thread = threading.Thread(target=run)
    thread.start()
    assert provider.started.wait(5), "provider was never called"

    controller.cancel()
    provider.release.set()
    thread.join(5)

    result = holder["result"]
    assert result.verification.evidence.get("cancelled") is True
    assert result.success is False
    assert result.verified is False


def test_runtime_accepts_explicit_cancel_token():
    from agentbetta.core.cancellation import CancellationToken

    token = CancellationToken()
    token.cancel()
    runtime = AgentBetta(_BlockingProvider(), runtime_config=RuntimeConfig(record_runs=False))
    result = runtime.run("x", cancel_token=token)
    assert result.verification.evidence.get("cancelled") is True
