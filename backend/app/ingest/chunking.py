from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TextChunk:
    index: int
    text: str
    start_offset: int | None
    end_offset: int | None
    meta: dict[str, Any]


def chunk_text(
    text: str,
    *,
    chunk_size: int = 1200,
    overlap: int = 150,
    base_meta: dict[str, Any] | None = None,
) -> list[TextChunk]:
    text = text or ""
    if not text.strip():
        return []

    base_meta = dict(base_meta or {})
    chunks: list[TextChunk] = []

    i = 0
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)

        # Try not to cut mid-paragraph if possible (best-effort).
        if end < n:
            window = text[start:end]
            last_break = max(window.rfind("\n\n"), window.rfind("\n"))
            if last_break > chunk_size * 0.6:
                end = start + last_break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(
                TextChunk(
                    index=i,
                    text=chunk,
                    start_offset=start,
                    end_offset=end,
                    meta=dict(base_meta),
                )
            )
            i += 1

        if end >= n:
            break
        start = max(0, end - overlap)

    return chunks


