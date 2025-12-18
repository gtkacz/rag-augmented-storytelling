from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlmodel import Session

from app.core.settings import settings
from app.db import crud
from app.db.models import Chunk, EmbeddingRecord
from app.embeddings.hf_dense import HuggingFaceDenseEmbedder
from app.ingest.chunking import chunk_text
from app.ingest.extractors.dispatcher import ExtractorDispatcher
from app.storage.local import write_extracted_text
from app.vectorstore.chroma import ChromaVectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(self) -> None:
        self._extract = ExtractorDispatcher()
        self._embedder = HuggingFaceDenseEmbedder()
        self._vs = ChromaVectorStore()

    def ingest_document(
        self,
        *,
        session: Session,
        kb_id: str,
        doc_id: str,
        raw_path: Path,
        content_type: str | None,
        chunk_size: int = 1200,
        overlap: int = 150,
    ) -> dict[str, Any]:
        doc = crud.get_document(session, doc_id)
        if not doc or doc.kb_id != kb_id:
            raise ValueError("document not found for kb")

        doc.status = "ingesting"
        session.add(doc)
        session.commit()

        extracted = self._extract.extract(path=str(raw_path), content_type=content_type)
        write_extracted_text(kb_id, doc_id, extracted.text)

        base_meta = {"doc_id": doc_id, "source_name": extracted.meta.get("source_name")}
        chunks = chunk_text(extracted.text, chunk_size=chunk_size, overlap=overlap, base_meta=base_meta)

        if not chunks:
            doc.status = "error"
            session.add(doc)
            session.commit()
            raise ValueError("no text extracted from document")

        # Persist chunks
        chunk_rows: list[Chunk] = []
        for c in chunks:
            row = Chunk(
                kb_id=kb_id,
                doc_id=doc_id,
                chunk_index=c.index,
                text=c.text,
                start_offset=c.start_offset,
                end_offset=c.end_offset,
                meta=c.meta,
            )
            session.add(row)
            chunk_rows.append(row)
        session.commit()
        for r in chunk_rows:
            session.refresh(r)

        # Embed & upsert
        texts = [r.text for r in chunk_rows]
        vectors = self._embedder.embed_texts(texts)
        metadatas = [
            {
                "kb_id": kb_id,
                "doc_id": doc_id,
                "chunk_id": r.id,
                "chunk_index": r.chunk_index,
                "source_name": r.meta.get("source_name") or doc.original_filename,
            }
            for r in chunk_rows
        ]
        self._vs.upsert(kb_id=kb_id, ids=[r.id for r in chunk_rows], vectors=vectors, texts=texts, metadatas=metadatas)

        # Save embedding records
        dims = len(vectors[0]) if vectors else 0
        for r in chunk_rows:
            session.add(
                EmbeddingRecord(
                    chunk_id=r.id,
                    vector_id=r.id,
                    embedding_model=settings.embedding_model,
                    dims=dims,
                )
            )
        session.commit()

        doc.status = "ready"
        session.add(doc)
        session.commit()

        return {"chunks": len(chunk_rows), "embedding_dims": dims, "extracted_meta": extracted.meta}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


