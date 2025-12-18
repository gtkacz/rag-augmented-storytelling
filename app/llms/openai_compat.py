from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.core.settings import settings


@dataclass(frozen=True)
class ProviderConfig:
    base_url: str
    api_key: str
    model: str
    extra_headers: dict[str, str] | None = None


class OpenAICompatibleClient:
    async def chat(
        self,
        *,
        provider: ProviderConfig,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        url = provider.base_url.rstrip("/") + "/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        if provider.extra_headers:
            headers.update(provider.extra_headers)

        body: dict[str, Any] = {
            "model": provider.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens

        timeout = httpx.Timeout(settings.http_timeout_s)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        # OpenAI-style: choices[0].message.content
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("No choices returned from provider")
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if not isinstance(content, str):
            raise ValueError("Provider response missing message.content")
        return content
