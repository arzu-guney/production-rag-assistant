# production-rag-assistant

A step-by-step **Applied AI Engineering** project. This repository is being developed into a **production-oriented RAG application** and a **public learning resource**.

It is built slowly and deliberately: each step should be understandable before the next layer is added.

This is **not** a finished production-ready system. It is a production-oriented learning project with a working local RAG path.

## Project goal

Learn how Retrieval-Augmented Generation (RAG) works by building a small assistant that can answer questions using my own documents — with room later for evaluation, observability, Docker, and CI/CD.

## A very simple explanation of RAG

**RAG** stands for **Retrieval-Augmented Generation**.

1. Index your documents (chunk → embed → store).
2. When someone asks a question, **retrieve** relevant chunks.
3. Send those chunks to a language model as **context**.
4. The model **generates** an answer grounded in that context.
5. Return **citations** from the retrieved chunks.

## Currently implemented

- FastAPI backend (`GET /health`, `POST /ask`)
- Typed Pydantic request/response models and validation
- Document loading for `.txt`, `.md`, `.pdf`
- Configurable chunking with overlap
- Local Sentence Transformers embeddings
- Persistent ChromaDB vector indexing with metadata
- Semantic retrieval (query embedding + top-k nearest chunks)
- Structured context construction
- Gemini grounded answer generation
- Deterministic source citations from retrieval metadata
- Basic empty-collection / missing-key / generation error handling

Canonical entry point: `backend/app/main.py`  
Canonical dependencies: `backend/requirements.txt`

### Ask flow

```text
POST /ask
  → embed question (local)
  → retrieve top-k chunks (Chroma)
  → build labelled context
  → generate answer (Gemini)
  → return answer + citations from retrieved chunks
```

Example response shape:

```json
{
  "answer": "...",
  "sources": [
    {
      "source": "sample-rag-overview.md",
      "page": null,
      "chunk_id": "chunk_..."
    }
  ]
}
```

### Local setup (Windows / Python 3.11)

```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and set GEMINI_API_KEY=...

python -m app.ingestion.indexer --path data/documents
uvicorn app.main:app --reload
```

Then:

- Health: `http://127.0.0.1:8000/health`
- Ask: `POST http://127.0.0.1:8000/ask` with `{"question":"..."}`
- Docs: `http://127.0.0.1:8000/docs`

Indexing is separate from asking. Questions reuse the existing Chroma collection; they do **not** re-index documents.

### Configuration defaults

| Setting | Default | Env var |
|---------|---------|---------|
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | `EMBEDDING_MODEL_NAME` |
| Chunk size / overlap | `500` / `100` | `CHUNK_SIZE` / `CHUNK_OVERLAP` |
| Vector DB path | `backend/data/vector_store` | `VECTOR_DB_PATH` |
| Collection | `documents` | `COLLECTION_NAME` |
| Retrieval top_k | `4` | `RETRIEVAL_TOP_K` |
| Gemini model | `gemini-2.0-flash` | `GEMINI_MODEL` |
| Gemini API key | (required for `/ask`) | `GEMINI_API_KEY` |

`top_k=4` balances enough context for a short sample corpus without flooding the prompt.

**Gemini model choice:** `gemini-2.0-flash` is fast and cost-efficient for a portfolio demo. Override with `GEMINI_MODEL` if needed.

**Distance threshold:** Chroma cosine space returns distances (lower = closer). No hard relevance cutoff is applied yet — choosing one needs evaluation data. The prompt still tells Gemini to refuse when context is insufficient.

## Planned

- Automated RAG evaluation / golden dataset / retrieval metrics
- Hybrid retrieval and reranking
- Observability
- Comprehensive automated tests
- Docker and CI/CD
- Stronger prompt-injection / security controls

## Current status

| Item | Status |
|------|--------|
| Indexing pipeline | Implemented |
| Semantic retrieval | Implemented |
| Gemini grounded `/ask` | Implemented |
| Deterministic citations | Implemented |
| Evaluation / tests / Docker / CI | **Not implemented** |

## Documentation

- [`docs/local-development.md`](docs/local-development.md)
- [`docs/backend-dependencies.md`](docs/backend-dependencies.md)
- [`backend/.env.example`](backend/.env.example)
- Learning notes under [`notes/`](notes/)

Supported local runtime: **Python 3.11** (especially on Windows, for Chroma wheels).
