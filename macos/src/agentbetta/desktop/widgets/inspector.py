"""Right-hand Run Inspector.

Shows the active model, executable configuration, exposed tools, active
permissions, resource usage, adaptation events and verification state. It only
displays what the core reports; it never computes policy itself.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from agentbetta.desktop.widgets.ui import (
    Card,
    ChipList,
    KeyValueGrid,
    badge,
    divider,
    faint,
    set_badge_tone,
)


def _tokens_from_usage(usage: dict[str, Any]) -> tuple[int, int, int]:
    usage = usage or {}
    tokens_in = usage.get("prompt_tokens") or usage.get("prompt_eval_count") or 0
    tokens_out = usage.get("completion_tokens") or usage.get("eval_count") or 0
    total = usage.get("total_tokens") or (int(tokens_in or 0) + int(tokens_out or 0))
    return int(tokens_in or 0), int(tokens_out or 0), int(total or 0)


class InspectorPanel(QWidget):
    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self.setObjectName("Inspector")
        self.setMinimumWidth(288)
        self.setMaximumWidth(420)
        self._started_at = None
        self._model_rows: list[tuple[str, Any]] = []
        self._usage_rows: list[tuple[str, str]] = []
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 10)
        title = QLabel("Run Inspector")
        title.setObjectName("H3")
        self.status = badge("IDLE", "muted")
        header_layout.addWidget(title)
        header_layout.addStretch(1)
        header_layout.addWidget(self.status)
        outer.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        self._body = QVBoxLayout(content)
        self._body.setContentsMargins(14, 4, 14, 16)
        self._body.setSpacing(12)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        self._build_sections()
        self.set_idle()

    # -- construction -----------------------------------------------------
    def _build_sections(self) -> None:
        self.model_card = Card("Active model")
        self.model_grid = KeyValueGrid()
        self.model_card.add(self.model_grid)
        self._body.addWidget(self.model_card)

        self.verification_card = Card("Verification")
        self.verification_row = QHBoxLayout()
        self.verification_badge = badge("—", "muted")
        self.verification_reason = faint("No run yet.")
        self.verification_row.addWidget(self.verification_badge)
        self.verification_row.addStretch(1)
        self.verification_card.add_layout(self.verification_row)
        self.verification_card.add(self.verification_reason)
        self._body.addWidget(self.verification_card)

        self.config_card = Card("Executable configuration  ·  X = ⟨M, C, T, P, Mem, R, τ, I⟩")
        self.config_grid = KeyValueGrid()
        self.config_card.add(self.config_grid)
        self._body.addWidget(self.config_card)

        self.tools_card = Card("Tools exposed")
        self.tools_chips = ChipList()
        self.tools_card.add(self.tools_chips)
        self._body.addWidget(self.tools_card)

        self.permissions_card = Card("Permissions")
        self.permissions_body = QVBoxLayout()
        self.permissions_body.setSpacing(6)
        self.allowed_label = QLabel("Allowed")
        self.allowed_label.setObjectName("FieldLabel")
        self.allowed_chips = ChipList()
        self.eligible_label = QLabel("Adaptively eligible")
        self.eligible_label.setObjectName("FieldLabel")
        self.eligible_chips = ChipList()
        self.denied_label = QLabel("Hard denied")
        self.denied_label.setObjectName("FieldLabel")
        self.denied_chips = ChipList()
        for label, chips in (
            (self.allowed_label, self.allowed_chips),
            (self.eligible_label, self.eligible_chips),
            (self.denied_label, self.denied_chips),
        ):
            self.permissions_body.addWidget(label)
            self.permissions_body.addWidget(chips)
        self.permissions_card.add_layout(self.permissions_body)
        self._body.addWidget(self.permissions_card)

        self.usage_card = Card("Resource usage")
        self.usage_grid = KeyValueGrid()
        self.usage_card.add(self.usage_grid)
        self._body.addWidget(self.usage_card)

        self.adaptations_card = Card("Adaptations")
        self.adaptations_body = QVBoxLayout()
        self.adaptations_body.setSpacing(6)
        self.adaptations_card.add_layout(self.adaptations_body)
        self._body.addWidget(self.adaptations_card)

        self._body.addStretch(1)

    # -- state ------------------------------------------------------------
    def set_idle(self) -> None:
        self._timer.stop()
        self._started_at = None
        self._model_rows = [
            ("Provider", "—"),
            ("Model", "—"),
            ("Tier", "—"),
            ("Locality", "—"),
        ]
        set_badge_tone(self.status, "IDLE")
        self.model_grid.set_rows(self._model_rows)
        self.config_grid.set_rows([])
        self.tools_chips.set_items([], "No run yet")
        self.allowed_chips.set_items([], "—")
        self.eligible_chips.set_items([], "—")
        self.denied_chips.set_items([], "—")
        self.usage_grid.set_rows(
            [("Tokens in", "—"), ("Tokens out", "—"), ("Total", "—"), ("Cost", "—"), ("Wall time", "—")]
        )
        set_badge_tone(self.verification_badge, "—", "muted")
        self.verification_reason.setText("No run yet.")
        self._clear_adaptations()

    def set_run_context(self, *, model_label: str, profile: str, mode: str, local_only: bool) -> None:
        self._started_at = None
        self._timer.stop()
        self._model_rows = [
            ("Selection", model_label),
            ("Permission profile", profile),
            ("Mode", mode),
            ("Local only", "yes" if local_only else "no"),
        ]
        set_badge_tone(self.status, "RUNNING")
        self.model_grid.set_rows(self._model_rows)
        set_badge_tone(self.verification_badge, "PENDING", "info")
        self.verification_reason.setText("Run in progress…")
        self._clear_adaptations()

    def start_clock(self) -> None:
        from datetime import datetime, timezone

        self._started_at = datetime.now(timezone.utc)
        self._timer.start()

    def stop_clock(self) -> None:
        self._timer.stop()

    def _tick(self) -> None:
        if self._started_at is None:
            return
        from datetime import datetime, timezone

        elapsed = (datetime.now(timezone.utc) - self._started_at).total_seconds()
        rows = self._usage_rows
        rows = [(k, (f"{elapsed:.0f}s" if k == "Wall time" else v)) for k, v in rows]
        self.usage_grid.set_rows(rows)

    # -- events -----------------------------------------------------------
    def on_event(self, event: Any) -> None:
        event_type = getattr(event, "type", "")
        data = getattr(event, "data", {}) or {}
        if event_type == "run_started":
            self.start_clock()
            set_badge_tone(self.status, "RUNNING")
        elif event_type == "attempt_started":
            self._apply_config(data.get("configuration"))
            self._set_model_row("Attempt", data.get("attempt"))
        elif event_type == "provider_started":
            self._set_model_row("Turn", data.get("turn"))
            tools = data.get("tools") or []
            self.tools_chips.set_items(list(tools), "none", "info")
        elif event_type in ("tool_requested", "tool_started"):
            self._set_model_row("Current tool", data.get("tool_name"))
        elif event_type == "tool_finished":
            self._set_model_row(
                "Last tool",
                f"{data.get('tool_name')} · {'ok' if data.get('ok') else 'failed'}",
            )
        elif event_type == "verification_updated":
            status = str(data.get("status") or "")
            set_badge_tone(self.verification_badge, status or "—")
            if data.get("reason"):
                self.verification_reason.setText(str(data["reason"]))
        elif event_type == "adaptation_recorded":
            self._append_adaptation(data)
        elif event_type == "run_cancelled":
            set_badge_tone(self.status, "CANCELLED")
            self.stop_clock()

    # -- summary ----------------------------------------------------------
    def set_summary(self, summary: dict[str, Any]) -> None:
        self.stop_clock()
        verified = summary.get("verified")
        if summary.get("cancelled"):
            status = "CANCELLED"
        elif summary.get("error"):
            status = "FAILED"
        elif verified:
            status = "VERIFIED"
        else:
            status = "NOT VERIFIED"
        set_badge_tone(self.status, status)

        verification = summary.get("verification") or {}
        v_status = str(verification.get("status") or "—")
        set_badge_tone(self.verification_badge, v_status)
        self.verification_reason.setText(str(verification.get("reason") or "—"))

        config = summary.get("final_configuration") or {}
        self._apply_config(config)

        self._model_rows = [
            ("Run ID", summary.get("run_id") or "—"),
            ("Provider", summary.get("provider") or "—"),
            ("Model", summary.get("model_id") or "—"),
            ("Tier", str(config.get("model_tier", "—"))),
            ("Attempts", str(summary.get("attempts", "—"))),
            ("Locality", "local" if summary.get("local_only") else "—"),
        ]
        self.model_grid.set_rows(self._model_rows)

        self.tools_chips.set_items(
            list(config.get("tools") or []), "none", "info"
        )
        self._apply_permissions(config.get("permissions") or {})
        self._apply_usage(summary)

        self._clear_adaptations()
        for event in summary.get("adaptations") or []:
            self._append_adaptation(event)

    # -- helpers ----------------------------------------------------------
    def _apply_config(self, config: dict[str, Any] | None) -> None:
        if not config:
            return
        self.config_grid.set_rows(
            [
                ("Model tier (M)", str(config.get("model_tier", "—"))),
                ("Context chars (C)", f"{config.get('context_chars', 0):,}"),
                ("Tools (T)", str(len(config.get("tools") or []))),
                ("Memory items (Mem)", str(config.get("memory_items", "—"))),
                ("Token budget (R)", f"{config.get('token_budget', 0):,}"),
                ("Per-call timeout (τ)", f"{config.get('max_seconds', '—')}s"),
                ("Max turns", str(config.get("max_turns", "—"))),
                ("Max tool calls (I)", str(config.get("max_tool_calls", "—"))),
            ]
        )
        self._apply_permissions(config.get("permissions") or {})

    def _apply_permissions(self, permissions: dict[str, Any]) -> None:
        self.allowed_chips.set_items(list(permissions.get("allowed") or []), "none", "success")
        self.eligible_chips.set_items(list(permissions.get("eligible") or []), "none", "warning")
        self.denied_chips.set_items(list(permissions.get("hard_denied") or []), "none", "danger")

    def _apply_usage(self, summary: dict[str, Any]) -> None:
        usage = summary.get("usage") or {}
        tokens_in, tokens_out, total = _tokens_from_usage(usage)
        cost = usage.get("cost_usd")
        wall = summary.get("wall_seconds")
        rows = [
            ("Tokens in", f"{tokens_in:,}" if tokens_in else "—"),
            ("Tokens out", f"{tokens_out:,}" if tokens_out else "—"),
            ("Total tokens", f"{total:,}" if total else "—"),
            ("Cost", f"${cost:.4f}" if isinstance(cost, (int, float)) else "—"),
            ("Wall time", f"{wall:.1f}s" if isinstance(wall, (int, float)) else "—"),
            ("Tool calls", str(len(summary.get("tool_results") or []))),
        ]
        self._usage_rows = rows
        self.usage_grid.set_rows(rows)

    def _clear_adaptations(self) -> None:
        while self.adaptations_body.count():
            item = self.adaptations_body.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.adaptations_body.addWidget(faint("No adaptations in the last run."))

    def _append_adaptation(self, data: dict[str, Any]) -> None:
        if self.adaptations_body.count() == 1:
            item = self.adaptations_body.itemAt(0).widget()
            if item is not None:
                item.setParent(None)
                item.deleteLater()
        dims = ", ".join(data.get("changed_dimensions") or []) or "none"
        row = QWidget()
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        title = QLabel(f"Attempt {data.get('attempt', '?')} · {dims}")
        title.setWordWrap(True)
        reason = faint(str(data.get("reason") or ""))
        layout.addWidget(title)
        layout.addWidget(reason)
        self.adaptations_body.addWidget(row)
        self.adaptations_body.addWidget(divider())

    def _set_model_row(self, key: str, value: Any) -> None:
        rows = self._model_rows
        rows = [(k, (value if k == key else v)) for k, v in rows]
        if not any(k == key for k, _ in rows):
            rows.append((key, value))
        self._model_rows = rows
        self.model_grid.set_rows(rows)
