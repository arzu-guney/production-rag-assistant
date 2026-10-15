# Research Track: Evaluating the Reliability of Retrieval-Augmented Generation Systems

**Author:** Arzu Guney  
**Target publication date:** 27 November 2026  
**Host codebase:** [`production-rag-assistant`](../README.md) (existing FastAPI / ChromaDB / Sentence Transformers / Gemini stack)

This directory contains planning and audit documentation for an independent research extension of the existing production-oriented RAG assistant. It does **not** replace the application architecture. Experimental features (reranking, evidence-based abstention gates, expanded datasets) are planned here and will be implemented in later commits.

## Documents

| File | Purpose |
|---|---|
| [`research-proposal.md`](research-proposal.md) | Research question, hypotheses, methodology, metrics, publication plan |
| [`repository-audit.md`](repository-audit.md) | Verified inventory of what the codebase already implements |
| [`experiment-plan.md`](experiment-plan.md) | Conditions A/B/C, controls, dataset plan, metric definitions, reproducibility protocol |

## Current system baseline (verified)

The research baseline reuses the implemented pipeline:

- Boundary-aware chunking (`backend/app/ingestion/chunking.py`)
- Local embeddings: `sentence-transformers/all-MiniLM-L6-v2` (`backend/app/services/embeddings.py`)
- Persistent ChromaDB cosine retrieval (`backend/app/services/vector_store.py`, `retrieval.py`)
- Gemini grounded generation with prompt-based abstention instructions (`backend/app/services/gemini.py`, `backend/app/prompts/__init__.py`)
- Deterministic citations from retrieval metadata (`backend/app/services/rag.py`)
- Offline retrieval evaluation harness (`backend/evals/evaluate_retrieval.py`)
- Optional live generation evaluation (`backend/evals/evaluate_generation.py`)
- Deterministic automated tests and secret-free CI

Default controlled settings (from `backend/app/core/config.py`):

| Setting | Default |
|---|---|
| `CHUNK_SIZE` | 500 |
| `CHUNK_OVERLAP` | 100 |
| `RETRIEVAL_TOP_K` | 4 |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Gemini model | `gemini-3.6-flash` |
| Generation temperature | 0.2 |

## Experimental conditions (planned)

| ID | Condition | Status |
|---|---|---|
| **A** | Baseline RAG (dense top-K + prompt abstention) | **Implemented** in current runtime |
| **B** | RAG with cross-encoder reranking | **Planned** (not implemented) |
| **C** | RAG with evidence-based abstention threshold | **Planned** (not implemented) |
| **A+B / B+C** | Optional combined conditions | **Planned** if schedule allows |

## Important distinctions

- **Retrieval improvements** (e.g. Condition B) are measured primarily with Recall@K / Hit Rate@K and MRR on held-out answerable questions, without requiring abstention gates.
- **Abstention improvements** (Condition C) are measured with Unsupported Answer Rate, False Refusal Rate, and Abstention Rate, using a calibrated threshold on a development split.
- Existing portfolio metrics on the 11-case golden set (`backend/evals/golden_dataset.json`) are **not** research results for the new study. They remain a historical engineering artefact.

## What is intentionally out of scope for this documentation pass

- Implementing reranking or threshold abstention
- Publishing fabricated evaluation numbers
- Replacing FastAPI, Chroma, Sentence Transformers, or Gemini with a new framework stack

## Related existing artefacts

- Engineering experiment log: [`backend/evals/experiments/chunking_experiment.md`](../backend/evals/experiments/chunking_experiment.md)
- Technical writing sample: [`docs/evaluating-retrieval-reliability-chunking-experiment.md`](../docs/evaluating-retrieval-reliability-chunking-experiment.md)
- Project README: [`README.md`](../README.md)
