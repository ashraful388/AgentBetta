"""The in-app User Guide / documentation content."""

from __future__ import annotations

USER_GUIDE = """
# AgentBetta — User Guide

AgentBetta is an adaptive AI agent that configures its model, context, tools,
permissions, memory and budgets for each task, runs it, **verifies** the result,
and adjusts only what was insufficient. It never silently escalates permissions.

## 1. Getting started
1. Open **Settings ▸ Providers & Models** (or **Local Models**) and configure a
   model: local **Ollama** needs no API key, or add a cloud/OpenAI-compatible
   provider with a key.
2. Go to **New Task**, type what you want done, pick a **Model** and a
   **Permissions** profile, then press **Run** (or **Enter**).
3. Answer any permission prompt, then read the result and the **Run Inspector**
   on the right (model, configuration, tools, permissions, usage, verification).

## 2. Models
- **Auto (AgentBetta)** — the model is chosen per task by the adaptive engine
  using your **Model Tiers** mapping (Tier 0 economical → Tier 2 high capability).
- **Specific model** — pins one configured model for the run.
- **Local only** — never call a cloud provider (under **Advanced**).
- **Ollama** — detected at `http://127.0.0.1:11434`; **Refresh** lists installed
  models; **Add selected to catalog**.
- **Cloud / custom** — add a provider (OpenAI, OpenRouter, DeepSeek, Z.ai, Gemini,
  LM Studio, vLLM or a custom base URL), enter the key, **Test connection**.

## 3. Running tasks
- The composer accepts multi-line text. **Enter** sends, **Shift+Enter** adds a line.
- **Attach** adds files as task inputs.
- **Advanced** reveals **Local only**, the run **Mode** and an optional
  **Context folder** (context is convenience, never a security boundary).
- **Mode**: `adaptive` (default), `fixed` (no adaptation), `wholesale`
  (escalate everything) — research/ablation modes.
- The **Run / Stop** button runs the task and stops it while it is working.
- Conversations are saved automatically; find them under **Chats**.

## 4. Permissions & approvals
- **Safe / Read-Only** — read files and public pages; no writes or shell.
- **Standard** — read/write user files, browse and interact; downloads with approval.
- **Extended** — add delete, move, process launch and bounded shell.
- **Full Computer** — all supported local/browser capabilities you select; still
  subject to OS security and hard-denied rules.
- Adaptive expansion may only activate permissions from the profile's *eligible*
  set; **hard-denied** permissions can never be granted by the agent.
- High-risk actions prompt: **Allow once / Allow for run / Deny**. A denial is
  final for that run.

## 5. Browser & web
- Web search/browsing uses a **dedicated AgentBetta browser profile** (Edge on
  Windows, Chromium on macOS) — never your personal Chrome/Edge profile, cookies
  or passwords.
- Settings ▸ **Browser & Web**: enable/disable, engine, show the window,
  download folder, clear browser data, allow interaction/downloads.
- `browser_read`, `browser_interact` and `browser_download` are separate permissions.

## 6. Memory
- AgentBetta can remember durable facts and preferences (**Memory** view).
- Verified runs auto-capture useful outcomes; you can add/forget/clear entries.
- **Memories injected per run** controls retrieval; optional local Ollama
  embeddings improve ranking.

## 7. Chats & projects
- **Chats** lists every conversation; open one to continue it.
- **Projects** group work by folder/context; select a project to see its chats.

## 8. Updates
- The header **Updates** button checks GitHub Releases on startup and highlights
  when a newer version exists; click it to review notes and update in place.
- Settings ▸ **General**: check on startup, **Stable/Pre-release** channel, and
  the **Update source** (`owner/repo`).

## 9. History & run records
- Every run is stored as an auditable record (**History** view): task, provider,
  model, configuration, adaptations, tools, permissions, verification, usage.
- Open a run for detail, **Rerun**, **Copy result**, or **Export report**.
- Records live in `Documents/AgentBetta/runs` (Windows) or
  `~/Documents/AgentBetta/runs` (macOS).

## 10. Privacy & data
- **Privacy mode** redacts task text in records.
- API keys live only in the OS credential store (Windows Credential Manager /
  macOS Keychain), never in settings files or logs.
- Settings ▸ **Privacy & Data**: clear history, delete stored keys, export a
  redacted diagnostic bundle.

## 11. Troubleshooting
- **Model errors / connection failed** — Settings ▸ Providers: **Test connection**;
  check the endpoint and key; for Ollama ensure the service is running.
- **Task not verified** — read the Inspector: a permission denial, missing tool or
  budget limit is reported there; widen the permission profile or use Adaptive.
- **Browser does nothing** — ensure the browser is enabled and Edge/Chromium is
  available; install the Chromium runtime on macOS if needed.
- **Console windows (Windows)** — none should appear; report if any do.
- Logs: Settings ▸ **Diagnostics** → open the logs folder.

## 12. Where things live
| | Windows | macOS |
|---|---|---|
| Settings | `%APPDATA%\\AgentBetta\\settings.json` | `~/Library/Application Support/AgentBetta/settings.json` |
| Chats | `%LOCALAPPDATA%\\AgentBetta\\chats.json` | `~/Library/Application Support/AgentBetta/chats.json` |
| Logs | `%LOCALAPPDATA%\\AgentBetta\\logs` | `~/Library/Logs/AgentBetta` |
| Run records | `Documents\\AgentBetta\\runs` | `~/Documents/AgentBetta/runs` |
| Secrets | Credential Manager | Keychain |
"""

__all__ = ["USER_GUIDE"]
