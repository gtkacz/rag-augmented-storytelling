from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    kb_id: str
    score: float
    text: str
    payload: dict[str, Any]


class VectorStore(Protocol):
    async def ensure_kb_collection(self, *, kb_id: str, vector_size: int) -> None: ...

    async def delete_kb_collection(self, *, kb_id: str) -> None: ...

    async def upsert_chunks(
        self,
        *,
        kb_id: str,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
        point_ids: list[str],
    ) -> None: ...

    async def search(
        self,
        *,
        kb_id: str,
        query_vector: list[float],
        top_k: int,
        where: dict[str, Any] | None,
    ) -> list[RetrievedChunk]: ...

    async def delete_doc_vectors(self, *, kb_id: str, doc_id: str) -> None: ...
