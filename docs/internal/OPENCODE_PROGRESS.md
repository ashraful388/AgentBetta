# OpenCode Progress Log — AgentBetta Windows Build

Factual milestone log required by `OPENCODE_WINDOWS_BUILD_HANDOFF.md` §35.

## W0 — Baseline Audit
- revision: `a27d005` (baseline committed); archive SHA-256
  `8253aea4...`; MANIFEST 57/57 verified
- tests: 17 passed / 0 failed; benchmark 3/3; CLI smoke PASS
- deliverable: `docs/windows/BASELINE_AUDIT.md`

## W1 — Core service boundaries and settings
- revision: `5a82acf`
- settings store, secret store, provider profiles, model catalog, event bus,
  controller, Windows paths
- tests: 45 passed

## W2 — Normalized provider + tool-call loop
- revision: `1c67575`
- `ProviderResponse.tool_calls`, `chat()` interface, real tool loop,
  cancellation, bounds, structured tool records
- tests: 63 passed

## W3 — Windows Computer Access
- revision: `f1662db`
- typed permissions, profiles, hard-deny, approvals, global filesystem,
  shell/process tools, tool-layer guards
- tests: 90 passed

## W4 — Browser/Web
- revision: `fa7a6af`
- `http_fetch`, Playwright Edge tools, dedicated profile, browser permissions
- tests: 100 passed

## W5 — Windows GUI shell
- revision: `f19699e`
- PySide6 main window, task composer, streaming run details, history, settings
  shell, QThread worker, approvals
- tests: 105 passed

## W6 — Provider/Local-model GUI
- revision: `a11ea4e`
- onboarding, provider CRUD, key storage, discovery, tier mapping, tiered Auto
- tests: 113 passed

## W7 — Integrated real-task validation
- revision: `a4f1b4b`
- structured turn/tool/time diagnosis; feature-gated tool exposure; JSON tool
  fallback; OpenAI adapter tool-call serialization fix
- W7 A–G: 7/7 PASS (`docs/windows/W7_VALIDATION_RESULTS.json`)
- tests: 119 passed

## W8 — macOS parity
- macOS reference not supplied; non-blocking
- deliverable: `docs/windows/MAC_WINDOWS_PARITY_MATRIX.md` (pending rows)

## W9 — Packaging
- revision: `534e243`
- PyInstaller one-directory spec, icon/version metadata, Inno Setup per-user
  installer, portable ZIP, SHA-256 sums, build report
- frozen EXE smoke exit 0; portable run outside repo exit 0; silent
  install/run/uninstall exit 0

## W10 — Security certification
- revision: `4491039`
- injection, secret-scan, redaction, mutating-tool gating tests; provider error
  sanitization
- tests: 125 passed

## W11 — Documentation and release candidate
- README, ARCHITECTURE, SECURITY, IMPLEMENTATION_STATUS, CHANGELOG updated
- `WINDOWS_USER_GUIDE.md`, `WINDOWS_ACCEPTANCE_REPORT.md`
- `docs/windows/*` user guides (install, quick start, providers, local models,
  PC access/permissions, browser/web, troubleshooting, uninstall)
- version set to `0.2.0a1`
- remaining: true clean-machine VM test; macOS parity when reference arrives

## GUI rebuild — three-pane agent console
- revision: working tree (post-W11 GUI rebuild)
- design system: light/dark/system token set + single Qt stylesheet
  (`desktop/theme.py`); consistent cards, badges, inputs, tables, tabs
- three-pane shell (`desktop/main_window.py`): left navigation (Tasks, Projects,
  Agents, Memory, History, Settings, About), center task console, right Run
  Inspector; header with brand and theme/inspector toggles
- new views: Projects (project store), Agents (identity card, operating contract,
  dual-plane, agent class taxonomy, tool risk tiers, lifecycle FSM), Memory
  Fabric (tiered governed memory), rebuilt History with run detail + report export
