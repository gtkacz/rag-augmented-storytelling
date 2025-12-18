from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    meta: dict[str, Any]


class Extractor(Protocol):
    def can_handle(self, *, filename: str, content_type: str | None) -> bool: ...

    def extract(self, *, filename: str, content: bytes, content_type: str | None) -> ExtractedDocument: ...
