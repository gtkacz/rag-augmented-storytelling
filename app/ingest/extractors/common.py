from __future__ import annotations

from pathlib import Path


def ext_lower(path: str) -> str:
    return Path(path).suffix.lower().lstrip(".")


def read_text_file(path: str) -> str:
    p = Path(path)
    # Try utf-8 first, fallback to latin-1 (best-effort for arbitrary user files)
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="latin-1", errors="replace")


