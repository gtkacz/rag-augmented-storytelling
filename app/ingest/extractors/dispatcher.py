from __future__ import annotations

from pathlib import Path

from app.ingest.extractors.base import ExtractedText, Extractor
from app.ingest.extractors.html import HtmlExtractor
from app.ingest.extractors.pdf import PdfExtractor
from app.ingest.extractors.plaintext import PlainTextExtractor
from app.ingest.extractors.structured import StructuredTextExtractor


class ExtractorDispatcher:
    def __init__(self) -> None:
        self._extractors: list[Extractor] = [
            PdfExtractor(),
            HtmlExtractor(),
            StructuredTextExtractor(),
            PlainTextExtractor(),
        ]

    def extract(self, *, path: str, content_type: str | None) -> ExtractedText:
        for ext in self._extractors:
            if ext.can_handle(path=path, content_type=content_type):
                out = ext.extract(path=path, content_type=content_type)
                # Always attach file name for citations.
                out.meta.setdefault("source_name", Path(path).name)
                return out

        # Fallback: best-effort decode as text.
        data = Path(path).read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1", errors="replace")
        return ExtractedText(text=text, meta={"source_type": "fallback", "source_name": Path(path).name})


