# macOS installation

AgentBetta for macOS is built from source (a prebuilt `.dmg` may also be
available from the releases page).

## Requirements

- macOS 11 (Big Sur) or later — Intel or Apple silicon
- No Python needed for the built `.app`; building requires Python 3.11/3.12

## Install a built app

1. Download `AgentBetta-<version>-macOS-<arch>.dmg` (or `.zip`).
   `<arch>` is `arm64` (Apple silicon) or `x86_64` (Intel).
2. Open the dmg and drag **AgentBetta** into **Applications**.
3. First launch (unsigned alpha): right-click the app → **Open**, or:
   ```bash
   xattr -dr com.apple.quarantine /Applications/AgentBetta.app
   ```

## Build it yourself

See [Building on macOS](building.md). The result is
`dist/AgentBetta.app` plus `release/macos/.../*.dmg` and `*.zip`.

## First run

1. **Settings → Local Models** (Ollama) or **Providers & Models** (cloud).
2. **New Task** → type a task → choose model + permissions → **Run**.

For browser features, run `playwright install chromium` once (or install
Microsoft Edge for Mac and select `msedge`).

## Data locations

| Purpose | Path |
|---|---|
| Settings | `~/Library/Application Support/AgentBetta/settings.json` |
| Chats | `~/Library/Application Support/AgentBetta/chats.json` |
| Logs | `~/Library/Logs/AgentBetta/agentbetta.log` |
| Cache | `~/Library/Caches/AgentBetta/` |
| Browser profile | `~/Library/Application Support/AgentBetta/browser/profile` |
| Run records | `~/Documents/AgentBetta/runs/` |
| Secrets | macOS Keychain |

## Uninstall

Drag **AgentBetta** from **Applications** to the Trash, then optionally remove
`~/Library/Application Support/AgentBetta`, `~/Library/Logs/AgentBetta`,
`~/Library/Caches/AgentBetta`, `~/Documents/AgentBetta`, and the Keychain entry
(service **AgentBetta**).
