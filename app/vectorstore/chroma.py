from __future__ import annotations

from typing import Any

from app.core.settings import settings
from app.vectorstore.base import VectorSearchResult


class ChromaVectorStore:
    def __init__(self) -> None:
        # Import lazily to avoid crashing the whole app on dependency mismatches
        # (e.g. pydantic v2 vs older chromadb builds).
        import chromadb  # type: ignore

        self._client = chromadb.PersistentClient(path=str(settings.chroma_dir))

    def _collection_name(self, kb_id: str) -> str:
        return f"kb_{kb_id}"

    def _get_collection(self, kb_id: str):
        name = self._collection_name(kb_id)
        return self._client.get_or_create_collection(name=name, metadata={"kb_id": kb_id})

    def upsert(
        self,
        *,
        kb_id: str,
        ids: list[str],
        vectors: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        if not (len(ids) == len(vectors) == len(texts) == len(metadatas)):
            raise ValueError("ids/vectors/texts/metadatas lengths must match")

        col = self._get_collection(kb_id)
        # Ensure kb_id is always present for filtering/debugging
        metadatas = [{**m, "kb_id": kb_id} for m in metadatas]
        col.upsert(ids=ids, embeddings=vectors, documents=texts, metadatas=metadatas)

    def query(
        self,
        *,
        kb_id: str,
        query_vector: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        col = self._get_collection(kb_id)

        final_where: dict[str, Any] | None = None
        if where:
            final_where = dict(where)

        res = col.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=final_where,
            include=["metadatas", "documents", "distances"],
        )

        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]

        out: list[VectorSearchResult] = []
        for _id, doc, meta, dist in zip(ids, docs, metas, dists):
            # Chroma returns distances; convert to a score where higher is better.
            score = -float(dist) if dist is not None else 0.0
            out.append(VectorSearchResult(id=str(_id), score=score, text=str(doc), meta=dict(meta or {})))
        return out


