from __future__ import annotations

from typing import Any


def build_storyteller_system_prompt() -> str:
    return (
        "You are a world-aware storyteller assistant.\n"
        "Use provided CONTEXT as canon for names, places, rules, and tone.\n"
        "If context is insufficient, ask clarifying questions or clearly mark assumptions.\n"
        "Keep the output vivid, coherent, and consistent with the canon."
    )


def build_user_prompt(user_message: str, *, contexts: list[dict[str, Any]]) -> str:
    if not contexts:
        return user_message

    blocks: list[str] = []
    for i, c in enumerate(contexts, start=1):
        citation = c.get("citation") or c.get("chunk_id") or c.get("id") or str(i)
        text = c.get("text") or ""
        blocks.append(f"[{i}] {citation}\n{text}")

    joined = "\n\n".join(blocks)
    return f"CONTEXT:\n{joined}\n\nUSER_REQUEST:\n{user_message}"