- Run Inspector (`desktop/widgets/inspector.py`): active model, executable
  configuration `X = ⟨M, C, T, P, Mem, R, τ, I⟩`, exposed tools, allowed/eligible/
  hard-denied permissions, resource usage, adaptations and verification
- Task console rebuilt: composer card, execution activity stream, Markdown result,
  generated-artifact list
- `AppServices` extended with project store, tool catalog and per-run usage
  aggregation; core untouched
- tests: **152 passed** (GUI tests: theme, navigation, inspector, memory, project
  store, result rendering; cancellation regression)

## Physical GUI test + bug fixes
- method: real Qt mouse/key events (QTest) on the live widget tree — typing,
  Run/Stop clicks, navigation clicks, modal approval dialog, provider injection
- scenarios: calculation run, real tool call, navigation, memory add, theme
  toggle, inspector toggle, high-risk approval dialog, permission denial (safe
  profile), cancellation, provider failure — **20/20 checks pass**
- **Fixed (critical):** Stop did not reach the core. `TaskController` created a
  cancellation token but never passed it to `AgentBetta.run`; cancelled runs
  completed and were recorded as successful. Token now propagates; a run
  cancelled during a blocking provider call is recorded `cancelled=True`,
  `success=False`, and shown as `CANCELLED`.
- **Fixed:** result/status rendering now distinguishes `CANCELLED` and
  provider-error states from a plain "not verified".
- **Fixed:** theme toggle skips a same-visible target (System=Light) so every
  click visibly changes theme.
- regression tests added: `tests/test_cancellation.py` (2) and a result-rendering
  test (1)

## Real-task GUI test (filesystem / web / browser / approvals)
- real multi-step tasks driven through the GUI with real tools: read+summarize,
  read+write+artifact, content search with adaptive tool expansion, overwrite
  approval (allow/deny), `http_fetch`, and two consecutive Playwright/Edge runs
- **13/13 real-task checks pass**
- real Ollama `qwen3:1.7b` task through the GUI: model called
  `list_directory_global` + `read_text_file_global` and returned the correct
  budget value, VERIFIED in 1 attempt
- `gpt-oss:20b` returns an Ollama server-side GGUF metadata error
  ("unsupported tensor ... size overflows"); this is a broken/unsupported local
  model blob, not an AgentBetta defect, and is surfaced as a clear provider error
- **Fixed:** hidden capability — native tool calls outside the active
  configuration were executed; now rejected (permission checked first so
  escalation still works)
- **Fixed:** a denied approval was re-prompted on the next adaptive attempt;
  denials are now cached per run and `approval_denied` is terminal for adaptation
- **Fixed:** characterization missed filenames/paths (`notes.txt`, `C:\...`,
  `~/...`), so file tools were not exposed for obvious file tasks
- **Fixed:** second browser run failed because the cached Playwright session was
  bound to the first run's thread; the session is now closed after each run
- regression tests added: `tests/test_security_regressions.py` (5); suite now
  **157 passed**

## UI polish + branded release build
- larger typography (base 11pt, larger headings/cards/badges/tables/tabs) and
  higher-contrast text in light and dark themes
- left navigation enlarged (12.5pt, taller rows, wider sidebar)
- supplied AgentBetta logo integrated: header brand mark, window/app icon, About
  screen; multi-size `.ico` generated from the transparent logo via Pillow
- `agentbetta.spec` bundles the image resources
- rebuilt with `scripts\build_windows.ps1`:
  - `AgentBetta-0.2.0-alpha.1-Windows-x64-Setup.exe` — 68.3 MB
  - `AgentBetta-0.2.0-alpha.1-Windows-x64-Portable.zip` — 97.3 MB
  - frozen smoke launch exit 0; resources present in the bundle
  - `release/windows/0.2.0-alpha.1/SHA256SUMS.txt` updated

## macOS port + clean source trees
- platform facade (`agentbetta.platform`) selecting Windows or macOS at import;
  added `platform/macos/{paths,filesystem,processes,credentials}.py`
