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
- Automated pytest suite (API, chunking, mocked `/ask`, optional slow retrieval/index tests)
- Golden evaluation dataset + retrieval Hit Rate@K / MRR harness
- Optional live Gemini generation evaluation (separate from pytest)
- Docker image for reproducible API + indexing runs
- GitHub Actions CI (fast tests + Docker build; no live Gemini)
- Structured JSON logging to `stdout` with configurable `LOG_LEVEL` and `LOG_FORMAT`
- Request correlation via `X-Request-ID` and async `contextvars` propagation
- Stage-level RAG observability (retrieval and generation latency, chunk counts, citation counts)
- Privacy-conscious logging policy (zero logging of questions, chunks, answers, or API keys)

Canonical entry point: `backend/app/main.py`  
Canonical dependencies: `backend/requirements.txt`  
Dev/test dependencies: `backend/requirements-dev.txt`

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
| Gemini model | `gemini-3.6-flash` | `GEMINI_MODEL` |
| Gemini API key | (required for `/ask`) | `GEMINI_API_KEY` |
| Log level | `INFO` | `LOG_LEVEL` |
| Log format | `json` | `LOG_FORMAT` |

`top_k=4` balances enough context for a short sample corpus without flooding the prompt.

**Gemini model choice:** `gemini-3.6-flash` is the project default for grounded `/ask` answers. Override with `GEMINI_MODEL` if needed.

**Distance threshold:** Chroma cosine space returns distances (lower = closer). No hard relevance cutoff is applied yet — choosing one needs evaluation data. The prompt still tells Gemini to refuse when context is insufficient.

## Planned

- Hybrid retrieval and reranking
- Broader automated tests / CI coverage
- Stronger prompt-injection / security controls
- Optional LLM-as-a-judge faithfulness scoring (later iteration)

## Testing and Evaluation

### Automated tests

From `backend/` (Python 3.11 venv active):

```powershell
pip install -r requirements-dev.txt
python -m pytest
```

Fast tests only (skip embedding/Chroma-heavy cases):

```powershell
python -m pytest -m "not slow"
```

What they verify:

- `GET /health` response shape
- `POST /ask` request validation (empty/whitespace/missing/too-long)
- `/ask` wiring with a **fake** RAG service (no live Gemini)
- chunking behaviour (overlap, IDs, invalid config)
- slow tests: temporary-index idempotency and semantic retrieval on a tiny corpus

Production test suites should not call live LLM APIs for basic correctness: LLM output is non-deterministic, slow, costly, and can fail for network/quota reasons unrelated to your code.

### Retrieval evaluation

Requires an already-indexed sample corpus (`python -m app.ingestion.indexer --path data/documents`).

```powershell
python -m evals.evaluate_retrieval
```

Uses `evals/golden_dataset.json`:

- **Hit Rate @ K**: share of answerable questions where at least one top-k chunk contains expected evidence (normalized substring match)
- **MRR**: mean of `1/rank` for the first evidence-bearing chunk (0 if none)

This evidence check is a **lightweight portfolio metric** for a controlled sample document, not a universal semantic relevance judge. Failures print question ID, expected evidence, and ranked chunk previews.

Do not treat scores as “production quality” claims until you measure them locally and understand failures.

### Optional generation evaluation

Requires `GEMINI_API_KEY` and an indexed corpus.

**Important cost/safety notes:**

- `pytest` never calls Gemini
- retrieval evaluation never calls Gemini
- live generation evaluation is an **explicit manual command only**
- by default it runs only **3 cases** to protect limited/free Gemini quotas
- this project never enables billing; quota/billing depends on your Google account/plan
- on 429 rate-limit/quota errors the harness reports the failure and continues (no automatic retries that multiply usage)

```powershell
# Cheapest live check: exactly one Gemini request
python -m evals.evaluate_generation --max-cases 1 --delay-seconds 15 --stop-on-provider-error

# Default small batch (3 cases)
python -m evals.evaluate_generation --max-cases 3 --delay-seconds 15

# Full golden dataset (uses more quota — opt in explicitly)
python -m evals.evaluate_generation --all --delay-seconds 15
```

Before requests begin, the command prints cases, max external requests, timeout, and retry policy.

The Gemini client uses a **60s HTTP timeout** and **disables SDK retries** (`HttpRetryOptions(attempts=1)`). By default google-genai would retry up to 5 times with backoff on 429, which can look like a hang and multiply quota usage.

