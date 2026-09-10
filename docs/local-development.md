# Local Development Guide

This guide explains how to run the **production-oriented** RAG backend in **production-rag-assistant** on Windows (Command Prompt or PowerShell).

Supported runtime: **Python 3.11**.

---

## What works today

- Index local documents into ChromaDB
- Ask questions with `POST /ask` (retrieve → Gemini → citations)
- `GET /health` liveness check

This is not a production-ready deployment guide. It is local development only.

---

## Prerequisites

- **Python 3.11**
- **Git**
- Repository cloned locally
- A **Gemini API key** for `/ask`

Python 3.12+ on Windows may fail installing `chroma-hnswlib` without a C++ compiler. Use 3.11 instead. Visual C++ Build Tools are **not** a project prerequisite.

```text
python --version
```

Expect `3.11.x`.

---

## Setup steps

### 1. Open the backend folder

```powershell
cd path\to\production-rag-assistant\backend
```

### 2. Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
copy .env.example .env
```

Edit `.env` and set:

```text
GEMINI_API_KEY=your_real_key_here
```

Optional:

```text
GEMINI_MODEL=gemini-2.0-flash
RETRIEVAL_TOP_K=4
```

Never commit `.env`.

### 5. Index the sample document

```powershell
python -m app.ingestion.indexer --path data/documents
```

Expected: only `sample-rag-overview.md` is loaded (about 5 chunks). Re-running should keep collection size stable.

### 6. Run the API

```powershell
uvicorn app.main:app --reload
```

### 7. Call the endpoints

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Ask:

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/ask `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"question":"What is retrieval-augmented generation?"}'
```

Interactive docs: `http://127.0.0.1:8000/docs`

Asking a question does **not** re-index documents. It reuses `data/vector_store`.

---

## Troubleshooting

### Wrong Python / Chroma install fails

Recreate the venv with Python 3.11:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Missing Gemini key

`/ask` should return HTTP 503 with a clear message if `GEMINI_API_KEY` is missing.

### Empty knowledge base

If you never indexed (or deleted `data/vector_store`), `/ask` should return HTTP 400 telling you to index documents first.

### Port already in use

Stop the other process using port 8000, or restart Uvicorn in a fresh terminal.
