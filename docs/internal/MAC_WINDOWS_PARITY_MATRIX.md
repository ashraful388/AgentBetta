# AgentBetta — macOS ↔ Windows Parity Matrix

**Status:** PENDING macOS REFERENCE
**Date:** 2026-09-13
**Owner:** OpenCode (Windows)

The macOS AgentBetta reference application/source has **not been supplied** in the
project folder. Per `OPENCODE_WINDOWS_BUILD_HANDOFF.md` §3.2 and §W8, this does
**not** block the Windows build. This matrix records the current Windows
implementation so it can be compared dimension-by-dimension when the Mac
reference becomes available.

## Reference availability

| Item | Status |
|---|---|
| macOS application binary | Not supplied |
| macOS source code | Not supplied |
| Where expected | Same Google Drive project folder |
| Blocking? | No — Windows implementation completed independently |

## Parity comparison dimensions

| Dimension | Windows (current implementation) | macOS reference | Difference / action |
|---|---|---|---|
| First-run onboarding | `OnboardingDialog`: choose Ollama (detect + list models) or cloud/custom provider; default permission profile; "configure later" path. Shown only when no provider/model configured. | Not inspected | Pending |
| Task composer | `TaskView`: task editor, optional workspace, attach files, provider/model combo, permission profile, run mode, Local-only toggle. No workspace required. | Not inspected | Pending |
| Provider/model selection | Combo: `Auto (AgentBetta)` plus configured models. Auto routes by `model_tier` to real mapped models. | Not inspected | Pending |
| Provider settings | Settings ▸ Providers & Models: add/edit/remove/enable, type/preset, base URL, default model, timeout, cloud/local, secure API key (Credential Manager), Test connection, Refresh models. | Not inspected | Pending |
| Local-model settings | Settings ▸ Local Models: Ollama endpoint, test, refresh installed models, add to catalog; custom OpenAI-compatible endpoint via provider editor. | Not inspected | Pending |
| Task attachments | `Attach files...` adds inputs; absolute/out-of-workspace inputs are read via global tools when permitted. | Not inspected | Pending |
| Task execution status | Status label + streaming run events (attempts, model calls, tools, verification, adaptations); no GUI freeze (QThread worker). | Not inspected | Pending |
| Result rendering | Markdown output, verified status footer, copy, run details panel, artifact paths. | Not inspected | Pending |
| Run history | Persistent JSON run records; History table (time, task, status, provider/model, duration, adaptations); open, rerun, copy, open folder, clear. | Not inspected | Pending |
| Permission prompts | `ApprovalDialog` for high-risk actions: tool, permission, risk, reason, arguments; Allow once / Allow for run / Deny. | Not inspected | Pending |
| PC-access controls | Permission profiles Safe / Standard / Extended / Full Computer, inspectable capabilities, hard-denied rules. | Not inspected | Pending |
| Browser/web controls | Settings ▸ Browser & Web: enable, engine (Edge/Chromium), visible toggle, download directory, clear profile data. | Not inspected | Pending |
| Logs/diagnostics | Settings ▸ Diagnostics: versions, paths, secret-store and browser status, open logs folder; rotating logs. | Not inspected | Pending |
| Settings navigation | Single Settings surface with 8 tabs; Save applies. | Not inspected | Pending |
| Visual hierarchy & terminology | Left nav (New Task, History, Settings, About); product identity and scientific terminology preserved (configuration, adaptation, verification). | Not inspected | Pending |

## Windows-only platform decisions (expected, not parity defects)

- Windows Credential Manager for secrets (macOS would use Keychain).
- Windows per-user paths (`%APPDATA%`, `%LOCALAPPDATA%`, `Documents`).
- Microsoft Edge through Playwright as the preferred browser engine.
- PowerShell and Windows process/ACL/UAC semantics.
- Inno Setup installer + PyInstaller `onedir` bundle.

## Next action

When the macOS reference is supplied: inspect its UI/behavior, fill the
"macOS reference" and "Difference / action" columns, and implement any
appropriate Windows parity improvements. Do not import platform-specific Mac
code.