On 429/timeout the harness reports the failure and continues (or stops with `--stop-on-provider-error`). No automatic retries.

### Current evaluation baseline

Measured locally on Windows / Python 3.11.9 against the small golden dataset (`evals/golden_dataset.json`) and the sample knowledge document.

**Retrieval evaluation (7 answerable cases, top-k = 4):**

| Metric | Result |
|--------|--------|
| Hit Rate @4 | **85.7%** (6/7) |
| MRR | **0.857** |

How to read this:

- This is a **baseline on a small controlled portfolio dataset**, not a production RAG benchmark.
- These scores should **not** be interpreted as general RAG accuracy for arbitrary corpora or domains.
- One retrieval failure is intentionally preserved for analysis: **`ans-006`** (“How does POST /ask use retrieved chunks in this project?”).
- The golden dataset and retrieval settings were **not** changed just to raise the score.
- Improving that miss (for example via chunking or retrieval experiments) is a **future** improvement area.

**Live generation evaluation:**

- Opt-in and cost-conscious (manual command; limited `--max-cases`; no automatic retries).
- A single successful live case was smoke-tested locally; that is **not** a generation-quality benchmark and must not be reported as “100% accuracy.”

Automated pytest: **15 passed** in the same local environment. Dependency/deprecation warnings may appear and currently do not fail the suite.

## Current status

| Item | Status |
|------|--------|
| Indexing pipeline | Implemented |
| Semantic retrieval | Implemented |
| Gemini grounded `/ask` | Implemented |
| Deterministic citations | Implemented |
| Automated tests (pytest) | Implemented |
| Golden dataset + retrieval eval | Implemented |
| Optional generation eval | Implemented |
| LLM-as-a-judge | **Not implemented** (deferred) |
| Docker | Implemented (`backend/Dockerfile`) |
| GitHub Actions CI | Implemented (`.github/workflows/ci.yml`) |
| Observability | Implemented (structured JSON, request correlation, stage timing) |

## Docker

This project ships a **production-oriented** container for the FastAPI backend. It is reproducible local packaging — not a claim that the system is fully production-ready or cloud-deployed.

### Build

From the repository root (or from `backend/` with adjusted paths):

```powershell
cd C:\Users\arzug\production-rag-assistant\backend
docker build -t production-rag-assistant:local .
```

Why `--reload` is not used in the image: reload is for local development (auto-restart on code changes). In a container you want a stable long-running process, clearer logs, and no extra file-watching overhead.

### Persist Chroma data

Do **not** bake `data/vector_store` into the image. Mount a named volume (or bind mount) so the index survives container replacement:

| Concept | Meaning |
|---------|---------|
| Image | Immutable build artifact (code + dependencies) |
| Container filesystem | Ephemeral runtime layer (lost when the container is removed) |
| Volume | Persistent storage outside the container lifecycle |

Example volume name: `rag_vector_store` → `/app/data/vector_store`

### Index sample documents

```powershell
cd C:\Users\arzug\production-rag-assistant\backend
docker run --rm `
  -v rag_vector_store:/app/data/vector_store `
  production-rag-assistant:local `
  python -m app.ingestion.indexer --path data/documents
```

### Run API

Inject secrets at runtime. Never bake `GEMINI_API_KEY` into the image.

Use container-relative paths in `.env` if you set `VECTOR_DB_PATH` / `DOCUMENTS_PATH` (for example `data/vector_store`). Do not pass Windows absolute paths into the container.

```powershell
cd C:\Users\arzug\production-rag-assistant\backend
docker run --rm -p 8000:8000 `
  --env-file .env `
  -v rag_vector_store:/app/data/vector_store `
  production-rag-assistant:local
```

Optional: mount a Hugging Face cache volume so the Sentence Transformer model is not re-downloaded on every fresh container:

`-v hf_cache:/root/.cache/huggingface`

### Test health endpoint

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Continuous Integration

GitHub Actions workflow: `.github/workflows/ci.yml`

On pushes and pull requests to `main`, CI:

1. Sets up **Python 3.11**
2. Installs runtime + development dependencies
3. Runs **fast** automated tests: `pytest -m "not slow"`
4. Performs a lightweight import check
5. Builds the Docker image (build-only; no push/deploy)

