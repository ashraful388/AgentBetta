# Getting started

AgentBetta is a desktop application. You do **not** need Python or any developer
tools to use it.

## 1. Install AgentBetta

<p align="center">
  <a href="https://github.com/ashraful388/AgentBetta/releases/download/v0.2.0-alpha.3/AgentBetta-0.2.0-alpha.3-Windows-x64-Setup.exe" style="display:inline-block;margin:4px;padding:10px 18px;border:1px solid #3b82f6;border-radius:10px;text-decoration:none;font-weight:700;">
    <img src="assets/agentbetta.png" alt="" width="20" height="20" />
    &nbsp;Download for Windows (.exe)
  </a>
  <span style="display:inline-block;margin:4px;padding:10px 18px;border:1px solid #94a3b8;border-radius:10px;font-weight:700;">
    &nbsp;macOS build coming soon
  </span>
</p>

=== "Windows"

    1. Download `AgentBetta-<version>-Windows-x64-Setup.exe` from the releases page.
    2. Run it. It is a **per-user** install (no administrator rights required).
    3. If Windows SmartScreen warns (the alpha is unsigned), choose **More info → Run anyway**.
    4. Launch **AgentBetta** from the Start Menu or the desktop shortcut.

    Prefer no installation? Use the `...-Portable.zip`: unzip it anywhere and run
    `AgentBetta.exe`. See [Windows installation](windows/installation.md).

=== "macOS"

    1. Build from source using the [`macos/`](../macos) tree, or wait for the Mac
       Studio installer to be added to Releases.
    2. See [macOS building](macos/building.md) and
       [installation](macos/installation.md).

## 2. Choose a model

You can run **local only** (no API key, no cost) or connect a cloud provider.

- **Local (recommended to start):** install [Ollama](https://ollama.com), then
  `ollama pull qwen3:1.7b`. Open **Settings → Local Models**, click
  **Test Ollama**, then **Add selected to catalog**.
- **Cloud / custom:** **Settings → Providers & Models → Add**, pick a preset
  (OpenAI, OpenRouter, DeepSeek, Z.ai, Gemini, LM Studio, vLLM) or enter a custom
  base URL, paste your API key, and click **Test connection**.

API keys are stored in the operating system's credential store (Windows
Credential Manager / macOS Keychain) — never in plain files or logs.

See [Providers & models](providers-and-models.md).

## 3. Run your first task

1. Open **New Task**.
2. Type a task, for example: *"List the .txt files in my Documents folder and
   summarize them."*
3. Pick a **Model** (`Auto (AgentBetta)` is fine) and a **Permissions** profile
   (`Standard` for file work).
4. Press **Run** (or **Enter**). Answer any permission prompt.
5. Read the result in the chat and the details in the **Run Inspector** on the right.

The task is **verified** independently of the model's own claims; look for the
**VERIFIED / NOT VERIFIED** badge.

## 4. Where to go next

- [User guide](user-guide.md) — the interface in detail
- [Permissions](permissions.md) — what the agent may and may not do
- [Browser & web](browser-and-web.md) — live web access
- [Troubleshooting](troubleshooting.md) — if a model or task fails
