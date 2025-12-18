from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ExtractedText:
    text: str
    meta: dict[str, Any]


class Extractor(Protocol):
    def can_handle(self, *, path: str, content_type: str | None) -> bool: ...

    def extract(self, *, path: str, content_type: str | None) -> ExtractedText: ...


