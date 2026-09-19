"""Optional local embeddings via Ollama.

Used only when the user enables embeddings (Settings ▸ Memory). If the local
embedding model is unavailable the memory layer falls back to keyword retrieval;
it never calls a cloud embedding provider in local-only mode.
"""

from __future__ import annotations


class OllamaEmbedder:
    def __init__(self, model: str = "nomic-embed-text",
                 base_url: str = "http://127.0.0.1:11434", timeout: int = 30) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def embed(self, text: str) -> list[float] | None:
        if not text or not text.strip():
            return None
        try:
            from agentbetta.providers.http import post_json

            data = post_json(
                f"{self.base_url}/api/embeddings",
                {"model": self.model, "prompt": text},
                timeout=self.timeout,
            )
        except Exception:
            return None
        embedding = data.get("embedding") if isinstance(data, dict) else None
        if not embedding:
            return None
        try:
            return [float(value) for value in embedding]
        except (TypeError, ValueError):
            return None


__all__ = ["OllamaEmbedder"]