CI intentionally does **not**:

- require `GEMINI_API_KEY`
- call Gemini
- run `evals.evaluate_generation`
- consume external LLM quota

Why: normal CI should stay deterministic and cost-free from an LLM-API perspective. Live generation evaluation remains a **manual**, rate-limit-aware command for developers.

Slow semantic/indexing tests (`@pytest.mark.slow`) stay valuable locally; excluding them from default CI avoids large model downloads on every push while keeping the PR feedback loop fast.

## Observability

This project implements lightweight, production-oriented observability using the Python standard library. It avoids heavy tracing dependencies, external daemons, or vendor lock-in.

### Key capabilities

- **Structured JSON logging:** Emits machine-readable single-line JSON logs to `stdout`/`stderr` for natural container capture (Docker, Kubernetes, cloud log routers).
- **Request correlation (`X-Request-ID`):** Generates or reuses a sanitized request correlation ID for every incoming request. The ID is returned in the `X-Request-ID` HTTP response header and injected into all log events during the request lifecycle.
- **Context-local propagation:** Uses `contextvars.ContextVar` to automatically propagate the request correlation ID across async tasks and worker threads without passing `request_id` through every function signature. Tokens are strictly reset in `finally` blocks to prevent state leakage.
- **HTTP request completion logging:** Logs HTTP method, path, status code, duration, and request ID. Routine successful `/health` checks (200 OK) are logged at `DEBUG` level to prevent log flooding in container environments, while degraded health checks are surfaced at `WARNING`/`ERROR`.
- **RAG stage timing:** Uses monotonic clocks (`time.perf_counter()`) to measure distinct pipeline stages:
  - `rag_request_started`: captures question length and retrieval `top_k`.
  - `retrieval_completed`: captures retrieval duration, chunks returned, top-k, and distinct source count.
  - `generation_completed`: captures model name, generation duration, and citation count.
  - `rag_request_completed`: captures end-to-end RAG request latency.
- **Structured error logging:** Categorizes domain failures (`ConfigurationError`, `EmptyKnowledgeBaseError`, `NoRelevantContextError`, `RetrievalError`, `GenerationError`) without printing giant stack traces or sensitive external payload dumps.

### Privacy-conscious logging policy

To safeguard user privacy and prevent credential/data leakage, the logging pipeline strictly enforces a zero-content-logging policy:
- **NEVER logged:** `GEMINI_API_KEY`, Authorization headers, `.env` file contents, full user questions, retrieved document chunks, generated answer text, or embedding vectors.
- **ONLY logged:** Safe diagnostic metadata such as string lengths, counts, durations in milliseconds, HTTP status codes, error categories, and correlation IDs.

### Example structured log lines (synthetic values)

Retrieval completion event:
```json
{
  "timestamp": "2026-09-12T09:30:15.123456Z",
  "level": "INFO",
  "logger": "app.rag",
  "event": "retrieval_completed",
  "request_id": "c9bf9e57-1685-4c89-bafb-ff5af830be8a",
  "top_k": 4,
  "chunks_returned": 4,
  "source_count": 1,
  "duration_ms": 18.7
}
```

Generation completion event:
```json
{
  "timestamp": "2026-09-12T09:30:16.456789Z",
  "level": "INFO",
  "logger": "app.rag",
  "event": "generation_completed",
  "request_id": "c9bf9e57-1685-4c89-bafb-ff5af830be8a",
  "model": "gemini-3.6-flash",
  "citation_count": 2,
  "duration_ms": 612.4
}
```

HTTP request completion event:
```json
{
  "timestamp": "2026-09-12T09:30:16.460123Z",
  "level": "INFO",
  "logger": "app.http",
  "event": "http_request_completed",
  "request_id": "c9bf9e57-1685-4c89-bafb-ff5af830be8a",
  "method": "POST",
  "path": "/ask",
  "status_code": 200,
  "duration_ms": 635.8
}
```

## Documentation

- [`docs/local-development.md`](docs/local-development.md)
- [`docs/backend-dependencies.md`](docs/backend-dependencies.md)
- [`backend/.env.example`](backend/.env.example)
- [`backend/Dockerfile`](backend/Dockerfile)
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
- Learning notes under [`notes/`](notes/)

Supported local runtime: **Python 3.11** (especially on Windows, for Chroma wheels).
