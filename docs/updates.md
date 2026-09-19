# Updates

AgentBetta updates itself from **GitHub Releases**.

## In the app

- The header **Updates** button checks for a newer release on startup.
- When a release is available the button becomes **Update `<version>`**
  (highlighted) — click it to review release notes and update in place.
- On Windows the Setup EXE runs silently and the app restarts.
- On macOS the `.dmg`/`.zip` matched to your CPU is downloaded and applied.

## Settings → General

- **Check for updates on startup**
- **Channel:** Stable / Pre-release
- **Update source:** `owner/repo` on GitHub
- **Check for updates now**

## For maintainers: publishing a release

1. Ensure the update source (`owner/repo`) is set in the app settings.
2. Push a tag, e.g. `v0.2.1`:
   ```bash
   git tag v0.2.1 && git push origin v0.2.1
   ```
3. The GitHub Actions workflow builds the installers and **publishes a Release**
   with the assets the updater downloads:
   - Windows: `AgentBetta-<version>-Windows-x64-Setup.exe`, `...-Portable.zip`, `SHA256SUMS.txt`
   - macOS: `AgentBetta-<version>-macOS-<arch>.zip` / `.dmg`, `SHA256SUMS.txt`
4. Mark a release **pre-release** to require the *Pre-release* channel.

!!! note
    `Stable` uses GitHub's "latest release" endpoint, so keep experimental
    releases marked as pre-releases.
