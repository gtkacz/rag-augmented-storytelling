from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from app.core.settings import settings


def kb_collection_name(kb_id: str) -> str:
    return f"kb_{kb_id}"


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    kb_id: str
    score: float
    text: str
    payload: dict[str, Any]


class QdrantVectorStore:
    def __init__(self) -> None:
        self._client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

    async def ensure_kb_collection(self, *, kb_id: str, vector_size: int) -> None:
        name = kb_collection_name(kb_id)
        if await self._client.collection_exists(name):
            info = await self._client.get_collection(name)
            vectors = info.config.params.vectors  # type: ignore[attr-defined]

            existing_size: int | None = None
            if hasattr(vectors, "size"):
                existing_size = int(vectors.size)  # type: ignore[attr-defined]
            elif isinstance(vectors, dict) and vectors:
                # Multi-vector config; take first vector size as baseline.
                existing_size = int(next(iter(vectors.values())).size)

            if existing_size is not None and existing_size != vector_size:
                # Recreate if embedding dimension changed.
                await self._client.delete_collection(name)
            else:
                return

        await self._client.create_collection(
            collection_name=name,
            vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
        )
        await self._client.create_payload_index(
            collection_name=name,
            field_name="doc_id",
            field_schema=qm.PayloadSchemaType.KEYWORD,
        )

    async def delete_kb_collection(self, *, kb_id: str) -> None:
        name = kb_collection_name(kb_id)
        if await self._client.collection_exists(name):
            await self._client.delete_collection(name)

    async def upsert_chunks(
        self,
        *,
        kb_id: str,
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
        point_ids: list[str],
    ) -> None:
        if not (len(vectors) == len(payloads) == len(point_ids)):
            raise ValueError("vectors/payloads/point_ids length mismatch")

        await self._client.upsert(
            collection_name=kb_collection_name(kb_id),
            points=qm.Batch(ids=point_ids, vectors=vectors, payloads=payloads),
        )

    async def search(
        self,
        *,
        kb_id: str,
        query_vector: list[float],
        top_k: int,
        where: dict[str, Any] | None,
    ) -> list[RetrievedChunk]:
        flt: qm.Filter | None = None
        if where:
            must: list[qm.FieldCondition] = []
            for key, value in where.items():
                if isinstance(value, list):
                    must.append(qm.FieldCondition(key=key, match=qm.MatchAny(any=value)))
                else:
                    must.append(qm.FieldCondition(key=key, match=qm.MatchValue(value=value)))
            flt = qm.Filter(must=must)

        res = await self._client.search(
            collection_name=kb_collection_name(kb_id),
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
            query_filter=flt,
        )

        out: list[RetrievedChunk] = []
        for p in res:
            payload = dict(p.payload or {})
            out.append(
                RetrievedChunk(
                    chunk_id=str(payload.get("chunk_id") or p.id),
                    doc_id=str(payload.get("doc_id") or ""),
                    kb_id=str(payload.get("kb_id") or kb_id),
                    score=float(p.score),
                    text=str(payload.get("text") or ""),
                    payload=payload,
                )
            )
        return out

    async def delete_doc_vectors(self, *, kb_id: str, doc_id: str) -> None:
        await self._client.delete(
            collection_name=kb_collection_name(kb_id),
            points_selector=qm.FilterSelector(
                filter=qm.Filter(must=[qm.FieldCondition(key="doc_id", match=qm.MatchValue(value=doc_id))])
            ),
        )
