<p align="center">
  <img src="docs/assets/agentbetta.png" alt="AgentBetta logo" width="128" />
</p>

<h1 align="center">AgentBetta™</h1>

<p align="center"><strong>An Adaptive AI Nano-Agent for Efficient, Verified Task Completion</strong></p>

AgentBetta is a desktop AI agent that configures its model, context, tools,
permissions, memory and budgets for each task, runs it, **verifies** the
outcome, and adjusts only the dimensions that were insufficient. It never
silently escalates permissions.

> **Status:** `0.2.0-alpha.2` — Windows desktop alpha; macOS build from source.
> Not a stable release; interfaces may change.

## Repository layout

This repository contains **both platforms in one place**, with documentation at
the root:

```
AgentBetta/
├── windows/     # Windows source — buildable tree (Setup EXE + portable ZIP)
├── macos/       # macOS source  — buildable tree (.app / .dmg)
├── docs/        # Documentation (also published as a website via mkdocs.yml)
├── website/     # Standalone landing page
├── assets/      # Logo / icon
├── LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, ...   # project files
└── .github/workflows/   # build-windows, build-macos, docs
```

- **Windows source code →** [`windows/`](windows)
- **macOS source code →** [`macos/`](macos)
- **Documentation →** [`docs/`](docs/index.md)

## Highlights

- **Adaptive configuration** — every run uses an explicit, auditable vector
  `X = ⟨M, C, T, P, Mem, R, τ, I⟩`; adaptation is selective and recorded.
- **Verified outcomes** — a runtime validator, not the model's own claim, decides
  success (`PASS` / `FAIL` / `INSUFFICIENT_EVIDENCE` / `ERROR`).
- **Local & cloud models** — Ollama locally, or any OpenAI-compatible endpoint;
  automatic fallback keeps tasks running.
- **Governed permissions** — profiles, approvals, and hard-denied actions the
  agent can never grant itself; no hidden capability.
- **PC & browser access** — files, shell/processes and real-time web, permission
  controlled and audited.
- **Chats, projects, memory** — saved conversations, project context, and
  governed long-term memory.
- **In-app updates** — from GitHub Releases.

## Install

<p align="center">
  <a href="https://github.com/ashraful388/AgentBetta/releases/download/v0.2.0-alpha.2/AgentBetta-0.2.0-alpha.2-Windows-x64-Setup.exe">
    <img src="docs/assets/agentbetta.png" alt="" width="20" height="20" />
    &nbsp;<b>Download for Windows (.exe)</b>
  </a>
  &nbsp;&nbsp;&nbsp;
  <a href="https://github.com/ashraful388/AgentBetta/releases/download/v0.2.0-alpha.2/AgentBetta-0.2.0-alpha.2-macOS-arm64.dmg">
    <img src="docs/assets/agentbetta.png" alt="" width="20" height="20" />
    &nbsp;<b>Download for macOS (.dmg)</b>
  </a>
</p>

<p align="center"><a href="https://github.com/ashraful388/AgentBetta/releases/tag/v0.2.0-alpha.2">All files (portable ZIP, macOS zip, checksums) →</a></p>

- **Windows 10/11 (x64)** — run the Setup EXE. Per-user, **no Python or admin
  required** (SmartScreen may warn on the unsigned alpha: *More info → Run anyway*).
- **macOS 11+ (Apple silicon)** — open the `.dmg` and drag **AgentBetta** to
  *Applications*; on first launch right-click → **Open**. Or build from
  [`macos/`](macos).

## Quick start

1. Install and launch AgentBetta.
2. Configure a model — **local** (Ollama, no API key) or **cloud/custom**
   (Settings → Providers & Models).
3. **New Task** → type a task → choose a model and permission profile → **Run**.
4. Read the result and the **Run Inspector** (model, configuration, tools,
   permissions, usage, verification).

## Build from source

=== "Windows"

    ```powershell
    cd windows
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -e ".[desktop,browser,http,build]" pillow
    powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
    ```

    Output: `windows\release\windows\<version>\` (Setup EXE, portable ZIP).

=== "macOS"

    ```bash
    cd macos
    python3 -m venv .venv && source .venv/bin/activate
    pip install -e ".[desktop,browser,http,build]" pillow pytest
    playwright install chromium
    bash scripts/build_macos.sh
    ```

    Output: `macos/release/macos/<version>/` (`.zip`, `.dmg`).

## Documentation

Full documentation lives in [`docs/`](docs/index.md) and can be published as a
website with MkDocs (`mkdocs.yml`):

| | |
|---|---|
| [Getting started](docs/getting-started.md) | Install, configure, first task |
| [User guide](docs/user-guide.md) | The desktop interface |
| [Windows installation](docs/windows/installation.md) · [building](docs/windows/building.md) | Windows |
| [macOS installation](docs/macos/installation.md) · [building](docs/macos/building.md) | macOS |
| [Providers & models](docs/providers-and-models.md) | Ollama, cloud, tiers, fallback |
| [Permissions](docs/permissions.md) | Profiles, approvals, hard-deny |
| [Browser & web](docs/browser-and-web.md) | Real-time web access |
| [Memory](docs/memory.md) · [Chats & projects](docs/chats-and-projects.md) | Data |
| [Updates](docs/updates.md) | In-app updates |
| [Architecture](docs/architecture.md) | The scientific core |
| [Troubleshooting](docs/troubleshooting.md) · [FAQ](docs/faq.md) | Help |

## How it works

```text
Task -> characterize -> conservative configuration X0 -> bounded tool loop
     -> verify (independent) -> diagnose insufficient dimension(s)
     -> selectively expand only those -> record -> optional contraction candidates
```

The scientific core is platform-neutral; the GUI, CLI and Python API all call the
same core. The only platform-specific code is
`windows/src/agentbetta/platform/windows/` and
`macos/src/agentbetta/platform/macos/`.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`SPECIFICATION.md`](SPECIFICATION.md).

## License & trademark

MIT © 2026 **Dr. Md. Ashraful Babu** — see [`LICENSE`](LICENSE) and
[docs/license.md](docs/license.md). **AgentBetta™** and the logo are trademarks
of the author; the MIT license does not grant trademark rights.

Third-party components (notably PySide6/Qt, LGPL-3.0) are covered by their own
licenses — see [`LICENSES/`](LICENSES) and
[`docs/windows/THIRD_PARTY_NOTICES.md`](docs/windows/THIRD_PARTY_NOTICES.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) (including a detailed **Agent GUI**
section) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
