from __future__ import annotations

from pydantic import BaseModel
from sqlmodel import Session

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_session
from app.db import crud

router = APIRouter()


class KBCreate(BaseModel):
    name: str
    description: str | None = None


@router.post("")
def create_kb(payload: KBCreate, session: Session = Depends(get_session)) -> dict:
    kb = crud.create_kb(session, name=payload.name, description=payload.description)
    return {"id": kb.id, "name": kb.name, "description": kb.description, "created_at": kb.created_at}


@router.get("")
def list_kbs(session: Session = Depends(get_session)) -> list[dict]:
    kbs = crud.list_kbs(session)
    return [{"id": kb.id, "name": kb.name, "description": kb.description, "created_at": kb.created_at} for kb in kbs]


@router.get("/{kb_id}")
def get_kb(kb_id: str, session: Session = Depends(get_session)) -> dict:
    kb = crud.get_kb(session, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="knowledge base not found")
    return {"id": kb.id, "name": kb.name, "description": kb.description, "created_at": kb.created_at}


