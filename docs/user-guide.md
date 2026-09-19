# User guide

The AgentBetta desktop client is a three-pane console: **navigation** on the
left, the **task console** in the centre, and the **Run Inspector** on the right.

## Navigation

| Item | Purpose |
|---|---|
| **New Task** | Chat-style task console |
| **Chats** | All saved conversations |
| **Projects** | Group work by folder/context; see each project's chats |
| **Agents** | Agent identity, operating contract, tool risk tiers, lifecycle |
| **Memory** | Durable, governed memory |
| **Settings** | Providers, models, permissions, browser, memory, privacy, diagnostics, user guide |
| **Guide** | This documentation, in-app |
| **About** | Version, developer, license, trademark |

## The task console

- **Composer:** type your task. **Enter** sends, **Shift+Enter** adds a new line.
- **Attach:** add files as task inputs.
- **Advanced:** reveals **Local only**, the run **Mode** (`adaptive` / `fixed` /
  `wholesale`) and an optional **Context folder**.
- **Run / Stop:** one button — it runs the task and stops it while it is working.
- **New chat:** starts a fresh conversation.

### Message actions

Every answer has icon actions:

| Action | Meaning |
|---|---|
| **Copy** | Copy the message |
| **Like / Dislike** | Rate the answer (saved with the chat) |
| **Try again** | Re-run the last request |
| **Edit & resend** (your messages) | Put the message back in the composer to edit |
| **Resend** (your messages) | Send the message again |

While a model is working you will see an **“AgentBetta is thinking…”** indicator.

## Run Inspector

Shows, for the active run:

- the model/provider actually used (including any fallback),
- the executable configuration `X = ⟨M, C, T, P, Mem, R, τ, I⟩`,
- the tools exposed and the permissions allowed / eligible / hard-denied,
- token/cost usage and wall time,
- adaptations performed,
- the verification status and reason.

## Chats and projects

Conversations are saved automatically. Open **Chats** to list, preview, open or
delete them. Assign a **context folder** (under **Advanced**) or open a chat from
a **Project** to associate it with that project. See [Chats & projects](chats-and-projects.md).

## Appearance

- **Theme:** System / Light / Dark (header button or Settings).
- The accent colour follows the AgentBetta logo blue.

## Keyboard

| Key | Action |
|---|---|
| `Enter` | Send the task |
| `Shift+Enter` | New line in the composer |
