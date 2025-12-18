from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_session
from app.db import crud
from app.ingest.pipeline import IngestionPipeline
from app.storage.local import save_upload

router = APIRouter()


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    status: str


class IngestStartResponse(BaseModel):
    job_id: str
    state: str


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/{kb_id}/documents", response_model=list[UploadResponse])
def upload_documents(
    kb_id: str,
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_session),
) -> list[UploadResponse]:
    kb = crud.get_kb(session, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="knowledge base not found")

    out: list[UploadResponse] = []
    for f in files:
        doc = crud.create_document(session, kb_id=kb_id, original_filename=f.filename or "upload", content_type=f.content_type)
        save_upload(kb_id, doc.id, f)
        out.append(UploadResponse(doc_id=doc.id, filename=doc.original_filename, status=doc.status))
    return out


@router.post("/{kb_id}/documents/{doc_id}/ingest", response_model=IngestStartResponse)
def start_ingest(
    kb_id: str,
    doc_id: str,
    background: BackgroundTasks,
    session: Session = Depends(get_session),
) -> IngestStartResponse:
    kb = crud.get_kb(session, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="knowledge base not found")

    doc = crud.get_document(session, doc_id)
    if not doc or doc.kb_id != kb_id:
        raise HTTPException(status_code=404, detail="document not found")

    job = crud.create_ingestion_job(session, kb_id=kb_id, doc_id=doc_id)

    def _run(job_id: str) -> None:
        # Separate session for background task.
        from app.db.session import SessionLocal

        with SessionLocal() as bg:
            j = crud.get_job(bg, job_id)
            if not j:
                return
            j.state = "running"
            j.started_at = utcnow()
            bg.add(j)
            bg.commit()

            try:
                from app.core.settings import settings
                raw_dir = settings.kb_files_dir / kb_id / "raw" / doc_id
                # Take the first file in the raw dir (MVP).
                files = sorted([p for p in raw_dir.glob("*") if p.is_file()])
                if not files:
                    raise ValueError("no raw file found for document")

                pipeline = IngestionPipeline()
                pipeline.ingest_document(
                    session=bg,
                    kb_id=kb_id,
                    doc_id=doc_id,
                    raw_path=files[0],
                    content_type=doc.content_type,
                )

                j.state = "succeeded"
                j.finished_at = utcnow()
                bg.add(j)
                bg.commit()
            except Exception as e:
                j.state = "failed"
                j.error = str(e)
                j.finished_at = utcnow()
                bg.add(j)
                bg.commit()

    background.add_task(_run, job.id)
    return IngestStartResponse(job_id=job.id, state=job.state)


@router.get("/{kb_id}/jobs/{job_id}")
def get_job(kb_id: str, job_id: str, session: Session = Depends(get_session)) -> dict:
    kb = crud.get_kb(session, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="knowledge base not found")
    job = crud.get_job(session, job_id)
    if not job or job.kb_id != kb_id:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "id": job.id,
        "kb_id": job.kb_id,
        "doc_id": job.doc_id,
        "state": job.state,
        "error": job.error,
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }

