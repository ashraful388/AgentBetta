# AgentBetta™

**An Adaptive AI Nano-Agent for Efficient, Verified Task Completion**

AgentBetta is a desktop AI agent that configures its model, context, tools,
permissions, memory and budgets for each task, runs it, **verifies** the
outcome, and adjusts only the dimensions that were insufficient. It never
silently escalates permissions.

> **Status:** `0.2.0-alpha.1` — Windows desktop alpha (macOS build from source).
> Not a stable release; interfaces may change.

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

**Windows 10/11 (x64)** — download `AgentBetta-<version>-Windows-x64-Setup.exe`
from the [releases page](../../releases) and run it. Per-user, **no Python or
admin required**. A portable ZIP is also available.

**macOS 11+** — build the `.app`/`.dmg` on a Mac (or use the CI build); see the
macOS docs.

## Quick start

1. Install and launch AgentBetta.
2. Configure a model — **local** (Ollama, no API key) or **cloud/custom**
   (Settings → Providers & Models).
3. **New Task** → type a task → choose a model and permission profile → **Run**.
4. Read the result and the **Run Inspector** (model, configuration, tools,
   permissions, usage, verification).

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
same core. Platform-specific code lives only in
`src/agentbetta/platform/windows/` and `.../macos/`.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) and [`SPECIFICATION.md`](SPECIFICATION.md).

## Run from source

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[desktop,browser]"
agentbetta-gui
```

## Build the installer

See [Windows building](docs/windows/building.md). In short:

```powershell
pip install -e ".[desktop,browser,build]" pillow
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

## License & trademark

MIT © 2026 **Dr. Md. Ashraful Babu** — see [`LICENSE`](LICENSE) and
[docs/license.md](docs/license.md). **AgentBetta™** and the logo are trademarks
of the author; the MIT license does not grant trademark rights.

Third-party components (notably PySide6/Qt, LGPL-3.0) are covered by their own
licenses — see [`LICENSES/`](LICENSES) and
[`docs/windows/THIRD_PARTY_NOTICES.md`](docs/windows/THIRD_PARTY_NOTICES.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).
