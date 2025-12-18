from __future__ import annotations

from bs4 import BeautifulSoup

from app.ingest.extractors.base import ExtractedDocument


class HtmlExtractor:
    def can_handle(self, *, filename: str, content_type: str | None) -> bool:
        name = filename.lower()
        if content_type in {"text/html", "application/xhtml+xml"}:
            return True
        return name.endswith((".html", ".htm"))

    def extract(self, *, filename: str, content: bytes, content_type: str | None) -> ExtractedDocument:
        soup = BeautifulSoup(content, "lxml")
        # Remove non-content.
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        return ExtractedDocument(
            text=text,
            meta={"kind": "html", "filename": filename, "title": title},
        )
