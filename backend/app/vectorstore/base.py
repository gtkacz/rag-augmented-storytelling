from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class VectorSearchResult:
    id: str
    score: float
    text: str
    meta: dict[str, Any]


class VectorStore(Protocol):
    def upsert(
        self,
        *,
        kb_id: str,
        ids: list[str],
        vectors: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None: ...

    def query(
        self,
        *,
        kb_id: str,
        query_vector: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]: ...


