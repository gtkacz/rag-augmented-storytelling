from __future__ import annotations

from typing import Any


def build_storyteller_system_prompt() -> str:
    return (
        "You are a careful, creative storyteller assistant. "
        "Use ONLY the provided context when it is relevant. "
        "If the context is insufficient, ask clarifying questions instead of inventing facts. "
        "Keep the tone consistent with the user's world and constraints."
    )


def build_user_prompt(question: str, *, contexts: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    parts.append("Question:\n" + question.strip())
    parts.append("\nContext (retrieved from the user's world knowledge base):")
    for i, ctx in enumerate(contexts, start=1):
        cite = ctx.get("citation") or f"source_{i}"
        text = (ctx.get("text") or "").strip()
        parts.append(f"\n[{i}] {cite}\n{text}")
    parts.append("\nInstructions: Answer the question. Cite sources like [1], [2] when using facts from context.")
    return "\n".join(parts)


