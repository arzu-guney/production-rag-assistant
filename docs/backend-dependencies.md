# Backend Dependencies

This document explains the Python packages used by the backend in **production-rag-assistant**.

## Current dependency file

```text
backend/requirements.txt
```

Install with **Python 3.11** (especially on Windows):

```text
pip install -r requirements.txt
```

## Package groups

### API foundation

| Package | Why it exists |
|---------|----------------|
| `fastapi` | Web API for `/health` and `/ask` |
| `uvicorn[standard]` | ASGI server |
| `python-dotenv` | Load `backend/.env` for local secrets/config |

### Local RAG indexing + retrieval

| Package | Why it exists |
|---------|----------------|
| `pypdf` | PDF text extraction |
| `sentence-transformers` | Local embeddings for documents and queries |
| `chromadb` | Persistent local vector store |
| `posthog` (`>=2.4,<4`) | Direct pin for Chroma compatibility; PostHog 6+/7+ breaks Chroma telemetry `capture()` and causes noisy Client*Event errors |

### Generation

| Package | Why it exists |
|---------|----------------|
| `google-genai` | Current Google Gen AI SDK for Gemini grounded answers |

### Development / tests (`requirements-dev.txt`)

| Package | Why it exists |
|---------|----------------|
| `pytest` | Automated unit and integration tests |
| `httpx` | Required by FastAPI `TestClient` for HTTP API tests |

Install with:

```text
pip install -r requirements-dev.txt
```

## Notes

- Prefer Python 3.11 on Windows so Chroma dependencies can install from prebuilt wheels.
- Do not commit real API keys. Use `.env` locally and `.env.example` as the template.
