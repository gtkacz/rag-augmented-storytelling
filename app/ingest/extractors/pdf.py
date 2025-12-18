from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader

from app.ingest.extractors.base import ExtractedDocument


class PdfExtractor:
    def can_handle(self, *, filename: str, content_type: str | None) -> bool:
        name = filename.lower()
        if content_type == "application/pdf":
            return True
        return name.endswith(".pdf")

    def extract(self, *, filename: str, content: bytes, content_type: str | None) -> ExtractedDocument:
        reader = PdfReader(BytesIO(content))
        texts: list[str] = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                texts.append(t)
        text = "\n\n".join(texts)
        meta = {
            "kind": "pdf",
            "filename": filename,
            "pages": len(reader.pages),
        }
        return ExtractedDocument(text=text, meta=meta)
