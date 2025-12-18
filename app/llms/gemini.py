from __future__ import annotations

# Stub adapter (kept for future).
# The primary integration path is OpenAI-compatible providers.

from dataclasses import dataclass


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model: str = "gemini-1.5-pro"


class GeminiClient:
    def __init__(self, config: GeminiConfig) -> None:
        self._config = config

    async def chat(self, *, system: str, user: str) -> str:
        raise NotImplementedError("Gemini adapter not implemented yet; use OpenAI-compatible providers.")
