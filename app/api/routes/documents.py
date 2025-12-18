from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db import crud
from app.ingest.pipeline import IngestService
from app.vectorstore.qdrant import QdrantVectorStore

router = APIRouter()


class DocumentOut(BaseModel):
    id: str
    kb_id: str
    filename: str
    content_type: str | None
    sha256: str
    size_bytes: int
    created_at: str


@router.post("/kbs/{kb_id}/documents")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    user_meta_json: str | None = Form(default=None),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    kb = await crud.get_kb(session, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")

    content = await file.read()

    user_meta: dict[str, Any] | None = None
    if user_meta_json:
        try:
            user_meta = json.loads(user_meta_json)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid user_meta_json: {e}") from e

    service = IngestService()
    result = await service.ingest_upload(
        session=session,
        kb_id=kb_id,
        filename=file.filename or "upload",
        content_type=file.content_type,
        content=content,
        user_meta=user_meta,
    )

    return {"doc_id": result.doc_id, "chunk_count": result.chunk_count}


@router.get("/kbs/{kb_id}/documents")
async def list_documents(kb_id: str, session: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    kb = await crud.get_kb(session, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")

    docs = await crud.list_documents(session, kb_id)
    return [
        {
            "id": d.id,
            "kb_id": d.kb_id,
            "filename": d.filename,
            "content_type": d.content_type,
            "sha256": d.sha256,
            "size_bytes": d.size_bytes,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    doc = await crud.get_document(session, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc.id,
        "kb_id": doc.kb_id,
        "filename": doc.filename,
        "content_type": doc.content_type,
        "sha256": doc.sha256,
        "size_bytes": doc.size_bytes,
        "created_at": doc.created_at.isoformat(),
        "extraction_meta": doc.extraction_meta,
        "user_meta": doc.user_meta,
    }


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    doc = await crud.get_document(session, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    kb_id = doc.kb_id

    # Best-effort remove vectors first.
    try:
        await QdrantVectorStore().delete_doc_vectors(kb_id=kb_id, doc_id=doc_id)
    except Exception:  # noqa: BLE001
        pass

    await crud.delete_document(session, doc_id)

    return {"deleted": True, "doc_id": doc_id}
