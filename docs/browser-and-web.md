# Browser & web

AgentBetta can access the internet for real-time information.

## Dedicated browser profile

Web automation uses a **dedicated AgentBetta browser profile**:

- Windows: Microsoft Edge (`msedge`) via Playwright, Chromium fallback.
- macOS: Chromium (Playwright); Edge for Mac is optional.

It **never** uses your personal Chrome/Edge profile, cookies, or saved
passwords. The profile lives in AgentBetta's own data directory and can be
cleared from Settings.

## Tools

| Tool | Permission |
|---|---|
| `http_fetch` | `network_http` |
| `browser_open`, `browser_search`, `browser_extract_text`, `browser_screenshot`, `browser_back`, `browser_close` | `browser_read` |
| `browser_click`, `browser_fill`, `browser_select` | `browser_interact` |
| `browser_download` | `browser_download` |

## Settings → Browser & Web

- enable/disable browser tools
- preferred engine (Edge / Chromium)
- show the browser window
- download directory
- clear AgentBetta browser data
- allow interaction / allow downloads

## Safety

- Browser access is **read / interact / download** separated by permission.
- Potential external side effects (form submission, downloads) require explicit
  approval unless a task-specific policy says otherwise.
- AgentBetta does not bypass CAPTCHAs, anti-bot measures, paywalls or
  authentication controls.

## Requirements

- Windows: Microsoft Edge (preinstalled on Windows 10/11) or Chromium.
- macOS: run `playwright install chromium` once, or install Edge for Mac.
