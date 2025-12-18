from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk, Document, KnowledgeBase


# KBs
async def create_kb(
    session: AsyncSession,
    *,
    name: str,
    description: str | None = None,
    tags: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> KnowledgeBase:
    kb = KnowledgeBase(name=name, description=description, tags=tags, extra=extra)
    session.add(kb)
    await session.commit()
    await session.refresh(kb)
    return kb


async def list_kbs(session: AsyncSession) -> list[KnowledgeBase]:
    res = await session.execute(select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()))
    return list(res.scalars().all())


async def get_kb(session: AsyncSession, kb_id: str) -> KnowledgeBase | None:
    res = await session.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    return res.scalar_one_or_none()


async def delete_kb(session: AsyncSession, kb_id: str) -> bool:
    res = await session.execute(delete(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    await session.commit()
    return res.rowcount > 0


# Documents
async def create_document(
    session: AsyncSession,
    *,
    kb_id: str,
    filename: str,
    content_type: str | None,
    sha256: str,
    size_bytes: int,
    storage_path: str,
    extracted_text: str | None = None,
    extraction_meta: dict[str, Any] | None = None,
    user_meta: dict[str, Any] | None = None,
) -> Document:
    doc = Document(
        kb_id=kb_id,
        filename=filename,
        content_type=content_type,
        sha256=sha256,
        size_bytes=size_bytes,
        storage_path=storage_path,
        extracted_text=extracted_text,
        extraction_meta=extraction_meta,
        user_meta=user_meta,
    )
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return doc


async def list_documents(session: AsyncSession, kb_id: str) -> list[Document]:
    res = await session.execute(
        select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc())
    )
    return list(res.scalars().all())


async def get_document(session: AsyncSession, doc_id: str) -> Document | None:
    res = await session.execute(select(Document).where(Document.id == doc_id))
    return res.scalar_one_or_none()


async def delete_document(session: AsyncSession, doc_id: str) -> bool:
    res = await session.execute(delete(Document).where(Document.id == doc_id))
    await session.commit()
    return res.rowcount > 0


# Chunks
async def create_chunks(session: AsyncSession, chunks: list[Chunk]) -> list[Chunk]:
    session.add_all(chunks)
    await session.commit()
    for c in chunks:
        await session.refresh(c)
    return chunks


async def list_chunks_for_doc(session: AsyncSession, doc_id: str) -> list[Chunk]:
    res = await session.execute(select(Chunk).where(Chunk.doc_id == doc_id).order_by(Chunk.chunk_index))
    return list(res.scalars().all())


async def delete_chunks_for_doc(session: AsyncSession, doc_id: str) -> int:
    res = await session.execute(delete(Chunk).where(Chunk.doc_id == doc_id))
    await session.commit()
    return int(res.rowcount or 0)
