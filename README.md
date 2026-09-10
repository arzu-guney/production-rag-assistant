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

**Important:** the explanation above describes the target design. RAG is **not implemented in this repository yet**.

## Currently implemented

What exists in the codebase today:

- A FastAPI backend foundation under `backend/`
- One endpoint: `GET /health`
- Local development documentation
- Backend dependency documentation
- Beginner-friendly learning notes for Day 1 topics

Canonical backend entry point:

```text
backend/app/main.py
```

Canonical dependency file:

```text
backend/requirements.txt
```

`GET /health` returns a response similar to:

```json
{
  "status": "ok",
  "service": "production-rag-assistant"
}
```

This health check confirms that the backend process starts and can respond to HTTP requests. It does **not** mean RAG is working.

## Planned

The following are **planned next** and are **not implemented yet**:

- Typed Q&A API
- Document ingestion
- Chunking
- Embeddings
- Vector indexing
- Retrieval
- LLM answer generation
- Source citations
- Tests
- Evaluation
- Docker
- CI/CD

Additional later topics may include observability and security experiments. None of those exist in the application code today.

## Current status

| Item | Status |
|------|--------|
| GitHub repository | Active |
| FastAPI backend foundation | Implemented (`backend/app/main.py`) |
| `GET /health` | Implemented |
| Local development docs | Implemented (`docs/local-development.md`) |
| Backend dependency docs | Implemented (`docs/backend-dependencies.md`) |
| Learning notes | In progress (`notes/`) |
| Working RAG application | **Not implemented** |
| Document ingestion / embeddings / vector DB | **Not implemented** |
| LLM integration / Q&A API | **Not implemented** |
| Tests / evaluation / Docker / CI/CD | **Not implemented** |

## Local Development

You can run the current FastAPI backend on your own computer. The backend only exposes a minimal `GET /health` endpoint so far.

For setup steps, see [`docs/local-development.md`](docs/local-development.md).

## Backend Dependencies

The packages needed to run the backend are documented in [`docs/backend-dependencies.md`](docs/backend-dependencies.md).

Dependencies currently support the FastAPI health endpoint only.

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
