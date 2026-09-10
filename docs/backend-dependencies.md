# Backend Dependencies

This document explains the Python packages used by the backend in **production-rag-assistant**.

## Current dependency file

Packages are listed in:

```text
backend/requirements.txt
```

Install from the `backend/` directory:

```text
pip install -r requirements.txt
```

## Package groups

### API foundation

| Package | Why it exists |
|---------|----------------|
| `fastapi` | Web API framework for `/health` and `/ask` |
| `uvicorn[standard]` | ASGI server that runs the FastAPI app |

### Local RAG indexing (Commit 3)

| Package | Why it exists |
|---------|----------------|
| `pypdf` | Extract text from PDF files during document loading |
| `sentence-transformers` | Create local embeddings without an external API key |
| `chromadb` | Persist chunk text, embeddings, and metadata locally |

## What this project does not use yet for answers

`/ask` still returns a placeholder. The following are **not** wired yet:

- Semantic retrieval into `/ask`
- LLM APIs for answer generation
- Cloud embedding providers (OpenAI, Gemini, etc.)

## Key Takeaway

`requirements.txt` lists everything needed to run the API and the local indexing pipeline. Another developer can recreate the environment with one install command after cloning the repository.
