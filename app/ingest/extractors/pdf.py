from __future__ import annotations

from pypdf import PdfReader

from app.ingest.extractors.base import ExtractedText
from app.ingest.extractors.common import ext_lower


class PdfExtractor:
    _exts = {"pdf"}

    def can_handle(self, *, path: str, content_type: str | None) -> bool:
        if content_type == "application/pdf":
            return True
        return ext_lower(path) in self._exts

    def extract(self, *, path: str, content_type: str | None) -> ExtractedText:
        reader = PdfReader(path)
        pages: list[str] = []
        for i, page in enumerate(reader.pages):
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            pages.append(f"[page {i+1}]\n{txt}".strip())
        text = "\n\n".join([p for p in pages if p])
        return ExtractedText(text=text, meta={"source_type": "pdf", "pages": len(reader.pages)})


