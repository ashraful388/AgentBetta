# AgentBetta — Windows Baseline Audit (W0)

**Milestone:** W0 — Baseline Audit
**Date:** 2026-09-13
**Auditor:** OpenCode (sole Windows implementer)
**Target release:** `0.2.0-alpha.1` (`0.2.0a1`)
**Status:** PASS — baseline understood; W1 may proceed.

This is the W0 deliverable required by the master work order (§31) and
`OPENCODE_WINDOWS_BUILD_HANDOFF.md` (§2, §39). No functional changes were made.

---

## 1. Exact source path

| Item | Value |
|---|---|
| Authoritative archive | `D:\AI Products\AgentBetta\AgentBetta-v0.1.0-dev.zip` |
| Archive SHA-256 | `8253aea4f82522a0b2f548c7f02c079fd5070c632cf472adeebf7f52d7595de9` |
| Extraction root (clean dev dir) | `D:\AI Products\AgentBetta\dev\src` |
| Package version | `0.1.0.dev0` |
| Platform | win32, 64-bit |
| Development Python | 3.12.1 (via `py -3.12`); system default is 3.13.5 |
| Dev virtualenv | `D:\AI Products\AgentBetta\dev\src\.venv` (Python 3.12) |

Extraction was performed with `Expand-Archive` into a clean directory
(`dev\src`) that was not previously part of any Git repository.

## 2. Source revision / Git state

- **There is no Git repository.** `git rev-parse --is-inside-work-tree` fails in
  both `D:\AI Products\AgentBetta` and `D:\AI Products\AgentBetta\dev\src`.
- **No commit/revision can be recorded.** The baseline is identified instead by:
  - archive SHA-256 above;
  - the in-archive `MANIFEST.sha256`.
- **Integrity check performed:** all **57** manifest entries verified by SHA-256 —
  **0 mismatches, 0 missing files.** The extracted tree is byte-for-byte the
  supplied baseline.
- Recommendation for W1: initialise a local Git repository before the first code
  change so every milestone can record a revision (handoff §2 requires
  `git status` / `git rev-parse HEAD`). This is an audit recommendation, not an
  owner decision.

## 3. Source tree summary

30 Python files, ~900 LOC (source + tests + benchmark). Structure:

```text
dev/src/
  pyproject.toml            # exists (setuptools, src-layout)
  README.md  ARCHITECTURE.md  SPECIFICATION.md  SECURITY.md
  IMPLEMENTATION_STATUS.md  CHANGELOG.md  ROADMAP.md  VISION.md  NAMING.md
  AgentBetta_Final_Workplan.txt   ZCODE_HANDOFF.md   MANIFEST.sha256
  src/agentbetta/
    __init__.py             # public exports + __version__
    cli.py                  # argparse CLI (direct + `run` task-file)
    core/
      models.py             # AgentConfiguration, PermissionSet, Task, TaskFeatures, Result, RunRecord, AdaptationEvent
      characterize.py       # heuristic TaskFeature extraction
      runtime.py            # AgentBetta orchestration loop
    policy/
      engine.py             # initial config, diagnose, selective_expand, wholesale_expand, contraction_candidates
    providers/
      base.py               # ModelProvider Protocol
      fake.py               # deterministic FakeProvider (offline)
      ollama.py             # local Ollama adapter
      openai_compatible.py  # generic cloud OpenAI-compatible adapter
      http.py               # urllib-based post_json helper
    tools/
      registry.py           # ToolRegistry + list/read/write/calculator
      workspace.py          # Workspace path-confinement
    validation/
      basic.py              # BasicValidator (non-empty / structured failure)
    records/
      store.py              # RunRecorder (JSON) + FrontierStore (JSONL)
  tests/                    # 8 files, 17 test functions
  benchmarks/               # run_smoke.py + tasks/smoke.json
  schema/task.schema.json
  examples/task.json
  docs/assets/agentbetta-mechanism.mmd
  scripts/windows_bootstrap.ps1
```

### `pyproject.toml` — present

- `requires-python = ">=3.11"`
- Core runtime dependencies: **none** (stdlib only)
- Optional extras: `yaml` (PyYAML>=6.0), `documents` (pypdf>=5.0),
  `dev` (pytest>=8.0, ruff>=0.6)
