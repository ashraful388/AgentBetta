"""Render run summaries into Markdown for the GUI (no chain-of-thought)."""

from __future__ import annotations

from typing import Any


def build_result_markdown(summary: dict[str, Any]) -> str:
    verification = summary.get("verification") or {}
    evidence = verification.get("evidence") or {}
    status = "VERIFIED" if summary.get("verified") else "NOT VERIFIED"
    if verification.get("status") == "ERROR" or summary.get("error"):
        status = "ERROR"
    if summary.get("cancelled"):
        status = "CANCELLED"
    body = summary.get("output") or ""
    if summary.get("cancelled") and not body.strip():
        body = "**Run cancelled.** The partial state was saved; no result was produced."
    elif not body.strip():
        reason = verification.get("reason") or "no output"
        if evidence.get("provider_error") or "Structured failure: provider_error" in reason:
            body = (
                "The model provider could not be reached or returned an error.\n\n"
                f"Reason: **{reason}**\n\n"
                "Check **Settings ▸ Providers & Models** and use **Test connection**, "
                "or switch to a local Ollama model."
            )
        else:
            body = (
                "No final answer was produced.\n\n"
                f"Reason: **{reason}**\n\n"
                "Check the Run details panel for tool activity and adaptations. "
                "If the run timed out, try a faster model, a more specific task, or "
                "run in **adaptive** mode so the time budget can expand."
            )
    footer = (
        f"\n\n---\n**{status}** · attempts: {summary.get('attempts')} · "
        f"provider: {summary.get('provider') or 'n/a'} · model: {summary.get('model_id') or 'n/a'}"
    )
    if summary.get("used_fallback"):
        requested = summary.get("requested_model") or "the selected model"
        body += (
            f"\n\n> **Fallback model used.** `{requested}` was unavailable, so this run "
            f"completed on `{summary.get('model_id') or 'another model'}`. Turn off "
            "provider fallback in **Settings ▸ Reliability** to fail instead."
        )
    return body + footer


def _config_line(config: dict[str, Any] | None) -> str:
    if not config:
        return "n/a"
    perms = config.get("permissions", {})
    return (
        f"tier {config.get('model_tier')}, context {config.get('context_chars')}, "
        f"tokens {config.get('token_budget')}, turns {config.get('max_turns')}, "
        f"tools [{', '.join(config.get('tools', [])) or 'none'}], "
        f"allowed [{', '.join(perms.get('allowed', [])) or 'none'}]"
    )


def build_details_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"**Run:** `{summary.get('run_id')}`")
    lines.append(f"**Provider / model:** {summary.get('provider') or 'n/a'} / {summary.get('model_id') or 'n/a'}")
    lines.append(f"**Attempts:** {summary.get('attempts')}")
    lines.append("")
    lines.append("**Initial configuration**")
    lines.append(f"- {_config_line(summary.get('initial_configuration'))}")
    lines.append("**Final configuration**")
    lines.append(f"- {_config_line(summary.get('final_configuration'))}")

    adaptations = summary.get("adaptations") or []
    if adaptations:
        lines.append("")
        lines.append("**Adaptations**")
        for event in adaptations:
            lines.append(
                f"- attempt {event.get('attempt')}: changed {', '.join(event.get('changed_dimensions', []))} "
                f"— {event.get('reason')}"
            )

    tools = summary.get("tool_results") or []
    if tools:
        lines.append("")
        lines.append("**Tool activity**")
        for tool in tools:
            state = "ok" if tool.get("ok") else f"failed ({tool.get('error')})"
            lines.append(
                f"- `{tool.get('tool_name')}` [{tool.get('risk')}] {state} "
                f"({tool.get('arguments_summary')})"
            )

    verification = summary.get("verification") or {}
    lines.append("")
    lines.append("**Verification**")
    lines.append(f"- {verification.get('status')}: {verification.get('reason')}")

    if summary.get("record_path"):
        lines.append("")
        lines.append(f"**Record:** `{summary.get('record_path')}`")
    return "\n".join(lines)


def record_to_summary(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize a stored run record into the summary shape used by the widgets."""

    task = record.get("task") or {}
    return {
        "run_id": record.get("run_id"),
        "output": record.get("output") or "",
        "success": record.get("success"),
        "verified": (record.get("verification") or {}).get("status") == "PASS",
        "attempts": len(record.get("attempts") or []),
        "record_path": None,
        "initial_configuration": record.get("initial_configuration"),
        "final_configuration": record.get("final_configuration"),
        "adaptations": record.get("adaptations") or [],
        "tool_results": record.get("tool_calls") or [],
        "verification": record.get("verification") or {},
        "provider": record.get("provider"),
        "model_id": record.get("model_id"),
        "task": task.get("objective"),
        "wall_seconds": record.get("wall_seconds"),
        "started_at": record.get("started_at"),
    }
