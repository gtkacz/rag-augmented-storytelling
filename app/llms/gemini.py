from __future__ import annotations

import logging

from google import genai

from app.core.settings import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def generate(self, *, system: str, user: str) -> str:
        # Minimal wrapper around SDK; keeps the door open to add retries/timeouts later.
        resp = self._client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                {"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]},
            ],
        )

        text = getattr(resp, "text", None)
        if not text:
            # Fallback: try to stringify the whole response for debugging.
            return str(resp)
        return text


