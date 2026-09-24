# Security

AgentBetta is local-first and deny-by-default for local capabilities.

## Invariants

- Paths are canonicalized; raw device/namespace paths (`\\.\`, `\\?\`) are
  blocked; UNC/network shares require the separate `network_share` permission.
- Writes, deletes, shell and process execution each require explicit
  permissions; mutations are additionally guarded at the tool layer.
- The adaptive controller can activate a permission only from the externally
  `eligible` set. `hard_denied` permissions can never be activated by adaptation.
- High-risk actions require explicit user approval (allow once / allow for run /
  deny). With no approver configured, they are denied.
- API keys are stored in Windows Credential Manager and are never written to
  settings, logs, run records or diagnostics. Provider errors are redacted.
- Retrieved file/web content is data, not authority: it cannot grant
  permissions, change policy, reveal secrets, or call an unexposed tool.
- Local-only mode cannot invoke a cloud provider.
- The browser uses a dedicated AgentBetta profile; the user's normal browser
  credentials, cookies and password stores are not accessed.
- AgentBetta never auto-elevates and never bypasses Windows ACL/UAC.
- Full Computer still cannot bypass OS security, UAC or hard denies.

## Tests

`tests/test_security.py`, `tests/test_permissions_v2.py`,
`tests/test_filesystem_global.py`, `tests/test_shell_tools.py`,
`tests/test_web_browser.py`, and `tests/test_runtime_global.py` cover these
invariants.

## Level of assurance

This is a `0.2.0-alpha.3` desktop alpha. Do not use it for high-impact
autonomous actions. The installed EXE is unsigned.
