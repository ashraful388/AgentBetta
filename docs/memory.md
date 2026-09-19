# Memory

AgentBetta has a durable, **governed** memory so it can remember facts and
preferences across runs. Manage it in the **Memory** view and in
**Settings → Memory**.

## What is remembered

- **Explicit** statements: "remember that I prefer concise answers".
- **Automatic** capture: useful outcomes from **verified** runs (only when
  auto-capture is enabled and privacy mode is off).

Memories are typed: `fact`, `preference`, `episode`, `summary`, with provenance,
importance and usage metadata.

## Retrieval

Relevant memories are injected into a task as background context — never as
instructions. **Memories injected per run** controls how many are retrieved;
optional local Ollama embeddings improve ranking.

## Governance

- Controlled writing (deduplicated on write),
- bounded growth (pruning by importance and age),
- user controls: **add**, **forget**, **clear all**, **open folder**,
- **privacy mode** prevents automatic capture.

## Where it is stored

- Windows: `%LOCALAPPDATA%\AgentBetta\memory\memory.jsonl`
- macOS: `~/Library/Application Support/AgentBetta/memory/memory.jsonl`

## Tips

- Use explicit "remember …" statements for stable preferences.
- Review and prune memory periodically in the **Memory** view.
- Disable memory entirely in Settings if you do not want persistence.
