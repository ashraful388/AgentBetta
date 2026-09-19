# AgentBetta Vision

AgentBetta is a standalone AI-agent framework that attempts to allocate only the configuration a task needs, verifies the result, and adapts when evidence shows that the initial allocation is insufficient.

The framework is general-purpose and model-agnostic. Its public implementation should support local and cloud models, controlled local tools, auditable run records, reproducible benchmarks, and a stable Python/CLI interface.

The scientific target is not a generic tool-calling loop. The central research object is the executable configuration of the agent and how that configuration changes in response to verified evidence.
