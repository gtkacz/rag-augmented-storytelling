from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeBase(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str
    description: str | None = None
    created_at: datetime = Field(default_factory=utcnow)


class Document(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    kb_id: str = Field(index=True, foreign_key="knowledgebase.id")

    original_filename: str
    content_type: str | None = None
    status: str = Field(default="uploaded", index=True)  # uploaded|ingesting|ready|error

    created_at: datetime = Field(default_factory=utcnow)


class IngestionJob(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    kb_id: str = Field(index=True, foreign_key="knowledgebase.id")
    doc_id: str = Field(index=True, foreign_key="document.id")

    state: str = Field(default="queued", index=True)  # queued|running|succeeded|failed
    error: str | None = None

    started_at: datetime | None = None
    finished_at: datetime | None = None

    created_at: datetime = Field(default_factory=utcnow)


class Chunk(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    kb_id: str = Field(index=True, foreign_key="knowledgebase.id")
    doc_id: str = Field(index=True, foreign_key="document.id")

    chunk_index: int = Field(index=True)
    text: str

    start_offset: int | None = None
    end_offset: int | None = None
    meta: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(SQLiteJSON, nullable=False),
    )


class EmbeddingRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    chunk_id: str = Field(index=True, foreign_key="chunk.id")

    vector_id: str = Field(index=True)
    embedding_model: str
    dims: int


