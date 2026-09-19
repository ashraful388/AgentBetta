# Architecture

```text
CLI / Python API / Windows GUI (PySide6)
      |
      v
Desktop Service Layer (settings, secrets, providers, events, history)
      |
      v
  AgentBetta Runtime
      |
      +--> Task Characterizer
      +--> Adaptive Configuration Engine
      |      +--> Initial Policy
      |      +--> Insufficiency Diagnoser
      |      +--> Selective Expansion
      |      +--> Contraction Candidate Generator
      |      +--> Frontier Store
      |
      +--> Tool Loop (model -> tool request -> permission/approval -> execute -> observation -> model)
      |      +--> Provider Registry
      |      |      +--> FakeProvider
      |      |      +--> OllamaProvider
      |      |      +--> OpenAICompatibleProvider
      |      |      +--> TieredProvider (Auto model-tier routing)
      |      +--> Tool Registry
      |             +--> workspace tools
      |             +--> global Windows filesystem tools
      |             +--> shell / process tools
      |             +--> browser / web tools
      |      +--> Permission layer (profiles, hard-deny, approvals)
      |
      +--> Runtime Validators
      |
      `--> Run Recorder
```

The desktop application is a client of the same core APIs used by the CLI and
the Python API. The GUI does not implement a separate agent engine or adaptation
policy.

Key packages:

- `core/` — models, runtime orchestration, characterization, tool loop, events,
  cancellation, controller.
- `policy/` — initial policy, diagnosis, selective expansion, contraction.
- `permissions/` — typed permission vocabulary, profiles, approvals.
- `providers/` — normalized `chat` interface and adapters.
- `tools/` — registry, schemas, guards, filesystem/shell/process/browser/web.
- `settings/` — secret-free settings store, secret store, provider/model profiles.
- `platform/windows/` — paths, credentials, filesystem, processes.
- `desktop/` — PySide6 GUI (views, widgets, workers, services).
- `records/` — run/frontier JSON persistence.

The desktop GUI, when packaged, must not depend on the source tree; it is bundled
with PyInstaller (one-directory) and installed per user.
