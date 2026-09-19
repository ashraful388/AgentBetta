# Windows installation

## Requirements

- Windows 10 or 11, **x64**
- No Python, no Git, no developer tools
- For web/browser features: **Microsoft Edge** (preinstalled on Windows 10/11)
- Optional: **Ollama** for local models (installed separately)

## Install (Setup EXE)

1. Download `AgentBetta-<version>-Windows-x64-Setup.exe`.
2. Run it. It installs **per user** — **no administrator rights** are required.
3. It creates a Start Menu entry and a **desktop shortcut** (AgentBetta icon).
4. If SmartScreen warns (the alpha is unsigned): **More info → Run anyway**.
5. Launch **AgentBetta**.

The installer does **not** delete your data on uninstall; run history and
credentials are preserved unless you choose to remove them.

## Portable (no install)

Unzip `AgentBetta-<version>-Windows-x64-Portable.zip` anywhere and run
`AgentBetta.exe`. Your data still lives under your user profile (see below).

## Verify the download

Compare the file's SHA-256 with `SHA256SUMS.txt`:

```powershell
Get-FileHash .\AgentBetta-<version>-Windows-x64-Setup.exe -Algorithm SHA256
```

## First run

1. **Settings → Local Models** (Ollama) or **Providers & Models** (cloud).
2. **New Task** → type a task → choose model + permissions → **Run**.

See [Getting started](../getting-started.md).

## Data locations

| Purpose | Path |
|---|---|
| Settings | `%APPDATA%\AgentBetta\settings.json` |
| Chats | `%LOCALAPPDATA%\AgentBetta\chats.json` |
| Logs | `%LOCALAPPDATA%\AgentBetta\logs\` |
| Cache | `%LOCALAPPDATA%\AgentBetta\cache\` |
| Browser profile | `%LOCALAPPDATA%\AgentBetta\browser\profile` |
| Run records | `%USERPROFILE%\Documents\AgentBetta\runs\` |
| Secrets | Windows Credential Manager |

## Uninstall

Use **Start Menu → Uninstall AgentBetta**, or *Settings → Apps → AgentBetta*.
Application files are removed; your settings, chats and credentials are kept.

To remove everything, also delete `%APPDATA%\AgentBetta`,
`%LOCALAPPDATA%\AgentBetta`, `Documents\AgentBetta`, and the stored credentials
in Credential Manager (service **AgentBetta**).
