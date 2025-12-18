from __future__ import annotations

from typing import Any

from app.core.settings import settings
from app.embeddings.hf_dense import HuggingFaceDenseEmbedder
from app.vectorstore.chroma import ChromaVectorStore


class RetrievalService:
    def __init__(self) -> None:
        self._embedder = HuggingFaceDenseEmbedder()
        self._vs = ChromaVectorStore()

    def retrieve(
        self,
        *,
        kb_id: str,
        question: str,
        top_k: int | None = None,
        where: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        qv = self._embedder.embed_texts([question])[0]
        results = self._vs.query(
            kb_id=kb_id,
            query_vector=qv,
            top_k=top_k or settings.rag_top_k,
            where=where,
        )

        contexts: list[dict[str, Any]] = []
        total = 0
        for r in results:
            citation = r.meta.get("source_name") or r.meta.get("doc_id") or r.id
            text = r.text
            if total + len(text) > settings.rag_max_context_chars:
                break
            total += len(text)
            contexts.append(
                {
                    "id": r.id,
                    "score": r.score,
                    "text": text,
                    "meta": r.meta,
                    "citation": citation,
                }
            )
        return contexts


