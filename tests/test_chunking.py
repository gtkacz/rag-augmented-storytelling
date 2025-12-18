from __future__ import annotations

from app.ingest.chunking import chunk_text


def test_chunk_text_basic() -> None:
    text = "\n\n".join(["para " + str(i) + " " + ("x" * 200) for i in range(10)])
    chunks = chunk_text(text, max_chars=500, overlap=50)
    assert chunks
    assert chunks[0].index == 0
    # Chunks should not exceed max_chars by construction.
    assert all(len(c.text) <= 500 for c in chunks)


def test_chunk_text_handles_empty() -> None:
    assert chunk_text("   \n\n  ") == []
