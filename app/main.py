from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.logging import setup_logging
from app.core.settings import settings
from app.db.session import init_db


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title=settings.app_name)

    @app.on_event("startup")
    def _startup() -> None:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        settings.kb_files_dir.mkdir(parents=True, exist_ok=True)
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        init_db()

    app.include_router(api_router)
    return app


app = create_app()

