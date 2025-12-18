from __future__ import annotations

import json

from app.ingest.extractors.base import ExtractedDocument


class JsonExtractor:
    def can_handle(self, *, filename: str, content_type: str | None) -> bool:
        name = filename.lower()
        if content_type == "application/json":
            return True
        return name.endswith(".json")

    def extract(self, *, filename: str, content: bytes, content_type: str | None) -> ExtractedDocument:
        obj = json.loads(content.decode("utf-8", errors="replace"))
        text = json.dumps(obj, ensure_ascii=False, indent=2)
        return ExtractedDocument(text=text, meta={"kind": "json", "filename": filename})