- platform-aware shell tool (`run_shell`; PowerShell on Windows, login shell on
  macOS) and `TOOLS_FOR_PERMISSION[shell_exec]`; platform browser engine and
  data paths (macOS: `~/Library/...`, `~/Documents/AgentBetta/runs`)
- macOS packaging: `packaging/agentbetta-macos.spec` (`.app`), `make_icns.py`,
  `scripts/build_macos.sh` (zip + dmg + SHA-256), `docs/macos/BUILD_AND_INSTALL.md`
- tests made platform-aware; suite still **157 passed** on Windows
- clean source trees created:
  - `AgentBetta-Windows/` (Windows platform package + Inno Setup build)
  - `AgentBetta-macOS/` (macOS platform package + `.app`/`.dmg` build)
  - both compile; macOS tree validated to select the macOS platform and expose
    `run_shell`; the `.app`/`.dmg` must be built on macOS (no cross-compile)

## Capability-question fix (browser / local PC)
- reported: "can you browse through my chrome browser?" and "can you access my
  local pc?" returned "I have no tools available"
- cause: `characterize()` had no browsing/local-PC vocabulary, so `needs_network`
  / `needs_files` were false and no tools were exposed; `https://` also
  false-matched the drive-letter path detector
- fix: browser vocabulary exposes browser/web tools; local-computer vocabulary
  exposes filesystem tools; URLs are stripped before path detection; the system
  prompt now lists granted capabilities and available tools
- regression tests added to `test_characterize.py` and `test_tool_loop.py`
- rebuilt + reinstalled the Windows build (Setup SHA-256
  `e73fb29041cd8d0d3df8966d2ee5221538fb6bb0807efe23039053f4cc5dedc1`)

## Licensing and copyright
- adopted the **MIT License**; copyright holder **Dr. Md. Ashraful Babu**
- updated `LICENSE`, `pyproject.toml`, Windows version metadata, `CITATION.cff`,
  README, About screen, `agentbetta/__init__.py`
- added `LICENSES/LGPL-3.0.txt`, `LICENSES/GPL-3.0.txt`, `LICENSES/README.md`
  (Qt LGPL-3.0 compliance) and refreshed `THIRD_PARTY_NOTICES.md`
- installer now bundles `LICENSE`, `LICENSES/`, `THIRD_PARTY_NOTICES.md`
- rebuilt + reinstalled (Setup SHA-256
  `ba21c07be05ce4a2ce845515a52a621b8dc0a7481853e7fec4407750cf2bf144`)

## Trademark + patent preparation
- added `docs/legal/` (confidential): IP roadmap, trademark filing brief,
  trademark policy, patent invention disclosure, provisional application draft,
  prior-art search plan
- added ™ to the window header, About screen, README and Windows version metadata
- `docs/legal/` is not bundled in the installer and must not be published before
  the patent application is filed
- rebuilt + reinstalled (Setup SHA-256
  `a278fe8dab903b56ba8fb2313e796901b091ab21e931b77d9980108ae53bcade`)

## GUI polish: console-window fix + developer section
- **Fixed:** Windows child processes flashed `cmd`/`conhost` windows. All
  subprocess spawns (`run_command`, `start_process`, `reveal_in_explorer`) now
  use `CREATE_NO_WINDOW` + hidden startupinfo (`_hidden_process_kwargs`);
  regression test added. The exe was already GUI-subsystem (subsystem 2).
- **Added:** Developer section on About (Dr. Md. Ashraful Babu — Associate
  Professor of Mathematics, Department of Physical Sciences, IUB, Dhaka) with
  clickable IUB / Google Scholar / Scopus links; safety note made platform-aware.
- rebuilt + reinstalled (Setup SHA-256
  `1608de74cabbc1e44684f1d8475b97dc21d6534571e70409e117e6946b1a6fac`)

## In-app updater (GitHub Releases)
- new `agentbetta.updates` package: release check, asset selection (Windows
  Setup EXE; macOS dmg/zip matched to arch), download + SHA-256 verify, install
  (silent Inno upgrade / macOS bundle swap)
