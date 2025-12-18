from __future__ import annotations

import pytest

from app.db import crud
from app.db.session import AsyncSessionLocal, init_db


@pytest.mark.asyncio
async def test_create_and_list_kb() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        kb = await crud.create_kb(session, name="test", description="desc")
        assert kb.id
        kbs = await crud.list_kbs(session)
        assert any(x.id == kb.id for x in kbs)
