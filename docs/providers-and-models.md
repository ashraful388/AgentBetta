# Providers & models

AgentBetta is provider-independent. Configure providers and models in
**Settings → Providers & Models**, **Local Models** and **Model Tiers**.

## Local models (Ollama)

- Default endpoint: `http://127.0.0.1:11434`
- **Settings → Local Models**: **Test Ollama**, **Refresh installed models**,
  **Add selected to catalog**.
- AgentBetta does **not** bundle model weights or Ollama itself.

Pull a model first, e.g.:

```bash
ollama pull qwen3:1.7b
```

## Cloud / OpenAI-compatible

**Settings → Providers & Models → Add**:

| Field | Notes |
|---|---|
| Preset | OpenAI, OpenRouter, DeepSeek, Z.ai/GLM, Gemini, LM Studio, vLLM, or Custom |
| Name | Your label |
| Type | Ollama or OpenAI-compatible |
| Base URL | e.g. `https://api.openai.com/v1` |
| API key | Stored in the OS credential store (never in files/logs) |
| Default model | Used when a model is not chosen explicitly |

Click **Test connection** to verify. **Refresh models** adds the endpoint's
models to the catalog.

!!! note "Test connection vs. real chat"
    An endpoint can list models but still reject a chat request (missing credit,
    unsupported model, outage). AgentBetta surfaces the real error and falls back
    to another configured model — see [Troubleshooting](troubleshooting.md).

## Auto (AgentBetta) and model tiers

`Auto (AgentBetta)` maps the run's model tier to a real model via your mapping:

| Tier | Label |
|---|---|
| 0 | economical |
| 1 | standard |
| 2 | high capability |

Map any configured model to each tier in **Settings → Model Tiers**. In the task
composer you can choose **Auto (AgentBetta)** or a **specific model**.

## Reliability: fallback

If the selected model fails, AgentBetta tries another configured model:

- **local providers first, then cloud**;
- **never cloud** when **Local only** is set;
- in **Auto** mode it also falls back across tiers.

The provider/model actually used is recorded in the Run Inspector and the run
record. Toggle this in **Settings → General → Reliability**.

## Cost

Where a provider returns usage, AgentBetta records tokens and cost per run. You
can enter input/output cost per million tokens on a model profile for cost
tracking.