- Console script: `agentbetta = agentbetta.cli:main`
- `[tool.pytest.ini_options]` sets `pythonpath=["src"]`, `testpaths=["tests"]`, `addopts="-q"`

## 4. Install result

Command (Python 3.12 venv):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,yaml,documents]"
```

**Result: SUCCESS.** Installed: agentbetta 0.1.0.dev0 (editable), PyYAML 6.0.3,
pypdf 6.18.1, pytest 9.1.1, ruff 0.16.7, plus transitive deps.

> Note: Python 3.12 was chosen deliberately for packaging stability
> (handoff §5). Python 3.13.5 is the machine default but is not the packaging
> target.

## 5. Test results

Command: `.\.venv\Scripts\python.exe -m pytest -v`

```text
platform win32 -- Python 3.12.1, pytest-9.1.1, pluggy-1.6.0
collected 17 items

tests\test_adaptation.py ...        [ 17%]
tests\test_characterize.py ..       [ 29%]
tests\test_cli.py ..                [ 41%]
tests\test_fixed_wholesale.py ..    [ 52%]
tests\test_permissions.py ..        [ 64%]
tests\test_runtime.py ..            [ 76%]
tests\test_tools.py ..              [ 88%]
tests\test_workspace.py ..          [100%]

17 passed in 0.27s
```

| Metric | Value |
|---|---|
| Test files | 8 |
| Test functions collected | **17** |
| Passed | **17** |
| Failed | **0** |
| Errors / skipped | 0 |

This exactly matches the shipped `TEST_RESULTS.txt` (`................. [100%]`).
**No existing passing test was modified or deleted.**

### Benchmark smoke

`.\.venv\Scripts\python.exe benchmarks\run_smoke.py` → **3/3 tasks verified**
(`reasoning-1`, `calc-1`, `files-1`), matching `BENCHMARK_SMOKE_RESULTS.json`.

### Lint (informational)

`ruff check src tests` → **47 findings** (41 auto-fixable): import sorting,
unused imports, quoted annotations, blind `except Exception`. These are
pre-existing style issues; they do **not** affect correctness or the passing
suite. Housekeeping (formatting pass) is deferred and will be bundled with W1
touching of those files, never as a behaviour change.

## 6. CLI smoke-test result

Command: `.\.venv\Scripts\agentbetta.exe --provider fake "Explain AgentBetta in one paragraph."`

```text
AgentBetta completed the offline deterministic task. Its runtime uses
task-conditioned configuration, runtime verification, selective adaptation,
and research-mode contraction proposals.

[AgentBetta] verified=True attempts=1 run=9178c19d10f74420
  record: .agentbetta\runs\9178c19d10f74420.json
```

Command: `.\.venv\Scripts\agentbetta.exe --provider fake --json "Calculate 17 * 23"`

Result: `success=true`, `verified=true`, output `17 * 23 = 391`, run record
written. **CLI smoke-test: PASS.** Exit code 0.

## 7. Provider inventory

| Provider | Status | Local/Cloud | Notes |
|---|---|---|---|
| `FakeProvider` | Implemented, tested | n/a | Deterministic offline; failure hooks (`[require-model-tier-2]`, `[require-context-24000]`, `[require-write]`); arithmetic shortcut |
| `OllamaProvider` | Implemented, **not live-certified** | Local | `/api/generate`, `stream=false`, `num_predict=token_budget`; default `qwen3:1.7b`, `http://127.0.0.1:11434`; no model discovery method |
| `OpenAICompatibleProvider` | Implemented, **not live-certified** | Cloud | `/chat/completions`; key from constructor or `AGENTBETTA_API_KEY` env var; no `/models` discovery |

- Provider contract is a minimal `Protocol` (`name`, `is_cloud`, `generate(task, config, context) -> ProviderResponse`).
- **No provider registry/profile abstraction exists.** Providers are constructed inline in `cli.py` (`_provider`).
- **No Anthropic / Gemini / OpenRouter / Z.ai-GLM / DeepSeek direct adapters.**
- **No tool-calling support** in any provider (`ProviderResponse` has only `text`, `usage`, `raw`; no `tool_calls`/`finish_reason`).

