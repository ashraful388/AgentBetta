# AgentBetta™

**An Adaptive AI Nano-Agent for Efficient, Verified Task Completion**

AgentBetta is a desktop AI agent that configures its model, context, tools,
permissions, memory and budgets for each task, runs it, **verifies** the
outcome, and adjusts only the dimensions that were insufficient. It never
silently escalates permissions.

- **Windows:** install with the Setup EXE (no Python required) — see [Windows installation](windows/installation.md).
- **macOS:** build the `.app`/`.dmg` from source on a Mac — see [macOS installation](macos/installation.md).
- **Providers:** local (Ollama) and cloud / OpenAI-compatible — see [Providers & Models](providers-and-models.md).
- **Safety:** permission profiles, hard-denied actions, approvals — see [Permissions](permissions.md).

## What makes it different

AgentBetta models every run as an explicit, auditable configuration vector
`X = ⟨M, C, T, P, Mem, R, τ, I⟩` and closes the loop:

1. characterize the task → 2. conservative initial configuration → 3. bounded
tool loop → 4. independent verification → 5. diagnose the insufficient
dimension → 6. selectively expand only that dimension → 7. record every
adaptation → 8. propose leaner configurations after verified success.

See [Architecture](architecture.md) for details.

## Documentation

| | |
|---|---|
| [Getting started](getting-started.md) | Install, configure a model, run your first task |
| [User guide](user-guide.md) | The desktop interface, chats, actions |
| [Providers & models](providers-and-models.md) | Ollama, cloud, tiers, Auto, fallback |
| [Permissions](permissions.md) | Profiles, approvals, hard-deny |
| [Browser & web](browser-and-web.md) | Real-time web access |
| [Memory](memory.md) | Durable, governed memory |
| [Chats & projects](chats-and-projects.md) | Conversations and project context |
| [Updates](updates.md) | In-app updates from GitHub Releases |
| [Troubleshooting](troubleshooting.md) | Fix common problems |
| [FAQ](faq.md) | Frequently asked questions |
| [Architecture](architecture.md) | The scientific core |
| [License](license.md) | MIT + third-party notices |

## License

MIT © 2026 Dr. Md. Ashraful Babu. See [License](license.md).
