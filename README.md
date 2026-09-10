# production-rag-assistant

A step-by-step **Applied AI Engineering** project. This repository is being developed into a **production-oriented RAG application** and a **public learning resource**.

It is built slowly and deliberately: each step should be understandable before the next layer is added.

This is **not** a finished production system today. The long-term goal is a production-oriented RAG assistant with evaluation, observability, and solid engineering habits.

## Project goal

Learn how Retrieval-Augmented Generation (RAG) works by building a small assistant that can answer questions using my own documents — with room later for tests, evaluation, Docker, and CI/CD.

The name refers to patterns I want to practise over time. It does **not** mean the repository is production-ready yet.

## Why I am building this project

I want a dedicated place to practise Applied AI Engineering from the ground up:

- Commit small, reviewable steps
- Keep learning notes next to the code
- Build something real over time instead of only running one-off demos
- Keep a clear line between what is implemented and what is still planned

## A very simple explanation of RAG

**RAG** stands for **Retrieval-Augmented Generation**.

In plain language:

1. You have documents (notes, PDFs, wiki pages, etc.).
2. When someone asks a question, the system **finds** useful pieces of text in those documents.
3. Those pieces are sent to a language model as **context**.
4. The model **generates** an answer using that context.

Simple analogy: **look up relevant notes first, then answer using those notes.**

A language model does not automatically know your private files. RAG is how you give it the right excerpts at question time.

**Important:** RAG **indexing** (load → chunk → embed → store) is implemented locally. Semantic retrieval and LLM answer generation for `/ask` are **not** implemented yet.

## Currently implemented

What exists in the codebase today:

- A FastAPI backend foundation under `backend/`
- `GET /health` liveness endpoint
- Typed `POST /ask` API contract with Pydantic request/response models (still a **placeholder** answer)
- Document loading for `.txt`, `.md`, and `.pdf`
- Text extraction (including PDF page-level extraction when text is available)
- Configurable character chunking with overlap
- Local embedding generation via Sentence Transformers (no external API key required)
- Persistent vector indexing with ChromaDB
- Metadata preservation (source path/name, document type, page number, chunk index)
- Local development documentation and learning notes

Canonical backend entry point:

```text
backend/app/main.py
```

Canonical dependency file:

```text
backend/requirements.txt
```

### API endpoints

`GET /health` returns:

```json
{
  "status": "ok",
  "service": "production-rag-assistant"
}
```

`POST /ask` accepts a typed question body but currently returns an honest **placeholder** response. It does **not** retrieve from the vector store or call an LLM yet.

### Local document indexing

Index sample documents (from the `backend/` directory):

```text
python -m app.ingestion.indexer --path data/documents
```

This runs:

`documents → text extraction → chunking → embeddings → ChromaDB persistence`

Default settings (overridable by environment variables):

| Setting | Default | Env var |
|---------|---------|---------|
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | `EMBEDDING_MODEL_NAME` |
| Chunk size | `500` characters | `CHUNK_SIZE` |
| Chunk overlap | `100` characters | `CHUNK_OVERLAP` |
| Vector DB path | `backend/data/vector_store` | `VECTOR_DB_PATH` |
| Collection name | `documents` | `COLLECTION_NAME` |

The persisted vector database under `backend/data/vector_store/` is **gitignored** and must not be committed.

Sample document: `backend/data/documents/sample-rag-overview.md`

## Planned

The following are **planned next** and are **not implemented yet**:

- Semantic retrieval for `/ask`
- Context construction
- LLM answer generation
- Source citations from retrieved chunks
- Evaluation
- Observability
- Docker
- CI/CD
- Tests

Additional later topics may include security experiments. Retrieval and generation are the next major steps.

## Current status

| Item | Status |
|------|--------|
| GitHub repository | Active |
| FastAPI backend foundation | Implemented |
| `GET /health` | Implemented |
| Typed `POST /ask` API contract | Implemented (**placeholder** response) |
| Document loading (txt/md/pdf) | Implemented |
| Text extraction | Implemented |
| Configurable chunking | Implemented |
| Local embeddings (Sentence Transformers) | Implemented |
| Persistent ChromaDB indexing | Implemented |
| Metadata preservation | Implemented |
| Semantic retrieval wired to `/ask` | **Not implemented** |
| LLM answer generation | **Not implemented** |
| Real source citations | **Not implemented** |
| Tests / evaluation / Docker / CI/CD | **Not implemented** |

## Local Development

**Supported local runtime: Python 3.11** (especially on Windows).

This project uses ChromaDB for local vector storage. On Windows, Python 3.12+ may fail during `pip install` when `chroma-hnswlib` has no compatible prebuilt wheel. Use Python 3.11 so installs stay reproducible without a C++ compiler.

You can run the current FastAPI backend on your own computer. The backend currently exposes `GET /health` and a typed `POST /ask` placeholder contract.

To build the local vector index from sample documents, see the indexing command in **Currently implemented**.

For API setup steps, see [`docs/local-development.md`](docs/local-development.md).

## Backend Dependencies

The packages needed to run the backend are documented in [`docs/backend-dependencies.md`](docs/backend-dependencies.md).

Dependencies now also include local RAG indexing libraries: `pypdf`, `sentence-transformers`, and `chromadb`.

## Learning notes

Day-by-day notes are kept as a public learning resource:

- [`notes/day-1a.md`](notes/day-1a.md)
- [`notes/day-1b.md`](notes/day-1b.md)
- [`notes/day-1c.md`](notes/day-1c.md)
- [`notes/day-1e.md`](notes/day-1e.md)
- [`notes/day-1f.md`](notes/day-1f.md)
- [`notes/day-1g.md`](notes/day-1g.md)
- [`notes/day-1h.md`](notes/day-1h.md)
- [`notes/day-1i.md`](notes/day-1i.md)
- [`notes/day-1k.md`](notes/day-1k.md)

These notes explain early backend concepts. They do not imply that RAG features have been built.
