# rag-augmented-storytelling

Local-first backend for **RAG-enhanced storytellers**: users upload arbitrary “world” knowledge, the backend indexes it locally, and `/query` retrieves context + calls Gemini to generate grounded responses.

## Backend (FastAPI)

### Setup

From the repo root:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Set environment variables (PowerShell):

```powershell
$env:GEMINI_API_KEY="YOUR_KEY"
$env:GEMINI_MODEL="gemini-1.5-pro"
$env:EMBEDDING_MODEL="antoinelouis/colbert-xm"
$env:EMBEDDING_DEVICE="cpu"
```

Run:

```bash
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Data layout (local)
- **SQLite**: `backend/data/app.db`
- **Files**: `backend/data/kb/<kb_id>/raw/<doc_id>/...`
- **Artifacts**: `backend/data/kb/<kb_id>/artifacts/<doc_id>/extracted.txt`
- **Chroma**: `backend/data/chroma/`

### API usage (curl)

Create a knowledge base:

```bash
curl -X POST http://127.0.0.1:8000/kbs -H "Content-Type: application/json" -d "{\"name\":\"my_world\",\"description\":\"campaign lore\"}"
```

Upload documents:

```bash
curl -X POST http://127.0.0.1:8000/kbs/<kb_id>/documents -F "files=@world.md" -F "files=@notes.pdf"
```

Start ingestion:

```bash
curl -X POST http://127.0.0.1:8000/kbs/<kb_id>/documents/<doc_id>/ingest
```

Check job:

```bash
curl http://127.0.0.1:8000/kbs/<kb_id>/jobs/<job_id>
```

Query (RAG + Gemini):

```bash
curl -X POST http://127.0.0.1:8000/kbs/<kb_id>/query -H "Content-Type: application/json" -d "{\"question\":\"Who rules the city of Veyra?\",\"top_k\":6}"
```