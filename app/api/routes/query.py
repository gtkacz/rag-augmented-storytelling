from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_session
from app.db import crud
from app.llms.gemini import GeminiClient
from app.rag.prompting import build_storyteller_system_prompt, build_user_prompt
from app.rag.retriever import RetrievalService

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    top_k: int | None = None
    filters: dict[str, Any] | None = None


@router.post("/{kb_id}/query")
def query_kb(kb_id: str, payload: QueryRequest, session: Session = Depends(get_session)) -> dict:
    kb = crud.get_kb(session, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="knowledge base not found")

    retriever = RetrievalService()
    contexts = retriever.retrieve(kb_id=kb_id, question=payload.question, top_k=payload.top_k, where=payload.filters)

    system = build_storyteller_system_prompt()
    user = build_user_prompt(payload.question, contexts=contexts)

    client = GeminiClient()
    answer = client.generate(system=system, user=user)

    return {
        "kb_id": kb_id,
        "question": payload.question,
        "answer": answer,
        "contexts": contexts,
    }

