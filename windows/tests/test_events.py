from agentbetta.core.controller import TaskController
from agentbetta.core.events import RunEventBus, RunEventType


class _FakeResult:
    run_id = "run123"
    success = True
    verified = True
    attempts = 1
    output = "done"
    record_path = "rec.json"


class _FakeRuntime:
    def run(self, task, **kwargs):
        return _FakeResult()


class _BoomRuntime:
    def run(self, task, **kwargs):
        raise RuntimeError("provider failed")


def test_event_bus_emits_in_order():
    bus = RunEventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e.type))
    bus.emit_type(RunEventType.RUN_STARTED)
    bus.emit_type(RunEventType.RUN_COMPLETED)
    assert seen == ["run_started", "run_completed"]


def test_listener_exception_does_not_break_emit():
    bus = RunEventBus()
    seen = []

    def bad(_event):
        raise ValueError("bad listener")

    bus.subscribe(bad)
    bus.subscribe(lambda e: seen.append(e.type))
    bus.emit_type(RunEventType.RUN_STARTED)
    assert seen == ["run_started"]


def test_controller_emits_started_and_completed():
    bus = RunEventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e.type))
    controller = TaskController(_FakeRuntime(), event_bus=bus)
    result = controller.run("do it")
    assert result.run_id == "run123"
    assert seen == ["run_started", "run_completed"]


def test_controller_emits_failed_on_error():
    bus = RunEventBus()
    seen = []
    bus.subscribe(lambda e: seen.append(e.type))
    controller = TaskController(_BoomRuntime(), event_bus=bus)
    import pytest

    with pytest.raises(RuntimeError):
        controller.run("do it")
    assert seen == ["run_started", "run_failed"]
