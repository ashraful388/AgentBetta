# Troubleshooting

## The task failed with a provider error

AgentBetta shows the **real** provider error (for example
`HTTP 400: credit insufficient balance`, `Requested model … not supported`,
`HTTP 503`, or a timeout).

1. Open **Settings → Providers & Models**, select the provider, **Test connection**.
2. Check the endpoint, API key, account credit/balance, and the exact model id.
3. Prefer a **local Ollama** model if the cloud endpoint is unavailable.
4. AgentBetta retries transient errors and **falls back** to another configured
   model automatically (Settings → General → Reliability).

!!! tip "Test connection can pass while chat fails"
    `/models` may work while `/chat/completions` rejects the model or your
    account has no credit. The run error message tells you which.

## Ollama not detected

- Ensure Ollama is installed and running: `ollama list`.
- Check the endpoint (default `http://127.0.0.1:11434`) in **Settings → Local Models**.
- Pull a model: `ollama pull qwen3:1.7b`.

## Browser does nothing / no browser

- Windows: Microsoft Edge should be present; otherwise install Chromium.
- macOS: run `playwright install chromium`, or install Microsoft Edge for Mac
  and select `msedge` in **Settings → Browser & Web**.
- Ensure the browser is **enabled** and the required permission
  (`browser_read` / `browser_interact` / `browser_download`) is allowed.

## Task is NOT VERIFIED

Open the **Run Inspector**: it reports the reason — a permission denial, a
missing tool, a budget/time limit, or a model insufficiency. Widen the
permission profile, choose a stronger model/tier, or use **Adaptive** mode.

## Windows SmartScreen warning

The alpha installer is **unsigned**. Choose **More info → Run anyway**.

## macOS Gatekeeper blocks the app

Right-click the app → **Open**, or:

```bash
xattr -dr com.apple.quarantine /Applications/AgentBetta.app
```

## Console windows flash on Windows

They should not. If any appear, note which action caused them and report it.

## Reset or clean data

- **Settings → Privacy & Data**: clear history, delete stored API keys, export a
  redacted diagnostic bundle.
- **Settings → Browser & Web**: clear AgentBetta browser data.

## Logs and diagnostics

**Settings → Diagnostics** shows versions and paths and can open the logs folder.

- Windows: `%LOCALAPPDATA%\AgentBetta\logs`
- macOS: `~/Library/Logs/AgentBetta`
