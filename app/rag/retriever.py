from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.embeddings.hf_dense import HFDenseEmbedder
from app.vectorstore.qdrant import QdrantVectorStore, RetrievedChunk


@dataclass(frozen=True)
class Citation:
    chunk_id: str
    doc_id: str
    score: float
    snippet: str
    metadata: dict[str, Any]


class RetrievalService:
    def __init__(self) -> None:
        self._embedder = HFDenseEmbedder()
        self._vs = QdrantVectorStore()

    async def retrieve(
        self,
        *,
        kb_id: str,
        question: str,
        top_k: int,
        where: dict[str, Any] | None,
    ) -> list[RetrievedChunk]:
        q = self._embedder.embed_query(question)
        return await self._vs.search(kb_id=kb_id, query_vector=q, top_k=top_k, where=where)

    @staticmethod
    def to_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
        citations: list[Citation] = []
        for c in chunks:
            text = c.text
            snippet = text[:400] + ("…" if len(text) > 400 else "")
            meta = dict(c.payload or {})
            citations.append(
                Citation(
                    chunk_id=c.chunk_id,
                    doc_id=c.doc_id,
                    score=c.score,
                    snippet=snippet,
                    metadata=meta,
                )
            )
        return citations
