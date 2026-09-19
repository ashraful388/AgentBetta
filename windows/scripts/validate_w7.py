"""W7 integrated validation harness (Tests A-G).

Run from the repository root:
    python scripts/validate_w7.py

Writes docs/windows/W7_VALIDATION_RESULTS.json. Live tests are marked SKIPPED
if Ollama or the network is unavailable; deterministic tests always run.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentbetta import AgentBetta, RuntimeConfig  # noqa: E402
from agentbetta.core.cancellation import CancellationToken  # noqa: E402
from agentbetta.core.events import RunEventBus  # noqa: E402
from agentbetta.core.models import ProviderResponse, ToolCall  # noqa: E402
from agentbetta.permissions import (  # noqa: E402
    ApprovalDecision,
    ApprovalService,
    profile_permission_set,
)
from agentbetta.providers import OllamaProvider, OpenAICompatibleProvider  # noqa: E402
from agentbetta.providers.base import BaseProvider  # noqa: E402

WORK = ROOT / "w7"
RUNS = WORK / "runs"
RESULTS: list[dict] = []

OLLAMA_MODEL = os.environ.get("AGENTBETTA_TEST_MODEL", "qwen3:1.7b")


def record(name: str, status: str, detail: str, **extra) -> None:
    entry = {"test": name, "status": status, "detail": detail}
    entry.update(extra)
    RESULTS.append(entry)
    print(f"[{status}] {name}: {detail}", flush=True)


def _ollama_available() -> bool:
    try:
        return OllamaProvider(model=OLLAMA_MODEL).test_connection()[0]
    except Exception:
        return False


def _approvals() -> ApprovalService:
    return ApprovalService(callback=lambda request: ApprovalDecision.ALLOW_RUN)


def test_a() -> None:
    ws = WORK / "a"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "note1.txt").write_text("AgentBetta is an adaptive nano-agent.", encoding="utf-8")
    (ws / "note2.txt").write_text("It verifies outcomes and adapts.", encoding="utf-8")
    target = ws / "summary.md"
    target.unlink(missing_ok=True)
    if not _ollama_available():
        record("A_local_ollama", "SKIPPED", "Ollama not available")
        return
    agent = AgentBetta(
        OllamaProvider(model=OLLAMA_MODEL),
        runtime_config=RuntimeConfig(run_dir=str(RUNS), max_total_seconds=240),
        approvals=_approvals(),
    )
    started = time.time()
    result = agent.run(
        "Read note1.txt in this workspace, then write a one sentence summary to summary.md",
        workspace=str(ws),
        permissions=profile_permission_set("full"),
    )
    record(
        "A_local_ollama",
        "PASS" if result.verified and target.exists() else "FAIL",
        f"verified={result.verified} file={target.exists()} attempts={result.attempts} "
        f"seconds={round(time.time()-started,1)}",
        tools=[t.tool_name for t in result.tool_results],
        output=result.output[:200],
    )


def test_b() -> None:
    ws = WORK / "b"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "data.txt").write_text("The two values are 17 and 23.", encoding="utf-8")
    if not _ollama_available():
        record("B_cloud_adapter", "SKIPPED", "Ollama not available")
        return
    agent = AgentBetta(
        OpenAICompatibleProvider(model=OLLAMA_MODEL, base_url="http://127.0.0.1:11434/v1"),
        runtime_config=RuntimeConfig(run_dir=str(RUNS), max_total_seconds=240),
        approvals=_approvals(),
    )
    started = time.time()
    result = agent.run(
        "Read data.txt and use the calculator tool to compute 17 times 23, then state the result.",
        workspace=str(ws),
        permissions=profile_permission_set("full"),
    )
    record(
        "B_cloud_adapter",
        "PASS" if result.verified and "391" in result.output else "FAIL",
        f"verified={result.verified} seconds={round(time.time()-started,1)}",
        tools=[t.tool_name for t in result.tool_results],
        output=result.output[:200],
    )


def test_c() -> None:
    if not _ollama_available():
        record("C_realtime_web", "SKIPPED", "Ollama not available")
        return
    agent = AgentBetta(
        OllamaProvider(model=OLLAMA_MODEL),
        runtime_config=RuntimeConfig(run_dir=str(RUNS), max_total_seconds=240),
    )
    started = time.time()
    try:
        result = agent.run(
            "Fetch the web page at https://example.com and summarize in one sentence what it says.",
            permissions=profile_permission_set("standard"),
        )
    except Exception as exc:
        record("C_realtime_web", "FAIL", f"{type(exc).__name__}: {exc}")
        return
    used_web = any(t.tool_name in ("http_fetch", "browser_open", "browser_search") for t in result.tool_results)
    record(
        "C_realtime_web",
        "PASS" if result.verified and used_web else "FAIL",
        f"verified={result.verified} web_tool_used={used_web} seconds={round(time.time()-started,1)}",
        tools=[t.tool_name for t in result.tool_results],
        output=result.output[:200],
    )


def test_d() -> None:
    directory = WORK / "d"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "alpha.txt").write_text("Alpha note: launch is Tuesday.", encoding="utf-8")
    (directory / "beta.txt").write_text("Beta note: budget is 42.", encoding="utf-8")
    target = directory / "out.md"
    target.unlink(missing_ok=True)
    if not _ollama_available():
        record("D_local_computer", "SKIPPED", "Ollama not available")
        return
    agent = AgentBetta(
        OllamaProvider(model=OLLAMA_MODEL),
        runtime_config=RuntimeConfig(run_dir=str(RUNS), max_total_seconds=240),
        approvals=_approvals(),
    )
    started = time.time()
    result = agent.run(
        f"Read alpha.txt and beta.txt under {directory} and write a one-sentence combined summary to "
        f"{directory}\\out.md",
        permissions=profile_permission_set("full"),
    )
    record(
        "D_local_computer",
        "PASS" if result.verified and target.exists() else "FAIL",
        f"verified={result.verified} file={target.exists()} seconds={round(time.time()-started,1)}",
        tools=[t.tool_name for t in result.tool_results],
    )


class _DeleteProvider(BaseProvider):
    name = "delete-provider"
    is_cloud = False
    model = "stub"

    def chat(self, request):
        tool_messages = [m for m in request.messages if m.get("role") == "tool"]
        if tool_messages:
            return ProviderResponse("Deleted.")
        return ProviderResponse(
            "", finish_reason="tool_calls",
            tool_calls=[ToolCall("c1", "delete_path", {"path": getattr(self, "target", "")})],
        )


def test_e() -> None:
    target = WORK / "e" / "temp.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("temp", encoding="utf-8")
    provider = _DeleteProvider()
    provider.target = str(target)
    agent = AgentBetta(
        provider,
        runtime_config=RuntimeConfig(run_dir=str(RUNS)),
        approvals=_approvals(),
    )
    result = agent.run("delete the temp file", permissions=profile_permission_set("standard"))
    activated = result.final_configuration.permissions.permits("file_delete")
    record(
        "E_permission_escalation",
        "PASS" if activated and not target.exists() else "FAIL",
        f"file_delete_activated={activated} file_deleted={not target.exists()}",
        adaptations=[list(e.changed_dimensions) for e in result.adaptations],
    )


def test_f() -> None:
    target = WORK / "f" / "keep.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("keep", encoding="utf-8")
    from agentbetta.core.models import PermissionSet

    perms = PermissionSet(
        allowed=frozenset({"file_read"}),
        eligible=frozenset({"file_read", "file_delete"}),
        hard_denied=frozenset({"file_delete"}),
    )
    provider = _DeleteProvider()
    provider.target = str(target)
    agent = AgentBetta(provider, runtime_config=RuntimeConfig(run_dir=str(RUNS)), approvals=_approvals())
    result = agent.run("delete the file", permissions=perms)
    record(
        "F_hard_denied",
        "PASS" if target.exists() and not result.final_configuration.permissions.permits("file_delete") else "FAIL",
        f"file_still_exists={target.exists()}",
    )


class _AlwaysToolProvider(BaseProvider):
    name = "always-tool"
    is_cloud = False
    model = "stub"

    def chat(self, request):
        return ProviderResponse(
            "", finish_reason="tool_calls",
            tool_calls=[ToolCall("c1", "calculator", {"expression": "1+1"})],
        )


def test_g() -> None:
    token = CancellationToken()
    bus = RunEventBus()

    def on_event(event):
        if event.type == "tool_finished":
            token.cancel()

    bus.subscribe(on_event)
    agent = AgentBetta(
        _AlwaysToolProvider(),
        runtime_config=RuntimeConfig(run_dir=str(RUNS), max_adaptations=3),
        event_bus=bus,
        cancel_token=token,
    )
    result = agent.run("Calculate 1 + 1")
    record(
        "G_cancellation",
        "PASS" if result.verification.evidence.get("cancelled") else "FAIL",
        f"cancelled={result.verification.evidence.get('cancelled')}",
    )


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    for test in (test_a, test_b, test_c, test_d, test_e, test_f, test_g):
        try:
            test()
        except Exception as exc:  # noqa: BLE001
            record(test.__name__, "FAIL", f"{type(exc).__name__}: {exc}")
    output = ROOT / "docs" / "windows" / "W7_VALIDATION_RESULTS.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(RESULTS, indent=2), encoding="utf-8")
    print(f"\nWrote {output}")
    failed = [r for r in RESULTS if r["status"] == "FAIL"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