## 8. Tool inventory

Registered in `default_registry()`:

| Tool | Permission | Risk | Notes |
|---|---|---|---|
| `list_directory` | `file_read` | low | Workspace-relative; capped at 500 entries |
| `read_text_file` | `file_read` | low | UTF-8 replace errors; `max_chars` cap |
| `write_text_file` | `file_write` | medium | Creates parent dirs; permission-gated |
| `calculator` | none | low | AST-based safe arithmetic |

**Not implemented:** global filesystem, stat/metadata, delete, copy, move/rename,
mkdir, search, hash, document extraction, shell/PowerShell, process launch,
open file/folder/URL, browser/web, desktop automation, downloads.

## 9. Current filesystem boundary

`tools/workspace.py` `Workspace` is the hard security boundary:

- root = `Path(root).expanduser().resolve()`, must exist;
- `resolve()` builds `root / relative`, resolves it, and rejects anything that
  does not descend from root (`WorkspaceEscapeError`).
- All file tools require a `Workspace` instance and operate only on relative paths.

`_build_context()` in `runtime.py` **explicitly refuses to read absolute or
out-of-workspace inputs** even when `file_read` is permitted
(“explicit workspace required to read this path”). There is currently **no
mechanism** to read an absolute path such as `D:\data\file.txt`.

> **Primary conflict with the Windows direction:** the new requirement is that a
> workspace is optional context, *not* the universal filesystem boundary
> (`CURRENT_WINDOWS_DIRECTION.md`, handoff §10). The present design hard-codes
> the workspace as the only filesystem authority.

## 10. Current permission implementation

`PermissionSet` is a frozen dataclass with:

- `allowed: frozenset[str]` (default `{"file_read"}`)
- `eligible: frozenset[str]` (default `{"file_read"}`)
- `permits(permission)` and `with_permission(permission)` (raises `PermissionError`
  if the permission is not in `eligible`).

Enforcement is minimal and correct for its scope:

- `ToolRegistry.execute()` checks `spec.permission` against `permissions.permits()`.
- `policy/engine.py` may only activate `file_write` when it is externally eligible.
- **No** `hard_denied` concept; **no** typed permission vocabulary; **no** profiles;
  **no** approval/allow-once/allow-for-run/deny flow; **no** high-risk action gating;
  **no** logged permission activations beyond the generic adaptation record.

## 11. Current browser/web capability

**None.** `characterize.py` can detect `needs_network` from keywords, but:

- no HTTP fetch tool is registered (only `providers/http.py` used for LLM calls);
- no Playwright, no Edge/channel selection, no dedicated browser profile;
- no search/navigation/extraction/download tools;
- no `browser_read` / `browser_interact` / `browser_download` permissions;
- no web-action recording.

## 12. Current GUI capability

**None.** There is no `desktop/` package, no PySide6/Qt dependency, no window,
composer, settings surface, history view, or worker/threading layer. The only
front ends are the argparse CLI and the Python API.

`ARCHITECTURE.md` already anticipates a desktop app that “must call the same
core API and must not implement a separate agent engine.”

## 13. Current packaging capability

**None.** `scripts/windows_bootstrap.ps1` only creates a venv and runs tests.
There is:

- no PyInstaller spec;
- no Inno Setup script;
- no `dist/`, `release/`, portable ZIP, installer, icon, version metadata;
- no SHA-256 release manifest, no BUILD/ACCEPTANCE report machinery;
- no clean-machine validation harness.

## 14. Docs ↔ source consistency

| Document | Claim | Source reality | Verdict |
|---|---|---|---|
| `IMPLEMENTATION_STATUS.md` | 17 pytest passed; 3/3 smoke; M2/M3/M5/M7 partial | Confirmed (17 pass, 3/3) | Consistent |
| `SPECIFICATION.md` | X = `<M,C,T,P,Mem,R,Tau,I>`, adaptation events, selective expansion, invariants | Implemented in `models.py` + `policy/engine.py` | Consistent |
| `ARCHITECTURE.md` | CLI/Python API → Runtime → characterizer/policy/providers/tools/validators/recorder | Matches code | Consistent |
| `SECURITY.md` | workspace constrained; writes require `file_write`; keys from env only; shell/network disabled | Matches code | Consistent (and now superseded for scope) |
| `README.md` | offline quick start, Ollama, OpenAI-compatible, structured task | Matches code | Consistent |
| `CURRENT_WINDOWS_DIRECTION.md` | GUI, installer, global PC access, browser, provider settings required | **Not implemented** | Expected gap (this workstream) |
| `OPENCODE_WINDOWS_BUILD_HANDOFF.md` | extensive Windows target | **Not implemented** | Expected gap (this workstream) |

