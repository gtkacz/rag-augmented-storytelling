from __future__ import annotations

from app.ingest.extractors.base import ExtractedText
from app.ingest.extractors.common import ext_lower, read_text_file


class PlainTextExtractor:
    _exts = {"txt", "md", "markdown", "log"}

    def can_handle(self, *, path: str, content_type: str | None) -> bool:
        if content_type and content_type.startswith("text/"):
            return True
        return ext_lower(path) in self._exts

    def extract(self, *, path: str, content_type: str | None) -> ExtractedText:
        text = read_text_file(path)
        return ExtractedText(text=text, meta={"source_type": "text"})


