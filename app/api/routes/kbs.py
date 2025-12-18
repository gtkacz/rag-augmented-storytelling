from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db import crud
from app.vectorstore.qdrant import QdrantVectorStore

router = APIRouter()


class KBCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    tags: list[str] | None = None
    extra: dict[str, Any] | None = None


class KBOut(BaseModel):
    id: str
    name: str
    description: str | None
    tags: list[str] | None
    extra: dict[str, Any] | None


@router.post("/kbs", response_model=KBOut)
async def create_kb(payload: KBCreate, session: AsyncSession = Depends(get_db)) -> KBOut:
    kb = await crud.create_kb(
        session,
        name=payload.name,
        description=payload.description,
        tags=payload.tags,
        extra=payload.extra,
    )
    return KBOut.model_validate(kb, from_attributes=True)


@router.get("/kbs", response_model=list[KBOut])
async def list_kbs(session: AsyncSession = Depends(get_db)) -> list[KBOut]:
    kbs = await crud.list_kbs(session)
    return [KBOut.model_validate(kb, from_attributes=True) for kb in kbs]


@router.get("/kbs/{kb_id}", response_model=KBOut)
async def get_kb(kb_id: str, session: AsyncSession = Depends(get_db)) -> KBOut:
    kb = await crud.get_kb(session, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")
    return KBOut.model_validate(kb, from_attributes=True)


@router.delete("/kbs/{kb_id}")
async def delete_kb(kb_id: str, session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    ok = await crud.delete_kb(session, kb_id)
    if not ok:
        raise HTTPException(status_code=404, detail="KB not found")

    # Best-effort: remove Qdrant collection.
    try:
        await QdrantVectorStore().delete_kb_collection(kb_id=kb_id)
    except Exception:  # noqa: BLE001
        pass

    return {"deleted": True, "kb_id": kb_id}
