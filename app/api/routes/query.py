from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db import crud
from app.llms.openai_compat import OpenAICompatibleClient, ProviderConfig
from app.rag.prompting import build_storyteller_system_prompt
from app.rag.retriever import RetrievalService

router = APIRouter()


class ProviderConfigIn(BaseModel):
    base_url: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    model: str = Field(min_length=1)
    extra_headers: dict[str, str] | None = None


class QueryIn(BaseModel):
    kb_id: str
    message: str = Field(min_length=1)
    top_k: int = Field(default=6, ge=1, le=50)
    provider_config: ProviderConfigIn
    system_preamble: str | None = None
    filters: dict[str, Any] | None = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class CitationOut(BaseModel):
    doc_id: str
    chunk_id: str
    snippet: str
    score: float
    metadata: dict[str, Any]


class QueryOut(BaseModel):
    answer: str
    citations: list[CitationOut]


@router.post("/query", response_model=QueryOut)
async def query(payload: QueryIn, session: AsyncSession = Depends(get_db)) -> QueryOut:
    kb = await crud.get_kb(session, payload.kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="KB not found")

    retriever = RetrievalService()
    retrieved = await retriever.retrieve(
        kb_id=payload.kb_id,
        question=payload.message,
        top_k=payload.top_k,
        where=payload.filters,
    )

    contexts = [
        {
            "chunk_id": r.chunk_id,
            "doc_id": r.doc_id,
            "score": r.score,
            "text": r.text,
            "citation": r.payload.get("filename") if isinstance(r.payload, dict) else None,
            "meta": r.payload,
        }
        for r in retrieved
    ]

    system = build_storyteller_system_prompt()
    if payload.system_preamble:
        system = payload.system_preamble + "\n\n" + system

    # Keep message format OpenAI-compatible.
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                "Use the following context as canon. If context is irrelevant, ignore it.\n\n"
                + "\n\n".join(
                    f"[ctx {i+1}] {c['text']}" for i, c in enumerate(contexts) if c.get("text")
                )
                + f"\n\nUser request:\n{payload.message}"
            ),
        },
    ]

    client = OpenAICompatibleClient()
    try:
        answer = await client.chat(
            provider=ProviderConfig(
                base_url=payload.provider_config.base_url,
                api_key=payload.provider_config.api_key,
                model=payload.provider_config.model,
                extra_headers=payload.provider_config.extra_headers,
            ),
            messages=messages,
            temperature=payload.temperature,
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Provider call failed: {e}") from e

    citations = RetrievalService.to_citations(retrieved)
    return QueryOut(
        answer=answer,
        citations=[
            CitationOut(
                doc_id=c.doc_id,
                chunk_id=c.chunk_id,
                snippet=c.snippet,
                score=c.score,
                metadata=c.metadata,
            )
            for c in citations
        ],
    )