No documentation contradicts the code for the shipped prototype. The
Windows-direction documents describe the **target**, not current behaviour —
`IMPLEMENTATION_STATUS.md` correctly labels the package a research prototype.

## 15. Key architectural gaps for Windows

1. **No service layer / settings / secrets / profiles.** Nothing separates GUI
   from core; no `SettingsStore`, `SecretStore`, `ProviderProfileStore`,
   `ModelCatalog`, `HistoryIndex`, `ApprovalService`, `RunEventBus`.
2. **No real tool-calling loop.** Runtime calls `provider.generate(task, config, context)`
   once, then verifies. There is no message list, no tool schema exposure, no
   tool-call parsing/validation/execution/observation loop, no `max_tool_calls`
   enforcement, no cancellation.
3. **Workspace is the hard FS boundary.** Blocks the required global PC access.
4. **Permission model too narrow.** Only `file_read`/`file_write`; no typed
   vocabulary, `hard_denied`, profiles, approvals, or risk gating.
5. **No browser/web layer.**
6. **No GUI or worker/threading architecture.**
7. **No provider profiles / model catalog / tier→model mapping.** `model_tier`
   is an integer only; it does not select an actual model.
8. **No secrets management.** API key via env var/constructor only.
9. **No Windows per-user paths** (`%LOCALAPPDATA%`, `%APPDATA%`,
   `Documents\AgentBetta`). Run dir defaults to `.agentbetta/runs` beside CWD.
10. **No packaging.** No PyInstaller/Inno/portable path.
11. **No run-event stream / cancellation / sanitized argument logging.**
12. **No logging/diagnostics module** with rotation and secret redaction.

## 16. Smallest safe refactor (W1 direction)

Preserve the scientific core (`models.py`, `characterize.py`, `policy/engine.py`)
and its invariants **unchanged in semantics**. The smallest safe path is:

1. **Introduce additive packages without moving existing files first:**
   `settings/`, `permissions/`, `platform/windows/`, `desktop/`, plus new tool
   modules. Existing modules keep working; new code composes them.
2. **Generalize the provider contract additively:** extend `ProviderResponse`
   with `finish_reason`/`tool_calls` (defaulted), add a typed request object and
   a `generate_messages(...)` method or adapter, while keeping the current
   `generate(task, config, context)` working for `FakeProvider`/CLI/tests.
3. **Introduce a `ToolContext` / path-policy object** that can represent either a
   `Workspace` root **or** an approved global path set, so existing workspace
   tools keep their guarantees while new global tools live behind a permission
   policy. Do not delete `Workspace`.
4. **Extend permissions additively:** keep `PermissionSet` (allowed/eligible) and
   add `hard_denied` + typed permission constants; keep `with_permission` raising
   for ineligible/hard-denied. Provide profiles on top.
5. **Wrap the runtime** in a controller/event bus that emits run events; keep
   `AgentBetta.run()` as the single execution entry point.
6. **Keep CLI working** and migrate it to settings-backed providers *after*
   tests protect the old path.

## 17. Proposed W1 file/module changes (file-level plan)

> Concrete, bounded, and test-first. No GUI or broad feature work in W1.

### New: settings & secrets

- `src/agentbetta/settings/__init__.py`
- `src/agentbetta/settings/models.py` — typed `AppSettings`, `GeneralSettings` (`theme`, `default_mode`, `data_dir`, history behavior)
- `src/agentbetta/settings/store.py` — `SettingsStore` (JSON at `%APPDATA%\AgentBetta\settings.json`), atomic write, schema versioning, no secrets
- `src/agentbetta/settings/secrets.py` — `SecretStore` protocol + `KeyringSecretStore` (Windows Credential Manager via `keyring`) + `InMemorySecretStore` (tests)
- `src/agentbetta/settings/provider_profiles.py` — `ProviderProfile` (`id,name,type,base_url,is_cloud,enabled,default_model,timeout,tls_verify,api_key_ref,options`); serialization provably secret-free
- `src/agentbetta/settings/models_catalog.py` — `ModelProfile` (+ `tier`, `tier_label`, `supports_tools/streaming/vision`, cost fields, `is_local`), `ModelCatalog`, tier→model mapping

