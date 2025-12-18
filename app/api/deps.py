from __future__ import annotations

from collections.abc import AsyncIterator

from app.db.session import AsyncSessionLocal


async def get_db() -> AsyncIterator[AsyncSessionLocal]:
    async with AsyncSessionLocal() as session:
        yield session
