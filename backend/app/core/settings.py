from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "rag-augmented-storytelling"
    environment: str = "local"

    # Paths (relative to backend/ by default)
    backend_root: Path = Path(__file__).resolve().parents[2]
    data_dir: Path = backend_root / "data"
    sqlite_path: Path = data_dir / "app.db"
    chroma_dir: Path = data_dir / "chroma"
    kb_files_dir: Path = data_dir / "kb"

    # Embeddings (local HF)
    embedding_model: str = "antoinelouis/colbert-xm"
    embedding_device: str = "cpu"
    embedding_max_length: int = 256

    # Retrieval
    rag_top_k: int = 6
    rag_max_context_chars: int = 12000

    # Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-pro"
    gemini_timeout_s: float = 60.0


settings = Settings()