### New: paths / platform

- `src/agentbetta/platform/__init__.py`
- `src/agentbetta/platform/windows/paths.py` — `%LOCALAPPDATA%`/`%APPDATA%`/`Documents\AgentBetta` root resolution + override for tests
- `src/agentbetta/platform/windows/credentials.py` — keyring backend shim (import-guarded; falls back gracefully off-Windows)

### New: events/controller boundary

- `src/agentbetta/core/events.py` — `RunEvent` types (`run_started`, `attempt_started`, `provider_started`, `tool_requested`, `approval_required`, `tool_started`, `tool_finished`, `verification_updated`, `adaptation_recorded`, `run_completed`, `run_failed`, `run_cancelled`) + `RunEventBus`
- `src/agentbetta/core/controller.py` — `TaskController` wrapping `AgentBetta.run()`; used by GUI later; emits events; owns cancellation token

### Modified (additive, behaviour-preserving)

- `src/agentbetta/core/models.py` — add `finish_reason`, `tool_calls: list[ToolCall]` (defaulted) to `ProviderResponse`; add `ToolCall` dataclass; add `hard_denied` to `PermissionSet` with backward-compatible defaults
- `src/agentbetta/providers/base.py` — add optional message-based method signature (protocol extension)
- `src/agentbetta/cli.py` — leave intact; optionally read settings later (guarded, non-breaking)
- `src/agentbetta/__init__.py` — export new settings/events types

### New tests (W1)

- `tests/test_settings_store.py` — persistence, atomic write, defaults, schema version
- `tests/test_secrets.py` — save/replace/delete via in-memory; assert settings/profile JSON never contains the secret
- `tests/test_provider_profiles.py` — round-trip serialization with no secret fields
- `tests/test_model_catalog.py` — tier 0/1/2 mapping, local/cloud flags, cost metadata
- `tests/test_events.py` — event emission order from a fake run; cancellation hook
- `tests/test_paths.py` — per-user path resolution (monkeypatched env)

### W1 acceptance gate

- All 17 baseline tests still pass (unchanged).
- New tests pass.
- **No API key is ever written to any settings/profile/run JSON or log** (asserted by test).
- Existing CLI + FakeProvider path unchanged end-to-end.

## 18. Proposed W2–W4 plan (summary, file-level)

**W2 — normalized provider + real tool loop**
- `core/models.py`: `ToolCall`, `ToolResult`, extend `ProviderResponse`.
- `core/tool_loop.py` (new): message assembly, tool-schema exposure limited to
  current `AgentConfiguration.tools`, tool-call validation → permission check →
  execution → observation → continue, bounded by `max_turns`/`max_tool_calls`/
  `max_seconds`; JSON fallback protocol for non-native models.
- `providers/openai_compatible.py` + `ollama.py`: parse native tool calls and a
  structured JSON fallback; move ALL vendor parsing out of `core/runtime.py`.
- `providers/fake.py`: add deterministic tool-call fixture(s).
- `validation/tool_call.py` (new): schema validation; validators keyed on
  tool/file/exit evidence, never model claims.
- `core/runtime.py`: swap single-shot generate for the tool loop while preserving
  diagnosis/selective-expansion semantics and all adaptation records.
- Tests: `test_tool_loop.py`, `test_tool_schema_validation.py`, provider contract tests.

**W3 — Windows computer access + permissions + approvals**
- `permissions/policy.py`, `permissions/profiles.py` (Safe/Standard/Extended/Full
  Computer), `permissions/approvals.py` (Allow once / Allow for run / Deny).
- `tools/filesystem.py` (global absolute paths: list drives/dir, stat, read,
  binary metadata, mkdir, write, append, copy, move, delete, search names/text,
  hash, open/reveal), `tools/shell.py` (PowerShell + exe with timeout/output caps,
  cwd, exit code), `tools/processes.py` (launch/list/terminate-own only, open).
