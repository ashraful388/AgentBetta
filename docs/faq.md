# FAQ

**Do I need Python or any developer tools?**
No. On Windows, install with the Setup EXE. On macOS, install the built `.app`
(or build it once on a Mac). End users need neither Python nor Git.

**Do I need an API key?**
No. AgentBetta works fully offline with a local **Ollama** model. Cloud
providers are optional.

**Where are my API keys stored?**
In the operating system credential store — **Windows Credential Manager** or the
**macOS Keychain**. They are never written to settings files, logs, or run
records.

**Does it use my Chrome/Edge profile or passwords?**
No. Web automation uses a **dedicated AgentBetta browser profile**; it never
reads your personal browser profile, cookies or saved passwords.

**Can it access my whole PC?**
It can read/write local files, run processes/shell and use the browser, all
governed by the permission profile. **Full Computer** is broad but still subject
to OS security, UAC/TCC, and hard-denied rules — and every action is audited.

**What does "verified" mean?**
A runtime validator — not the model's own claim — decides success. Statuses are
`PASS`, `FAIL`, `INSUFFICIENT_EVIDENCE`, `ERROR`.

**Can the agent give itself more permissions?**
No. It may only activate permissions from the pre-approved **eligible** set. A
**hard-denied** permission can never be activated.

**Which models are supported?**
Any local Ollama model and any OpenAI-compatible endpoint (OpenAI, OpenRouter,
DeepSeek, Z.ai/GLM, Gemini, LM Studio, vLLM, custom).

**Why did my model fail and the task still finish?**
AgentBetta fell back to another configured model (local first). The Run
Inspector shows the provider/model actually used.

**Is it free?**
The software is **MIT licensed** (free to use and modify). Cloud model usage is
billed by your provider; local models are free.

**How do I update?**
The header **Updates** button, driven by GitHub Releases. See [Updates](updates.md).

**Where is my data?**
See [Chats & projects](chats-and-projects.md) and [Memory](memory.md) for paths.
