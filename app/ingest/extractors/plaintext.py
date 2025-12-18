from __future__ import annotations

from app.ingest.extractors.base import ExtractedDocument


class PlaintextExtractor:
    def can_handle(self, *, filename: str, content_type: str | None) -> bool:
        name = filename.lower()
        if content_type and content_type.startswith("text/"):
            return True
        return name.endswith((".txt", ".md", ".markdown"))

    def extract(self, *, filename: str, content: bytes, content_type: str | None) -> ExtractedDocument:
        text = content.decode("utf-8", errors="replace")
        return ExtractedDocument(text=text, meta={"kind": "plaintext", "filename": filename})
