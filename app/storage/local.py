from __future__ import annotations

import re
from pathlib import Path

from fastapi import UploadFile

from app.core.settings import settings


_FILENAME_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def safe_filename(name: str) -> str:
    name = name.strip().replace("\\", "_").replace("/", "_")
    name = _FILENAME_SAFE.sub("_", name)
    return name or "file"


def kb_dir(kb_id: str) -> Path:
    return settings.kb_files_dir / kb_id


def doc_raw_dir(kb_id: str, doc_id: str) -> Path:
    return kb_dir(kb_id) / "raw" / doc_id


def doc_artifacts_dir(kb_id: str, doc_id: str) -> Path:
    return kb_dir(kb_id) / "artifacts" / doc_id


def save_upload(kb_id: str, doc_id: str, upload: UploadFile) -> Path:
    target_dir = doc_raw_dir(kb_id, doc_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    fname = safe_filename(upload.filename or "upload")
    target_path = target_dir / fname

    with target_path.open("wb") as f:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)

    return target_path


def write_extracted_text(kb_id: str, doc_id: str, text: str) -> Path:
    target_dir = doc_artifacts_dir(kb_id, doc_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "extracted.txt"
    path.write_text(text, encoding="utf-8")
    return path


def read_extracted_text(kb_id: str, doc_id: str) -> str | None:
    path = doc_artifacts_dir(kb_id, doc_id) / "extracted.txt"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


