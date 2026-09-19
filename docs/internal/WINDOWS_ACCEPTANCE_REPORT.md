# AgentBetta Windows Acceptance Report

**Version:** `0.2.0-alpha.1`
**Date:** 2026-09-13
**Base source revision:** `a4f1b4b4c1b22d0e958e0ae1edf7efc2bda46316`
**Final revision at report time:** see `git log -1` (all work committed)
**Test totals:** **144 passed, 0 failed** (plus 7/7 W7 integrated scenarios PASS,
plus 47/47 GUI acceptance checks PASS)

---

## Core

| Criterion | Status | Evidence |
|---|---|---|
| Existing AgentBetta tests pass | PASS | 125 passed; baseline 17 preserved |
| Adaptive, fixed, wholesale available | PASS | `test_adaptation.py`, `test_fixed_wholesale.py` |
| Actual tool-call loop implemented | PASS | `core/tool_loop.py`; `test_tool_loop.py` |
| Tool calls schema validated | PASS | `tools/schema.py`; `test_tool_schema.py` |
| Adaptation events auditable | PASS | run records + `test_adaptation.py` |
| Validators not overridable by model claims | PASS | `validation/basic.py`; `test_security.py` injection test |

## GUI

| Criterion | Status | Evidence |
|---|---|---|
| PySide6 GUI launches from packaged app | PASS | frozen EXE smoke exit 0; `test_gui_smoke.py` |
| Task composer without workspace | PASS | `TaskView` (workspace optional) |
| Auto and specific-model selection | PASS | `test_provider_management.py` |
| Stop/Cancel works | PASS | worker cancel + `test_tool_loop.py` cancellation |
| Run details show model/provider/tools/permissions/adaptations/verification/usage | PASS | `widgets/report.py`, `TaskView` |
| History reopens prior runs | PASS | `HistoryView`; `test_gui_smoke.py` |
| Settings persistent | PASS | `SettingsStore`; `test_settings_store.py` |

## Providers

| Criterion | Status | Evidence |
|---|---|---|
| Ollama detected and models listed | PASS | live `OllamaProvider.test_connection` / `list_models` |
| OpenAI-compatible custom provider added | PASS | `test_provider_management.py`, `test_provider_contract.py` |
| Endpoint editable | PASS | `ProviderDialog` |
| API key via Credential Manager/keyring | PASS | `settings/secrets.py`; keyring available on host |
| Key not in settings/logs/run records | PASS | `test_provider_management.py`, `test_security.py` |
| Test connection works | PASS | `Services.test_provider`; live OpenAI-compatible `/models` |
| Models refreshed where supported | PASS | `refresh_models`; contract tests |
| Local/cloud status visible | PASS | provider table column |
| Local-only mode cannot call cloud | PASS | `TieredProvider` local-only block; `test_provider_management.py` |

## Model tiers

| Criterion | Status | Evidence |
|---|---|---|
| Tier 0/1/2 mapping | PASS | `settings/models_catalog.py`; `test_model_catalog.py` |
| Adaptive tier change changes actual model | PASS | `test_provider_management.py` (m0→m1→m2) |
| Fixed model mode prevents switching | PASS | fixed mode single attempt; `test_fixed_wholesale.py` |

## Local PC access

| Criterion | Status | Evidence |
|---|---|---|
| Local-drive file access without workspace | PASS | live Test D; `test_runtime_global.py` |
| Absolute paths canonicalized | PASS | `platform/windows/filesystem.py` |
| Read / write / delete permission enforced | PASS | `test_filesystem_global.py`, `test_runtime_global.py` |
| Raw device namespace blocked | PASS | `test_filesystem_global.py` |
| Network shares require separate permission | PASS | `_resolve` UNC gate; `test_filesystem_global.py` |
| Shell/process timeout + output caps | PASS | `test_shell_tools.py` |
| No automatic elevation/UAC bypass | PASS | design + `docs/windows/PC_ACCESS_AND_PERMISSIONS.md` |

## Permissions

| Criterion | Status | Evidence |
|---|---|---|
| Safe / Standard / Extended / Full Computer | PASS | `permissions/profiles.py`; `test_permissions_v2.py` |
| Allow once / Allow for run / Deny | PASS | `permissions/approvals.py`, `ApprovalDialog` |
| Hard-denied cannot be activated | PASS | `test_permissions_v2.py`, `test_runtime_global.py` |
| Web/file content cannot grant permission | PASS | `test_security.py` |

## Browser / Web

