from __future__ import annotations

from collections.abc import Generator

from app.db.session import SessionLocal


def get_session() -> Generator:
    with SessionLocal() as session:
        yield session


