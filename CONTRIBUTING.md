# Contributing

Thanks for your interest in AgentBetta. Development is currently led by the
project owner; contributions are welcome via issues and pull requests.

## Repository layout

- `windows/` — Windows source (buildable tree)
- `macos/` — macOS source (buildable tree)
- `docs/` — documentation (published as a website via `mkdocs.yml`)
- `website/` — standalone landing page

The scientific core and the GUI are shared; only the platform layer
(`src/agentbetta/platform/<os>/`) and the packaging differ.

## Ground rules

- Preserve the invariants in [`SPECIFICATION.md`](SPECIFICATION.md): no silent
  permission escalation, selective expansion, observable adaptation, verified
  success, failure retention, local boundary, controlled contraction.
- Add tests for every behavior change. Run them from the platform folder:
  ```bash
  cd windows   # or: cd macos
  python -m pytest
  ```
- Keep the core platform-neutral. Put OS-specific code only in
  `src/agentbetta/platform/`.
- Do not commit secrets, user data (`settings.json`, `chats.json`,
  `projects.json`, run records), or build outputs.
- Keep the GUI a **client of the core** — never duplicate adaptation logic in the
  UI.

---

## The Agent GUI

AgentBetta ships a professional desktop client (PySide6 / Qt 6) that is a client
of the same core used by the CLI and the Python API. This section documents what
the GUI includes, so contributions stay consistent.

### Layout — a three-pane agent console

- **Left — navigation:** New Task, Chats, Projects, Agents, Memory, Settings,
  Guide, About.
- **Center — task console:** chat transcript + composer.
- **Right — Run Inspector:** live run details.

### Task console (chat interface)

- **Chat transcript** of message bubbles: the user's messages on the right, the
  agent's on the left (with the AgentBetta logo avatar), plus inline status lines
  for tool/verification activity. History is preserved per conversation.
- **Per-message actions (icons):**
  - agent messages: **Copy**, **Like**, **Dislike**, **Try again**
  - user messages: **Copy**, **Edit & resend**, **Resend**
  - ratings are saved with the conversation.
- **Thinking indicator** while the model is responding.
- **Composer:** multi-line input (**Enter** to send, **Shift+Enter** for a new
  line), **Attach** files, and a single **Run / Stop** button.
- **Advanced** (collapsed by default): **Local only**, run **Mode**
  (`adaptive` / `fixed` / `wholesale`) and an optional **Context folder**. These
  research/rare options are kept out of the routine path.

### Run Inspector (right panel)

Shows, for the active run: the provider/model actually used (including any
fallback), the executable configuration `X = ⟨M, C, T, P, Mem, R, τ, I⟩`, exposed
tools, allowed / eligible / hard-denied permissions, token/cost usage and wall
time, adaptations performed, and the verification status and reason.

### Other views

- **Chats** — list, preview, open, delete saved conversations.
- **Projects** — group work by folder/context; selecting a project shows all its
  chats.
- **Agents** — the agent identity card, operating contract, dual-plane
  description, agent-class taxonomy, tool risk tiers (L0–L5) and the lifecycle FSM.
- **Memory** — the governed memory fabric (tiered view, add/forget/clear).
- **Settings** — General, Providers & Models, Local Models, Model Tiers, Tools &
  Permissions, Browser & Web, Memory, Privacy & Data, Diagnostics, **User Guide**.
- **Guide** — the in-app documentation.
- **About** — version, developer, license, trademark.

### Dialogs

- **Onboarding** (first run), **Approval** (Allow once / Allow for run / Deny),
  **Update** (release notes + download/install), **Provider** (add/edit).

### Theming and icons

- **Light / Dark / System** only; the accent colour is the AgentBetta logo blue.
- Text is true black in light mode and white in dark mode; heavier weights.
- A built-in **SVG line-icon set** (`desktop/icons.py`), tinted to the theme, at
  a standard size. Buttons and tabs have visible borders and accent highlight
  states.

### Updates

The header **Updates** button checks GitHub Releases and highlights when a newer
version is available; Settings controls the channel and the `owner/repo` source.

### Where the GUI code lives

```
src/agentbetta/desktop/
  app.py            # entry point (theme, window icon, AppUserModelID)
  main_window.py    # three-pane shell, header, navigation, update button
  theme.py          # design tokens + Qt stylesheet + document stylesheet
  icons.py          # inline SVG icon set
  guide.py          # in-app user guide content
  chats.py          # persistent conversations
  projects.py       # project store
  assets.py         # logo / icon access
  services.py       # application service layer (no Qt; testable headlessly)
  workers.py        # QThread workers (runs, background calls)
  views/            # task, chats, projects, agents, memory, settings, guide, about
  widgets/          # chat transcript, inspector, approval/update/onboarding dialogs, cards
```

### GUI guidelines for contributors

- Keep the main task screen minimal: model, permissions, attach, Run/Stop.
- Put advanced/research controls under **Advanced** or in Settings.
- The GUI must **not** import core policy/adaptation logic directly — go through
  the service layer and the core controller.
- Keep the GUI responsive: run work on `QThread` workers; never block the UI.
- Never display secrets; redact provider errors.
- Preserve light/dark parity and the shared design tokens.

## Reporting issues

Open a GitHub issue with steps to reproduce, your OS, the model/provider, and the
relevant **Run Inspector** details (the run record is the evidence source).
