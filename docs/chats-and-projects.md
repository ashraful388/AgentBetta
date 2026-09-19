# Chats & projects

## Chats

Every conversation is saved automatically. Open **Chats** to:

- list all conversations (title, project, message count, updated time, status),
- preview a conversation,
- **Open chat** to continue it in **New Task**,
- **Delete** a conversation,
- start a **New chat**.

Messages carry their **likes/dislikes** and the run status (verified / not
verified).

## Projects

A **project** is optional task context: a name plus a folder (and optionally a
default permission profile and preferred model).

- Create/manage projects in the **Projects** view.
- Select a project to see **all chats associated with it**; double-click a chat
  to resume it.
- **Use in New Task** loads the project as the task's context.

A project folder is **convenience context, not a security boundary** — file
access is still governed by the permission profile.

## Where chats are stored

- Windows: `%LOCALAPPDATA%\AgentBetta\chats.json`
- macOS: `~/Library/Application Support/AgentBetta/chats.json`

Projects: `projects.json` in the same directory.

## Run records

Each execution is also written as an auditable run record (task, model,
configuration, adaptations, tools, permissions, verification, usage):

- Windows: `Documents\AgentBetta\runs`
- macOS: `~/Documents/AgentBetta/runs`

Open the runs folder from **Settings → Privacy & Data**.
