from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.db.models import Chunk as ChunkModel
from app.embeddings.hf_dense import HFDenseEmbedder
from app.ingest.chunking import chunk_text
from app.ingest.extractors.dispatcher import ExtractorDispatcher
from app.storage.local import LocalFileStore
from app.vectorstore.qdrant import QdrantVectorStore


@dataclass(frozen=True)
class IngestResult:
    doc_id: str
    chunk_count: int


class IngestService:
    def __init__(self) -> None:
        self._files = LocalFileStore()
        self._extractors = ExtractorDispatcher()
        self._embedder = HFDenseEmbedder()
        self._vs = QdrantVectorStore()

    async def ingest_upload(
        self,
        *,
        session: AsyncSession,
        kb_id: str,
        filename: str,
        content_type: str | None,
        content: bytes,
        user_meta: dict[str, Any] | None,
    ) -> IngestResult:
        storage_path, sha, size = self._files.put(kb_id=kb_id, filename=filename, content=content)

        extracted = self._extractors.extract(filename=filename, content=content, content_type=content_type)
        chunks = chunk_text(extracted.text)

        # Persist doc + chunks
        doc = await crud.create_document(
            session,
            kb_id=kb_id,
            filename=filename,
            content_type=content_type,
            sha256=sha,
            size_bytes=size,
            storage_path=storage_path,
            extracted_text=extracted.text,
            extraction_meta=extracted.meta,
            user_meta=user_meta,
        )

        chunk_models: list[ChunkModel] = []
        payloads: list[dict[str, Any]] = []
        texts: list[str] = []
        point_ids: list[str] = []

        for c in chunks:
            cm = ChunkModel(
                kb_id=kb_id,
                doc_id=doc.id,
                chunk_index=c.index,
                text=c.text,
                token_count=None,
                start_offset=c.start,
                end_offset=c.end,
                payload={
                    "kb_id": kb_id,
                    "doc_id": doc.id,
                    "chunk_index": c.index,
                    "filename": filename,
                    **(extracted.meta or {}),
                    **(user_meta or {}),
                },
            )
            chunk_models.append(cm)

        chunk_models = await crud.create_chunks(session, chunk_models)

        for cm in chunk_models:
            payload = dict(cm.payload or {})
            payload.update({"chunk_id": cm.id, "text": cm.text, "kb_id": kb_id, "doc_id": doc.id})
            payloads.append(payload)
            texts.append(cm.text)
            point_ids.append(cm.id)

        embedded = self._embedder.embed_texts(texts)
        await self._vs.ensure_kb_collection(kb_id=kb_id, vector_size=embedded.dim)
        await self._vs.upsert_chunks(kb_id=kb_id, vectors=embedded.vectors, payloads=payloads, point_ids=point_ids)

        return IngestResult(doc_id=doc.id, chunk_count=len(chunk_models))
