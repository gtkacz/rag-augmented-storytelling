from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.documents import router as documents_router
from app.api.routes.kbs import router as kbs_router
from app.api.routes.query import router as query_router
from app.core.logging import configure_logging
from app.core.settings import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(logging.INFO)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.files_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(title="RAG Storyteller API", version="0.1.0", lifespan=lifespan)

app.include_router(kbs_router, prefix="/v1", tags=["kbs"])
app.include_router(documents_router, prefix="/v1", tags=["documents"])
app.include_router(query_router, prefix="/v1", tags=["query"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
