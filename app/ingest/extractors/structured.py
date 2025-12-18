from __future__ import annotations

import json

import orjson
import yaml

from app.ingest.extractors.base import ExtractedText
from app.ingest.extractors.common import ext_lower, read_text_file


class StructuredTextExtractor:
    _exts = {"json", "yaml", "yml"}

    def can_handle(self, *, path: str, content_type: str | None) -> bool:
        if content_type in {"application/json", "text/yaml", "application/x-yaml"}:
            return True
        return ext_lower(path) in self._exts

    def extract(self, *, path: str, content_type: str | None) -> ExtractedText:
        raw = read_text_file(path)
        ext = ext_lower(path)
        if ext == "json" or content_type == "application/json":
            # Parse & pretty-print for stable chunking.
            try:
                obj = orjson.loads(raw)
                text = orjson.dumps(obj, option=orjson.OPT_INDENT_2).decode("utf-8")
            except Exception:
                obj2 = json.loads(raw)
                text = json.dumps(obj2, indent=2, ensure_ascii=False)
            return ExtractedText(text=text, meta={"source_type": "json"})

        # YAML
        obj = yaml.safe_load(raw)
        text = yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)
        return ExtractedText(text=text, meta={"source_type": "yaml"})


