from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from app.core.settings import settings
from app.db import models  # noqa: F401

engine = create_engine(
    f"sqlite:///{settings.sqlite_path}",
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    # MVP: create tables automatically. Alembic scaffolding can be added later.
    SQLModel.metadata.create_all(engine)


class SessionLocal(Session):
    def __init__(self) -> None:
        super().__init__(engine)