- header **Updates** button with startup check and `⬆ Update <version>` state;
  update dialog with release notes and progress; Settings ▸ General controls
- GitHub Actions now publish a Release on `v*` tags with the assets the updater
  downloads; macOS assets named per architecture
- `tests/test_updates.py` (version ordering, asset selection incl. arch,
  checksums, update decision)
- rebuilt + reinstalled (Setup SHA-256
  `32d5ff815f0077578430b43b5f43fda1e6ee70ae2b86c9a5ab9a1b93974c6f58`)

## UI overhaul (chat console, logo-blue theme, icons, guide)
- task screen rebuilt as a **chat transcript** (user/agent bubbles, preserved
  history, inline status lines) with a compact composer (Enter to send)
- theme accent switched to the **logo blue**; light text is **black**, dark text
  **white**; heavier weights and larger sizes
- built-in **SVG icon set** (`desktop/icons.py`), standard 22 px, theme-tinted;
  used in nav, header and composer
- buttons and tabs have visible borders and accent highlight states
- run **Mode** and **Context folder** moved under an **Advanced** toggle
- **User Guide** tab added under Settings (organised manual)
- Updates button auto-highlights when a release is available
- shared GUI code mirrored to both clean trees; tests pass
- rebuilt + reinstalled (Setup SHA-256
  `b0ed2aa4200173b705db6df1881239a12e3221bda9b926a1b3b4326453cb95f4`)

## UI refinement (density, chats, guide, icon)
- fonts resized (UI 14px, chat/output 12px); lighter logo-blue accent
- single **Run/Stop** button; composer simplified (Local only/Mode/Context under
  **Advanced**)
- **Chats** navigation + persistent conversations (`chats.json`); projects list
  their chats; open a chat to resume
- **Guide** navigation (documentation) plus the Settings User Guide tab
- Windows **desktop shortcut created by default**; AppUserModelID set so the
  taskbar uses the AgentBetta icon
- tests added for chat store and single-button task view; both trees pass
- rebuilt + reinstalled (Setup SHA-256
  `6ec721a7f0bf49249cd51c39beab66d81d4a6bff33dc1ca94e23d97c7c5a0b98`)

## Chat actions + styling; History removed
- agent replies: Copy / Like / Dislike / Try again; user messages: Copy / Edit &
  resend / Resend (icon buttons; ratings persisted on the message)
- animated "thinking" indicator while the model responds
- lighter user bubble; UI-styled output via a QTextDocument stylesheet
- History navigation and view removed (run records still written; reachable via
  Settings ▸ Privacy & Data / Diagnostics)
- both trees pass; rebuilt + reinstalled (Setup SHA-256
  `911f2f8be3f42d4a2f7d8745998f9b8967bfb1591d0e6f99157eaefe0f84e18e`)

## Provider reliability fix (reported "provider_error")
- reproduced with a misconfigured/insufficient cloud provider (chat returned
  model-not-supported / 404 / 503 / timeouts; another account reported
  insufficient credit); only the local model worked
- fixed: real provider message now surfaced in the result/record; transient
  errors retried with backoff; `FallbackProvider` tries another configured model
  (local first, never cloud in local-only) and Auto falls back across tiers
- physically tested: a failing cloud selection now completes on the local model
  and verifies; 29/29 GUI option checks pass
- rebuilt + reinstalled (Setup SHA-256
  `11e7b36f8275a5de5b5aa8e7501acc398e935adb257f19d618fe5e034e9670f8`)

## Public-release cleanup
- removed user-specific UAT/report artifacts and dev run records from the source
  trees and release folder; genericized the one private endpoint in tests
- removed confidential `docs/legal/` from the public trees (kept privately)
- `.gitignore` extended for user data and legal drafts
- provider API keys were never in source (OS credential store only); rebuilt a
  fresh installer (Setup SHA-256
  `4a66d65bbadc93ef196fbe6a2f507ff5c915c9dcfff7060bcf13e0482c7adb23`)
