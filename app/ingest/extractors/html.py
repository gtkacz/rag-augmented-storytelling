from __future__ import annotations

from bs4 import BeautifulSoup

from app.ingest.extractors.base import ExtractedText
from app.ingest.extractors.common import ext_lower, read_text_file


class HtmlExtractor:
    _exts = {"html", "htm"}

    def can_handle(self, *, path: str, content_type: str | None) -> bool:
        if content_type in {"text/html", "application/xhtml+xml"}:
            return True
        return ext_lower(path) in self._exts

    def extract(self, *, path: str, content_type: str | None) -> ExtractedText:
        raw = read_text_file(path)
        soup = BeautifulSoup(raw, "html.parser")
        # Remove scripts/styles for cleaner text.
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text("\n")
        return ExtractedText(text=text, meta={"source_type": "html"})


