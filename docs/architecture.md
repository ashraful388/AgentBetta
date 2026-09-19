# Architecture

AgentBetta's scientific core is platform-neutral. The desktop client is a client
of the same core used by the CLI and the Python API — the GUI does not implement
a separate agent engine.

## Executable configuration

For a task `q`, the agent represents its configuration as:

`X = ⟨M, C, T, P, Mem, R, τ, I⟩`

- `M` — model/capability tier
- `C` — context allocation
- `T` — exposed tools
- `P` — permissions/authority
- `Mem` — memory policy/allocation
- `R` — token/compute/resource budget
- `τ` — time/turn/retry bounds
- `I` — interaction controls

Every adaptation is recorded as an `AdaptationEvent` (before/after
configurations, changed dimensions, reason, evidence, verification).

## The closed loop

```text
Task
  -> characterize (task features)
  -> choose conservative X0 (least agency)
  -> execute under a bounded tool loop
       (tool must be exposed by T AND permitted by P)
  -> verify with a runtime validator (independent of model text)
       PASS -> return + optional counterfactual contraction candidates
       FAIL -> diagnose the insufficient dimension(s)
             -> selectively expand only those dimensions
             -> retry
  -> record configuration, adaptations, verification, usage
  -> frontier store (for later learning)
```

## Core invariants

1. No silent permission escalation.
2. Selective expansion: a diagnosis for one dimension does not expand unrelated ones.
3. Observable adaptation: every change is recorded.
4. Verified success: only the runtime validator may mark success.
5. Failure retention: failed attempts and probes are retained.
6. Local boundary: local-only mode never invokes a cloud provider.
7. Controlled contraction: experiments are limited to safe/reproducible tasks.

## Components

```text
CLI / Python API / Desktop GUI (PySide6)
      |
Desktop Service Layer (settings, secrets, providers, events, history, chats, projects)
      |
AgentBetta Runtime
      +-- Task Characterizer
      +-- Adaptive Configuration Engine (initial policy, diagnosis,
      |     selective expansion, contraction candidates, frontier store)
      +-- Tool Loop (model -> tool request -> permission/approval -> execute -> observation)
      |     +-- Provider Registry (Fake, Ollama, OpenAI-compatible, Tiered, Fallback)
      |     +-- Tool Registry (workspace, global filesystem, shell/process, browser/web, memory)
      |     +-- Permission layer (profiles, hard-deny, approvals)
      +-- Runtime Validators
      +-- Run Recorder
```

Platform-specific code lives only in `src/agentbetta/platform/windows/` and
`src/agentbetta/platform/macos/` (paths, filesystem, shell, processes). Everything
else is shared.

## Modes

- `adaptive` — the full loop (default)
- `fixed` — no adaptation
- `wholesale` — escalate non-authority dimensions together (baseline/ablation)

See `SPECIFICATION.md` and `ARCHITECTURE.md` in the repository for the full
specification.