- `platform/windows/filesystem.py`, `platform/windows/processes.py` — canonical
  paths, block `\\.\`, treat UNC as separate `network_share` permission.
- `core/tool_loop.py`: hook approval service for high-risk actions.
- Tests: outside-workspace read/write allowed with permission; denied without;
  hard-deny unbypassable; shell timeout; raw device path blocked.

**W4 — browser/web**
- `tools/web.py` (read-only HTTP fetch), `tools/browser.py` (Playwright, Edge
  `channel="msedge"`, dedicated profile under `%LOCALAPPDATA%\AgentBetta\browser`,
  open/search/extract/click/fill/select/screenshot/download/back/close).
- Permissions `browser_read` / `browser_interact` / `browser_download`.
- Tests: deterministic local fixture pages; injection cannot grant permission;
  profile isolation; cancellation.

## 19. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | Python 3.13 default vs packaging target | Medium | Pin 3.12 for venv/build; document |
| 2 | Keyring may prompt or fail on some Windows configs | Medium | Abstract `SecretStore`; in-memory fallback for tests; clear error surface; never plaintext fallback |
| 3 | Playwright + Edge bundling under PyInstaller | High | One-directory build; prefer installed Edge; documented fallback; test early in W9 |
| 4 | Refactoring runtime risks breaking reproducibility/benchmarks | High | Additive changes; keep 17 tests green; never change adaptation semantics in W1/W2 |
| 5 | `nodelete` security regressions in globals FS | High | Deny-by-default + typed permissions + hard_denied + approval tests at every layer |
| 6 | Prompt injection via web/files granting capabilities | High | Treat all retrieved content as data; policy layer not reachable from tool output (SECURITY invariant) |
| 7 | Network share vs local conflated | Medium | Separate `network_share` permission from the start |
| 8 | Cost/token reporting from arbitrary endpoints | Medium | Store only when provider exposes it; never fabricate |
| 9 | No Git baseline → hard to roll back | Medium | Initialise local Git before W1 (recommended) |
| 10 | Ruff debt obscuring real diffs | Low | Format touched files in W1; do not mass-format unrelated code |

## 20. Stop-condition check (handoff §37)

None of the stop conditions are present in the baseline:

- no permission bypass exists (the model is `file_read`/`file_write` with
  eligibility, and the write path is tested);
- hard permission policy is not model-reachable;
- no secret storage/logging exists at all (nothing in plaintext);
- no browser automation exists;
- app is not packaged, so no source-tree/.venv dependency exists yet;
- local-only guard is present in `runtime.py` (`Cloud provider cannot be used for
  a local-only task`) and needs to be extended, not repaired;
- no GUI adaptation engine exists;
- contraction candidates are **proposed only** and never auto-replayed (safe).

## 21. W0 conclusion

The baseline is a clean, internally consistent, fully passing research prototype:
**17/17 tests, 3/3 smoke, CLI OK, archive integrity 57/57, zero mismatches.**
It contains no GUI, no packaging, no browser access, no tool-calling loop, and a
workspace-locked filesystem/permission model — all of which the Windows
workstream must add. The scientific core (`AgentConfiguration`, characterization,
selective diagnosis/expansion, contraction candidates, run/frontier records,
FakeProvider determinism) is sound and must be preserved and extended additively.

**W0 status: PASS.** No broad implementation was performed.

---

### Deliverable checklist (work order §31)

| Required item | Where |
|---|---|
| Exact source path | §1 |
| Source tree summary | §3 |
| `pyproject.toml` exists? | §3 |
| Install result | §4 |
| Test count / pass / fail | §5 |
| CLI smoke-test result | §6 |
| Provider inventory | §7 |
| Tool inventory | §8 |
| Current filesystem boundary | §9 |
| Current permission implementation | §10 |
| Current browser/web capability | §11 |
| Current GUI capability | §12 |
| Current packaging capability | §13 |
| Key architectural gaps for Windows | §15 |
| Proposed W1 file/module changes | §17 |
| Risks | §19 |
| Commit/revision | §2 (no Git; archive SHA-256 recorded) |
