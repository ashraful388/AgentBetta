# Changelog

## 0.2.0-alpha.3 — 2026-09-25

### Fixed
- **GitHub update source.** The updater now uses `ashraful388/AgentBetta` and
  migrates the previous repository value from existing settings.
- **Update availability and installation.** The header and Settings checks now
  share one request, highlight available releases, retry visibly after failures,
  and open the update dialog from the first click. Source runs can download and
  launch the installer.
- **Release compatibility.** Prerelease versions use semantic ordering across
  paginated releases, platform/CPU assets are validated, and split SHA-256
  manifests are merged before installation.

## 0.2.0-alpha.2 — 2026-09-22

### Added
- **Unlimited mode (no token, time, context or step caps).** New
  `RuntimeConfig.unlimited` / Settings → General → "No token or time limits"
  (on by default): `token_budget`, `context_chars`, `max_seconds`, `max_turns`
  and `max_tool_calls` become `UNLIMITED` (0). Providers omit `max_tokens` /
  `num_predict`, HTTP uses no timeout, context is never truncated, and
  adaptation can no longer re-impose a cap.
- **Follow-up continuity.** A short message in an ongoing chat (e.g. "now run
  it") now carries the previous assistant output as labeled reference context,
  so pronouns resolve across runs.
- **Fallback disclosure.** Results state when a fallback model answered
  instead of the selected one.

### Fixed
- **Orphaned models in the selector.** Deleting a provider left its catalog
  models (and stale tier assignments) visible and selectable. `model_choices()`
  now hides models whose provider is missing/disabled, removing a provider
  prunes its models, and settings self-heal on load.
- **Reasoning models burning the token budget.** A response with empty content
  and `finish_reason == "length"` (or reasoning tokens ≥ completion tokens) is
  now a structured `token_limit` failure, so adaptive mode raises the budget
  instead of reporting "no usable output".
- **Execution intent detection.** "run it" / "execute …" now expose shell and
  process tools (previously no tools were exposed at all).
- **Server-closed connections** now surface an actionable message (request too
  large or server-side cap; try a smaller task or a different model) instead of
  raw `RemoteDisconnected`.

## Unreleased — no task time limit, generous interaction bounds

### Changed
- **Generous interaction bounds (fixes `Structured failure: tool_limit`).**
  Real multi-step tasks were stopped after only a few tool calls. Defaults and
  adaptive ladders raised: `max_tool_calls` 3 → **40** (ladder 40/80/160/320),
  `max_turns` 3 → **25** (ladder 25/50/100), `max_adaptations` 3 → **8**.
- **Removed the wall-clock time limit for task execution.** A run is no longer
  aborted by elapsed time (previously a 600 s run cap plus a per-attempt time
  budget that produced `Structured failure: timeout`). A run now continues until
  it succeeds, is cancelled, or reaches a step/resource bound.
  - `RuntimeConfig.max_total_seconds` defaults to **0 = no limit**.
  - The per-attempt time abort was removed; the τ dimension is now only the
    per-model-call timeout (default raised to 600 s; ladder 600/1200/2400).
  - New **Settings ▸ General ▸ “Time limit per run”** control (default *No limit*).
  - The Run Inspector labels τ as the **per-call timeout**, not a run limit.

## Unreleased — provider keys, shutdown and startup fixes

### Fixed
- **API keys were not persisted in the packaged Windows app.** The frozen build
  did not bundle `win32ctypes`, so `keyring`'s Windows backend failed and keys
  fell back to session-only memory — providers appeared added but stopped working
  after a restart. The PyInstaller spec now bundles `win32ctypes` (and
  `keyring.backends.Windows`), and `pywin32-ctypes` is an explicit dependency.
- **Crash on exit (`0xC0000409`).** A background `QThread` (the startup update
  check) was destroyed while still running during Qt teardown. The app now asks
  threads to stop, waits briefly, and exits the process directly.
- **Corrupt/BOM settings file crashed startup.** `SettingsStore.load()` now reads
  UTF-8 with BOM tolerance and, on invalid JSON, preserves the file as
  `settings.json.corrupt` and falls back to defaults instead of raising.
- **`httpx` was a hard import.** `tools/web.py` now imports it lazily, so a
  missing optional dependency can no longer break the whole tool registry; build
  instructions include the `http` extra.
- The provider dialog now warns when secure storage is unavailable instead of
  silently discarding keys.
- Both platform trees ship `LICENSES/` and `THIRD_PARTY_NOTICES.md`; the
  PyInstaller specs anchor paths to their own folder.

## Unreleased — GUI rebuild (three-pane agent console)

### Added
- Design system (`desktop/theme.py`): light/dark/system tokens and one cohesive
  Qt stylesheet (cards, badges, inputs, tables, tabs, scrollbars).
- Three-pane shell: left navigation (Tasks, Projects, Agents, Memory, History,
  Settings, About), center task console, right Run Inspector.
- Run Inspector: active model, executable configuration `X = ⟨M, C, T, P, Mem,
  R, τ, I⟩`, exposed tools, allowed/eligible/hard-denied permissions, resource
  usage, adaptation events and verification state.
- Projects view backed by a secret-free project store (`desktop/projects.py`).
- Agents view: identity card, operating contract, dual-plane separation, agent
  class taxonomy, tool risk tiers (L0–L5) and lifecycle FSM.
- Memory Fabric view: tiered view (working/short-term/semantic/episodic/
  procedural) over the governed memory store.
- History view rebuilt with inline run detail and Markdown/JSON report export.
- Task console rebuilt with an execution activity stream and generated-artifact
  list.
- 5 new GUI tests (theme, navigation, inspector, memory, project store).

### Changed
- Settings view adopts the shared section header and design system.
- About and approval dialogs restyled; approval dialog is explicit about tool,
  permission, risk and arguments.
- Larger typography across the app (base 11pt; larger headings, cards, badges,
  tables, tabs) and higher-contrast text colors in both light and dark themes.
- Left navigation uses a larger font and taller rows for readable icons/labels.
- The supplied AgentBetta logo is used for the header brand mark, the window and
  application icon, and the About screen; `packaging/make_icon.py` now generates a
  multi-size `.ico` from the transparent logo.

### Build
- Windows release rebuilt: `AgentBetta-0.2.0-alpha.1-Windows-x64-Setup.exe`
  (68.3 MB) and `AgentBetta-0.2.0-alpha.1-Windows-x64-Portable.zip` (97.3 MB);
  SHA-256 in `release/windows/0.2.0-alpha.1/SHA256SUMS.txt`.

### Public-release cleanup (no user/provider data in source or build)
- Removed leaked, user-specific artifacts from the source trees and release
  folder (UAT/report files that listed private providers/models).
- Genericized the one test that used a private endpoint/model to
  `https://api.example.com/v1` / `example-model`.
- Removed confidential `docs/legal/` (patent/trademark drafts) from the public
  trees; kept privately in the working copy.
- Deleted development run records (`.agentbetta/`, `w7/`) from the working tree.
- Strengthened `.gitignore` to exclude user data (`settings.json`, `chats.json`,
  `projects.json`, memory/records) and `docs/legal/`.
- Rebuilt the installer fresh. Provider API keys were never in the source: they
  live only in the OS credential store (Windows Credential Manager / macOS
  Keychain); provider profiles live in per-user `settings.json`.

### Provider reliability (real errors, retry, fallback)
- **Real provider errors are surfaced.** A failed provider call now reports the
  actual (redacted) message (e.g. `HTTP 400: credit insufficient balance` or
  `Requested model ... not supported`) in the result and run record instead of a
  generic "provider_error".
- **Transient retry**: timeouts and 5xx/429 responses are retried up to 3 times
  with exponential backoff before failing.
- **Provider fallback**: if the selected model fails, AgentBetta tries another
  configured model (local providers first, then cloud; never cloud in local-only
  mode) via `FallbackProvider`; Auto mode also falls back across tiers. Toggle in
  Settings ▸ General ▸ Reliability. The provider/model actually used is recorded.
- Fixes the reported case where a cloud model failed and the whole task failed;
  it now completes on the local model.

### Chat actions, output styling, History removed
- **Per-message actions (icons)**: agent replies have **Copy, Like, Dislike,
  Try again**; user messages have **Copy, Edit & resend, Resend**. Ratings are
  persisted on the message.
- **Thinking indicator**: an animated "AgentBetta is thinking…" line while a
  model is responding.
- **Lighter user bubble**: `#dbeafe` in light mode / `#1d3a5c` in dark mode.
- **UI-styled output**: chat output is rendered with a document stylesheet
  (headings, code blocks, blockquotes, tables, links) inside the bubbles.
- **History removed**: the History navigation/view is gone (chats and projects
  now cover it). Run records are still written and reachable from
  Settings ▸ Privacy & Data / Diagnostics.

### UI refinement (density, chats, guide, icon)
- **Fonts resized**: UI text is 14px, chat/output text is 12px (was too large).
- **Lighter accent blue** (`#3b82f6` light / `#6aa4ff` dark) derived from the logo.
- **Single Run/Stop button** that toggles with the run state.
- **Chats navigation**: a new **Chats** view lists every saved conversation
  (title, project, messages, updated, status) with a preview and open/delete;
  conversations persist automatically to `chats.json`.
- **Projects → chats**: selecting a project lists its chats; open one to resume.
- **User Guide/Documentation**: new top-level **Guide** view (plus the Settings
  tab) with the full manual.
- **Composer organised**: only Model, Permissions, attach and Run/Stop on the
  main row; **Local only**, Mode and Context folder live under **Advanced**.
- **Windows desktop shortcut** is now created by default, and the app sets an
  AppUserModelID so the taskbar shows the AgentBetta icon.

### UI overhaul (chat console)
- **Chat interface**: the task screen is now a chat transcript of message bubbles
  (user right, AgentBetta left) with preserved conversation, in-line status
  lines for tool/verification activity, and a compact composer (Enter to send,
  Shift+Enter for a new line). Removed the static result/activity boxes.
- **Logo-blue theme**: the accent colour is now taken from the AgentBetta logo
  blue (`#0f62fe` light / `#4c8dff` dark) instead of green.
- **Typography**: true **black** text in light mode and **white** in dark mode,
  heavier weights (Medium base, bold headings) and larger sizes.
- **Icons**: a built-in SVG line-icon set at a standard 22 px, tinted to the
  theme; used in the navigation, header and composer buttons.
- **Buttons & tabs** now have visible borders and accent highlight states.
- **Simplified main screen**: run **Mode** and **Context folder** moved under an
  **Advanced** toggle; research controls stay out of the routine path.
- **User Guide** tab added under Settings — an organised manual (getting started,
  models, tasks, permissions, browser, memory, updates, history, privacy,
  troubleshooting, file locations).
- **Updates button** is auto-highlighted (accent, filled) whenever a newer
  GitHub release is found.

### In-app updates (GitHub Releases)
- Added `agentbetta.updates`: GitHub Releases version check, platform-aware
  asset selection (Windows Setup EXE; macOS dmg/zip matched to the CPU
  architecture), download with progress, SHA-256 verification, and install
  (silent Inno upgrade on Windows; dmg/`ditto` bundle swap on macOS).
- Added an **Updates** button in the header that checks on startup and shows
  `⬆ Update <version>` when a release is available, plus an update dialog with
  release notes, download progress and install.
- Added Settings ▸ General update controls: check on startup, channel
  (stable/pre-release), update source (`owner/repo`) and "Check for updates now".
- Added GitHub Actions release jobs: pushing a `v*` tag publishes a Release with
  the Setup EXE / portable ZIP / macOS zip+dmg and `SHA256SUMS.txt` that the
  updater consumes. macOS assets are now named per architecture.
- Tests: version ordering, asset selection (incl. architecture), checksum
  verification, and update decision (`tests/test_updates.py`).

### License and copyright
- AgentBetta is now **MIT licensed**; copyright (c) 2026
  **Dr. Md. Ashraful Babu**.
- Replaced the placeholder `LICENSE`; updated `pyproject.toml` (license/authors),
  Windows file-version metadata, `CITATION.cff`, README, the About screen and
  `src/agentbetta/__init__.py` (`__license__`/`__author__`).
- Added `LICENSES/` with the official LGPL-3.0 and GPL-3.0 texts and a Qt
  LGPL-3.0 compliance note; `THIRD_PARTY_NOTICES.md` updated (first-party MIT +
  third-party components).
- The packaged application and installer now bundle `LICENSE`, `LICENSES/` and
  `THIRD_PARTY_NOTICES.md`.

### Trademark and patent preparation
- Added `docs/legal/` — filing-ready IP dossier:
  `IP_ROADMAP.md`, `TRADEMARK_FILING_BRIEF.md`, `TRADEMARK_POLICY.md`,
  `PATENT_INVENTION_DISCLOSURE.md`, `PROVISIONAL_APPLICATION_DRAFT.md`,
  `PRIOR_ART_SEARCH_PLAN.md`.
- Added ™ notices: window header and About screen show "AgentBetta™"; About shows
  the trademark line; Windows version metadata adds `LegalTrademarks`.
- `docs/legal/` is **confidential** and is deliberately **not** bundled into the
  installer; do not publish it until the patent application is filed.

### Cross-platform (macOS port)
- Added a macOS platform layer (`src/agentbetta/platform/macos/`: paths,
  filesystem, processes, credentials) and a platform facade that selects the
  implementation by OS. Data paths, the shell tool (`run_shell` via the login
  shell), open/reveal, volume listing and the preferred browser engine are now
  platform-aware; the scientific core and GUI are unchanged.
- Platform-aware shell-tool mapping (`TOOLS_FOR_PERMISSION[shell_exec]`) so the
  macOS shell tool is exposed correctly.
- Added macOS packaging: `packaging/agentbetta-macos.spec` (`.app` bundle),
  `packaging/make_icns.py`, and `scripts/build_macos.sh` (zip + dmg + hashes),
  plus `docs/macos/BUILD_AND_INSTALL.md`.
- Made the test suite platform-aware (`test_paths`, `test_shell_tools`,
  `test_filesystem_global`) so the same suite runs on Windows and macOS.
- Produced two clean source trees: `AgentBetta-Windows/` and `AgentBetta-macOS/`
  (source, tests, docs and build files only; no build outputs, caches or venv).

### Fixed
- **Cancellation now reaches the core runtime.** `TaskController` previously
  created a cancellation token but never passed it to `AgentBetta.run`, so the
  Stop button emitted a `run_cancelled` event while the run completed and was
  recorded as `success=True`. The token is now passed through and honoured after
  any in-flight provider call returns.
- A run cancelled during a blocking provider call is recorded `cancelled=True`,
  `success=False`, and is never reported as verified.
- GUI result/status now shows `CANCELLED` and provider-error states explicitly
  instead of a generic "No final answer" / "Not verified".
- Theme toggle skips a target that resolves to the same visible theme (e.g.
  System=Light), so every click visibly changes the theme.
- **No hidden capability:** a native tool call is now rejected unless the tool is
  exposed by the active `AgentConfiguration`. Permission is evaluated first so
  adaptive permission escalation still works; a permission-granted but
  unexposed tool is refused and drives tool expansion instead of executing.
- **Approval denials are durable for a run.** A denied action is cached and never
  re-prompts, and `approval_denied` is terminal for adaptation (the agent no
  longer retries a denied action on the next attempt).
- **Characterization detects filenames/paths.** Tasks mentioning `notes.txt`,
  `C:\...`, `~/...` now set `needs_files`, so read/write tools are exposed
  immediately instead of requiring an adaptation round-trip.
- **Browser works across runs.** The Playwright session is closed at the end of
  every run so the next run can start it cleanly on its own worker thread
  (previously a second browser run in the same session failed). The on-disk
  browser profile is preserved.
- **Capability questions now expose the right tools.** "Can you browse my
  Chrome?" and "Can you access my local PC?" previously matched no task feature,
  so no tools were exposed and the agent (correctly, but unhelpfully) replied
  that it had no tools. Browsing vocabulary ("browse", "browser", "chrome",
  "website", …) now exposes the browser/web tools, and local-computer vocabulary
  ("pc", "computer", "drive", "my files", …) exposes the filesystem tools. URLs
  no longer false-trigger the drive-letter path detector.
- **The system prompt states granted capabilities.** It now lists the allowed
  permissions and available tools, so the agent answers "can you do X?"
  accurately and points to the permission profile instead of denying all access.
- **No more console windows.** Every Windows child process the app spawns
  (PowerShell/shell, `tasklist`/`taskkill`, `explorer`/reveal, launched
  executables) now uses `CREATE_NO_WINDOW` with a hidden `STARTF_USESHOWWINDOW`
  startupinfo, so packaged GUI use no longer flashes `cmd`/`conhost` windows.
- **Developer section on the About screen.** Shows Dr. Md. Ashraful Babu's name,
  role, department, university and location, with clickable IUB / Google Scholar
  / Scopus profile links; the safety note is now platform-aware.

## 0.2.0-alpha.1 — 2026-09-13

Windows desktop alpha. Scientific core preserved from 0.1.0-dev.

### Added
- PySide6 desktop client: New Task, History, Settings, About; streaming run
  details; Markdown results; QThread worker with cancellation.
- Settings service: secret-free settings store, Windows Credential Manager secret
  store, provider profiles and presets, model catalog, tier mapping.
- Provider/model management GUI: add/edit/remove/enable, API key handling, test
  connection, model discovery, Ollama detection, first-run onboarding.
- Tiered `Auto (AgentBetta)` provider that routes each call to the model mapped
  to the active model tier.
- Real normalized tool-call loop with schema validation, permission and approval
  checks, bounds, structured tool records, and a JSON fallback protocol.
- Typed permission vocabulary and profiles (Safe/Standard/Extended/Full
  Computer), `hard_denied`, and allow-once/allow-for-run/deny approvals.
- Global Windows filesystem tools (drives, list, stat, read/write/append, copy,
  move, delete, search, grep, hash) and shell/process/open tools.
- Browser/web tools: `http_fetch` and Playwright (Edge) navigation, search,
  extraction, click, fill, select, screenshot, download, back.
- Diagnostics: rotating logs, diagnostics tab, Windows paths module.
- Global long-term memory: typed memory store (fact/preference/episode/summary),
  hybrid retrieval (keyword + optional local Ollama embeddings + recency/
  importance/usage), explicit `remember`/`recall` tools, automatic capture on
  verified runs, `Mem` configuration dimension wired to injection count,
  Settings ▸ Memory manager, CLI `--memory`.
- Packaging: PyInstaller one-directory spec, icon and version metadata, Inno
  Setup per-user installer, portable ZIP, SHA-256 sums, build report.
- Test suite expanded from 17 to **125** passing tests; W7 integrated validation
  A–G all pass.

### Changed
- Runtime now drives a tool loop instead of a single context prompt, while
  preserving characterization, diagnosis, selective expansion, contraction
  candidates and run records.
- Permission model extended with `hard_denied`; `with_permission` refuses
  hard-denied/ineligible activation.
- Local models: `think` disabled by default for qwen3-class Ollama models.

### Security
- Secrets stored only in Windows Credential Manager; provider errors redacted.
- Retrieved content cannot grant permissions; mutating tools are permission-gated
  at the tool layer as well as the registry.
- Local-only mode blocks cloud inference.

## 0.1.0-dev — 2026-09-10

- Initial local implementation handoff.
- Core task/runtime and configuration data models.
- Heuristic task characterization.
- Selective adaptation engine and contraction candidate generator.
- Fake, Ollama and OpenAI-compatible providers.
- Safe workspace and basic tools.
- Runtime verification, records, CLI, tests and benchmark smoke harness.
