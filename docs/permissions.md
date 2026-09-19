# Permissions & approvals

AgentBetta is **deny-by-default** and never silently escalates permissions.

## Permission profiles

Choose a profile in the task composer (or set a default in Settings).

| Profile | Allows | Denies |
|---|---|---|
| **Safe / Read-Only** | Read files, public web pages | Writes, deletes, shell, process launch |
| **Standard** | Read/write user files, browse and interact; downloads with approval | Destructive delete, unrestricted shell |
| **Extended** | Read/write/move/delete, process launch, bounded shell, full browser | — |
| **Full Computer** | All supported local/browser/desktop capabilities you select | Still subject to OS security and hard-denied rules |

You can inspect the exact capabilities of each profile in
**Settings → Tools & Permissions**.

## allowed / eligible / hard_denied

Every permission has one of three states:

- **allowed** — granted for the run.
- **eligible** — the adaptive engine may activate it if a task requires it.
- **hard_denied** — the agent can **never** activate it, regardless of adaptation.

The adaptive engine may only move a permission from *eligible* to *allowed*. It
can never remove a *hard_denied*.

## Approvals

High-risk actions prompt a dialog showing the exact tool, arguments, permission,
risk and reason, with three choices:

- **Allow once**
- **Allow for run**
- **Deny** (final for that run — the agent will not re-prompt for the same action)

Examples that require approval: deleting files, overwriting an existing
non-temporary file, state-changing shell commands, launching installers,
submitting a browser form with an external side effect.

## No hidden capability

A model may only use tools **exposed by the current configuration**. A tool call
outside the configuration is rejected and recorded — it is never executed, even
if a permission would otherwise allow it.

## Operating system limits

AgentBetta operates with your current user's OS privileges. It does not bypass
Windows UAC/NTFS ACLs or macOS TCC prompts, and it never auto-elevates.
