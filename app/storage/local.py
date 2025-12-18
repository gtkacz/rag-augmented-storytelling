from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.settings import settings


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


class LocalFileStore:
    def __init__(self) -> None:
        self._root: Path = settings.files_dir

    def put(self, *, kb_id: str, filename: str, content: bytes) -> tuple[str, str, int]:
        sha = sha256_bytes(content)
        size = len(content)
        # Partition by hash to avoid huge single dirs.
        subdir = self._root / kb_id / sha[:2] / sha[2:4]
        subdir.mkdir(parents=True, exist_ok=True)

        safe_name = "_".join(filename.split())
        path = subdir / f"{sha}_{safe_name}"
        path.write_bytes(content)
        return str(path), sha, size
