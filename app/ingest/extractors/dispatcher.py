from __future__ import annotations

from app.ingest.extractors.base import ExtractedDocument, Extractor
from app.ingest.extractors.html import HtmlExtractor
from app.ingest.extractors.pdf import PdfExtractor
from app.ingest.extractors.plaintext import PlaintextExtractor
from app.ingest.extractors.structured import JsonExtractor


class ExtractorDispatcher:
    def __init__(self) -> None:
        self._extractors: list[Extractor] = [
            PlaintextExtractor(),
            HtmlExtractor(),
            PdfExtractor(),
            JsonExtractor(),
        ]

    def extract(self, *, filename: str, content: bytes, content_type: str | None) -> ExtractedDocument:
        for ex in self._extractors:
            if ex.can_handle(filename=filename, content_type=content_type):
                return ex.extract(filename=filename, content=content, content_type=content_type)
        # Fallback: treat as utf-8 text.
        text = content.decode("utf-8", errors="replace")
        return ExtractedDocument(text=text, meta={"kind": "fallback_text", "filename": filename})
