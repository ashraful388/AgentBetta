"""Agent Registry view.

Surfaces the AgentBetta agent identity, its operating contract, the dual-plane
architecture, the agent class taxonomy, tool risk tiers and the lifecycle FSM.
This is descriptive: the GUI never implements a second policy engine.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QHeaderView,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from agentbetta import __version__
from agentbetta.desktop.widgets.ui import Card, KeyValueGrid, SectionHeader, muted

_AGENT_CLASSES = [
    ("Nano Agent", "Ephemeral (task-scoped)", "Task scratchpad; zero long-term storage",
     "L0–L1 read/compute", "AgentBetta's adaptive execution core"),
    ("Worker Agent", "Bounded session", "Domain project memory; episodic logs",
     "L0–L3 workspace read/write", "Domain tasks: files, browser, synthesis"),
    ("Manager Agent", "Persistent/orchestrator", "Shared workflow state; registry",
     "L0–L2 delegation", "Decomposition, budgets (reserved)"),
    ("Reviewer Agent", "Read-mostly evaluator", "Golden rubrics; temporary diffs",
     "L0–L1 read/score", "Independent verification (validator)"),
    ("System Agent", "Platform daemon", "Platform state; metrics",
     "Infrastructure", "Routing, telemetry, memory compaction"),
]

_RISK_TIERS = [
    ("L0", "Pure transform (math, parsing)", "No authorization; in-process"),
    ("L1", "Read internal (workspace, state)", "Automatic within policy"),
    ("L2", "Read external (web, public API)", "Automatic; untrusted payload"),
    ("L3", "Write internal (workspace files)", "Autonomous within storage budget"),
    ("L4", "Write external (notify, push)", "Audit notification"),
    ("L5", "Irreversible / costly (delete, spend)", "Blocking human approval"),
]


def _table(headers: list[str], rows: list[tuple[str, ...]], stretch: int = -1) -> QTableWidget:
    table = QTableWidget(len(rows), len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setSelectionMode(QTableWidget.NoSelection)
    table.setAlternatingRowColors(True)
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            table.setItem(r, c, QTableWidgetItem(value))
    table.resizeRowsToContents()
    if stretch >= 0:
        table.horizontalHeader().setSectionResizeMode(stretch, QHeaderView.Stretch)
    return table


class AgentsView(QWidget):
    def __init__(self, services: Any = None, parent: Any = None) -> None:
        super().__init__(parent)
        self.services = services
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(14)
        outer.addWidget(
            SectionHeader(
                "Agent Registry",
                "Identity, operating contract and governance surfaces for the AgentBetta agent.",
            )
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(14)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        identity = Card("Agent identity card")
        grid = KeyValueGrid()
        grid.set_rows(
            [
                ("Name", "AgentBetta Adaptive Nano-Agent"),
                ("Class", "Nano / Worker (adaptive)"),
                ("Version", __version__),
                ("Mission", (
                    "Dynamically configure intelligence, context, tools, permissions, "
                    "memory and resources per task; verify the outcome; selectively "
                    "adjust only insufficient dimensions."
                )),
                ("Domain", "General local computer, browser and knowledge tasks"),
                ("Profile", "Analytical, conservative, evidence-demanding, verifiable"),
            ]
        )
        identity.add(grid)
        layout.addWidget(identity)

        contract = Card("Agent Operating Contract")
        cgrid = KeyValueGrid()
        cgrid.set_rows(
            [
                ("Risk classification", "reversible-write (bounded by permission profile)"),
                ("Data retrieval", "Autonomous within profile"),
                ("Workspace file generation", "Autonomous within storage budget"),
                ("Network mutation / publishing", "Prohibited / human-approval-required"),
                ("Financial expenditure", "Prohibited"),
                ("Hard caps", "tokens · wall-clock · turns · tool calls (per configuration)"),
                ("Stop conditions", (
                    "verified completion, budget exceeded, 3 consecutive tool "
                    "failures, policy denial, cancellation"
                )),
                ("Rollback", "Run records + pinned provider/model per run"),
            ]
        )
        contract.add(cgrid)
        layout.addWidget(contract)

        planes = Card("Dual-plane separation")
        planes.add(muted(
            "Capability Plane: reasoning, planning, context assembly, model routing, tool "
            "dispatch. Control Plane: policy and permission enforcement, approvals, budgets, "
            "sandboxing, observability. The GUI controls the planes through the core controller; "
            "it never duplicates their logic."
        ))
        layout.addWidget(planes)

        layout.addWidget(Card("Agent class taxonomy"))
        layout.addWidget(_table(
            ["Class", "Lifecycle", "Scope & memory", "Action levels", "Function"],
            _AGENT_CLASSES,
            stretch=4,
        ))

        layout.addWidget(Card("Tool Gateway risk tiers"))
        layout.addWidget(_table(
            ["Tier", "Meaning", "Authorization"], _RISK_TIERS, stretch=2
        ))

        lifecycle = Card("Lifecycle FSM")
        lifecycle.add(muted(
            "UNINITIALIZED → INITIALIZING → PLANNING → EXECUTING → VALIDATING → EVALUATING → "
            "COMPLETED. Exception transitions: any state → FAILED (budget/policy), → KILLED "
            "(emergency stop), → SUSPENDED → RESUMING (approval / long wait)."
        ))
        layout.addWidget(lifecycle)
        layout.addStretch(1)
