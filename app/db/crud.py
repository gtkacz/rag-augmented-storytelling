from __future__ import annotations

from sqlmodel import Session, select

from app.db.models import Chunk, Document, IngestionJob, KnowledgeBase


def create_kb(session: Session, *, name: str, description: str | None) -> KnowledgeBase:
    kb = KnowledgeBase(name=name, description=description)
    session.add(kb)
    session.commit()
    session.refresh(kb)
    return kb


def list_kbs(session: Session) -> list[KnowledgeBase]:
    return list(session.exec(select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())))


def get_kb(session: Session, kb_id: str) -> KnowledgeBase | None:
    return session.get(KnowledgeBase, kb_id)


def create_document(
    session: Session,
    *,
    kb_id: str,
    original_filename: str,
    content_type: str | None,
) -> Document:
    doc = Document(kb_id=kb_id, original_filename=original_filename, content_type=content_type)
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def get_document(session: Session, doc_id: str) -> Document | None:
    return session.get(Document, doc_id)


def list_documents_for_kb(session: Session, kb_id: str) -> list[Document]:
    stmt = select(Document).where(Document.kb_id == kb_id).order_by(Document.created_at.desc())
    return list(session.exec(stmt))


def create_ingestion_job(session: Session, *, kb_id: str, doc_id: str) -> IngestionJob:
    job = IngestionJob(kb_id=kb_id, doc_id=doc_id)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_job(session: Session, job_id: str) -> IngestionJob | None:
    return session.get(IngestionJob, job_id)


def upsert_chunk(session: Session, chunk: Chunk) -> Chunk:
    session.add(chunk)
    session.commit()
    session.refresh(chunk)
    return chunk


