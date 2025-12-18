## RAG-augmented storytelling

Backend: FastAPI + Qdrant + local Hugging Face embeddings.
Frontend: Streamlit.

### Requirements
- Python **3.13+**
- [`uv`](https://github.com/astral-sh/uv)
- Qdrant running locally (default `http://localhost:6333`)

### Setup
- Copy `env.example` to `.env` and adjust values.

### Install
```bash
uv sync
```

### Run API
```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Run Streamlit
```bash
uv run streamlit run streamlit_app.py
```

### Lint/format
```bash
uv run ruff check .
uv run ruff format .
```

### Notes
- Each knowledge base uses a separate Qdrant collection (`kb_{kb_id}`).
- Uploaded files are stored under `DATA_DIR/files/`.
