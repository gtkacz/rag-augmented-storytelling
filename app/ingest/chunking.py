from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    index: int
    text: str
    start: int | None
    end: int | None


def chunk_text(
    text: str,
    *,
    max_chars: int = 1200,
    overlap: int = 150,
) -> list[Chunk]:
    """Simple, robust chunker.

    - Splits on paragraph boundaries when possible.
    - Enforces max_chars with sliding-window fallback.
    """

    normalized = text.replace("\r\n", "\n")
    paras = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    if not paras:
        return []

    chunks: list[Chunk] = []
    buf = ""
    idx = 0
    pos = 0

    def flush() -> None:
        nonlocal buf, idx, pos
        if not buf:
            return
        start = pos
        end = pos + len(buf)
        chunks.append(Chunk(index=idx, text=buf, start=start, end=end))
        idx += 1
        pos = max(end - overlap, 0)
        buf = ""

    for p in paras:
        candidate = (buf + "\n\n" + p).strip() if buf else p
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        flush()
        if len(p) <= max_chars:
            buf = p
            continue

        # Fallback: sliding window.
        i = 0
        while i < len(p):
            window = p[i : i + max_chars]
            chunks.append(Chunk(index=idx, text=window, start=None, end=None))
            idx += 1
            i = max(i + max_chars - overlap, i + 1)

    flush()
    return chunks