| Criterion | Status | Evidence |
|---|---|---|
| Playwright integration works | PASS | live Edge open/extract/search; `test_web_browser.py` |
| Edge detected | PASS | `channel="msedge"` live |
| Dedicated AgentBetta profile | PASS | `%LOCALAPPDATA%\AgentBetta\browser\profile` |
| Search/navigation on current web | PASS | live DuckDuckGo search + example.com fetch |
| Text extraction | PASS | `browser_extract_text` |
| Click/fill require permission | PASS | `test_web_browser.py` |
| Downloads require permission | PASS | `browser_download` + `test_web_browser.py` |
| Browser actions recorded | PASS | session `actions` + run records |
| Normal browser credentials not harvested | PASS | dedicated profile; no cookie/password access |
| CAPTCHA/paywall not bypassed | PASS | design + docs |

## Long-term memory

| Criterion | Status | Evidence |
|---|---|---|
| Global memory store (persistent, user-owned) | PASS | `memory/store.py`; `test_memory.py` |
| Typed memories + hybrid retrieval | PASS | `memory/retrieval.py`; `test_memory.py` |
| Explicit `remember`/`recall` tools (permission-gated) | PASS | `tools/memory.py`; `test_memory.py` |
| Automatic capture on verified runs | PASS | `memory/extract.py`; `test_memory.py` |
| Privacy mode skips capture | PASS | `test_memory.py` |
| `Mem` dimension wired to injection count | PASS | `policy/engine.py`, `core/runtime.py` |
| Settings ▸ Memory inspect/add/forget/clear | PASS | GUI UAT `settings.memory.*` (47/47) |
| Live recall across runs (real model) | PASS | GUI run answered from memory |

## Records and privacy

| Criterion | Status | Evidence |
|---|---|---|
| Run record has provider/model/config/adaptations/verification | PASS | `RunRecord`; `test_runtime.py` |
| PC/browser actions logged with sanitized args | PASS | `ToolResult.arguments_summary` |
| Secrets redacted | PASS | `test_security.py` |
| Privacy mode behaves as documented | PASS | `privacy_mode` redacts task/output |
| Log rotation/bounds | PASS | `RotatingFileHandler` (2 MB × 5) |

## Packaging

| Criterion | Status | Evidence |
|---|---|---|
| PyInstaller spec committed | PASS | `agentbetta.spec` |
| Setup EXE built | PASS | `release/windows/0.2.0-alpha.1/` |
| Portable ZIP built | PASS | same |
| SHA-256 hashes generated | PASS | `SHA256SUMS.txt` |
| Installer version metadata + uninstall entry | PASS | `packaging/version_info.txt`, Inno script |
| End user does not need Python | PASS | frozen bundle |
| No source-tree dependency | PASS | portable copy run outside repo, exit 0 |
| No `.venv` dependency | PASS | frozen bundle |
| Clean-machine install test | PARTIAL | isolated-directory install/uninstall/run PASS; true separate clean VM **not available in this environment** |
| Portable test | PASS | exit 0 |
| Uninstall test | PASS | silent uninstall exit 0; EXE removed |

## Documentation

INSTALL_WINDOWS, QUICK_START, PROVIDERS_AND_MODELS, LOCAL_MODELS,
PC_ACCESS_AND_PERMISSIONS, BROWSER_AND_WEB, TROUBLESHOOTING, UNINSTALL,
BUILD_REPORT, MAC_WINDOWS_PARITY_MATRIX, WINDOWS_ACCEPTANCE_REPORT, and
`WINDOWS_USER_GUIDE.md` — **all present**. **PASS**

## Release blockers

| Blocker | Status |
|---|---|
| Zero known critical permission bypasses | PASS |
| Zero plaintext API-key storage | PASS |
| Zero cloud calls from local-only mode | PASS |
| Zero packaged runtime dependence on developer source | PASS |
| No automatic destructive contraction replay | PASS (candidates only) |

---

## W7 integrated validation (live)

See `W7_VALIDATION_RESULTS.json`.

| Test | Result |
|---|---|
| A — local Ollama read/summarize/write | PASS (verified, file written) |
| B — OpenAI-compatible adapter + tools | PASS |
| C — real-time web retrieval | PASS (web tool used) |
| D — local computer task outside workspace | PASS (file written) |
| E — permission escalation activates eligible permission | PASS |
| F — hard-denied action cannot succeed | PASS |
| G — cancellation | PASS |

## Known limitations

1. **True clean-machine certification not performed.** An isolated-directory
   install/run/uninstall test passed, but a separate clean Windows VM/physical
   machine was not available. This remains the one mandatory acceptance item to
   repeat on a clean machine.
2. **Local model quality varies.** With Ollama `qwen3:1.7b`, simple file/calc
   tasks complete; broad multi-step tasks can exhaust the run budget. A stronger
   tool-calling model improves results. `gpt-oss:20b` failed to load on this host
   with a llama.cpp tensor-size error.
3. **Provider-call cancellation is cooperative.** A cancel takes effect at the
   next checkpoint; an in-flight HTTP inference call cannot be interrupted until
   it returns or times out.
4. Installer is unsigned (SmartScreen warnings expected).
5. macOS parity rows remain pending until the Mac reference is supplied.
