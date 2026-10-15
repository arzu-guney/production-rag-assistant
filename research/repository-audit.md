# Repository Audit for Research Extension

**Author:** Arzu Guney  
**Audit basis:** Inspection of the current `production-rag-assistant` codebase  
**Purpose:** Distinguish **implemented** functionality from **planned** research work  
**Rule:** No experimental features claimed here unless verified in code

---

## 1. Executive summary

The repository is a working production-oriented RAG backend with modular ingestion, dense retrieval, Gemini generation, deterministic citations, offline retrieval evaluation, optional live generation evaluation, automated tests, Docker, and CI. It is suitable as the **host system** for Conditions A/B/C research, but it is **not** yet a complete research evaluation platform: the primary corpus is a single sample document with 11 golden cases; reranking is absent; evidence-based abstention gates are absent; and answer faithfulness metrics are not implemented in the serving path.

---

## 2. Architecture (implemented)

```text
Documents (.txt/.md/.pdf)
  → loaders.py
  → chunking.py (boundary-aware)
  → embeddings.py (SentenceTransformer)
  → vector_store.py (Chroma, cosine)
  → RetrievalService.retrieve()
  → build_context() + prompts
  → GeminiService.generate()
  → AskResponse { answer, sources }
```

Entrypoint: `backend/app/main.py`  
Ask route: `backend/app/routers/ask.py`  
Orchestration: `backend/app/services/rag.py` (`RagService.ask`)  
DI wiring: `backend/app/dependencies.py`

### Technology stack (from `backend/requirements.txt` + code)

| Area | Package / system | Verified default |
|---|---|---|
| API | `fastapi`, `uvicorn` | App title `production-rag-assistant` v0.2.0 |
| Config | `python-dotenv`, Pydantic `Settings` | `backend/app/core/config.py` |
| PDF load | `pypdf` | Per-page extraction |
| Embeddings | `sentence-transformers` | `all-MiniLM-L6-v2` |
| Vector DB | `chromadb` | Persistent, `hnsw:space: cosine` |
| LLM | `google-genai` | Model `gemini-3.6-flash`, temperature `0.2` |

---

## 3. Feature inventory

### 3.1 Implemented and reusable for research

| Feature | Location | Research relevance |
|---|---|---|
| Boundary-aware chunking | `backend/app/ingestion/chunking.py` | Freeze as Condition A indexing |
| Clean re-index | `indexer.py --clean`, `VectorStore.clear()` | Reproducible index builds |
| Local embeddings | `EmbeddingService` | Shared doc/query space |
| Dense top-K retrieval | `RetrievalService` | Condition A retriever |
| Cosine distances on chunks | `RetrievedChunk.distance` | Candidate signal for Condition C |
| Labelled context blocks | `build_context()` | Debugging / faithfulness inspection |
| Prompt grounding + instructed abstention | `SYSTEM_INSTRUCTION` | Condition A abstention baseline |
| Deterministic citations | `_citations_from_chunks()` | Source attribution without LLM invention |
| Offline Hit Rate@K + MRR | `evaluate_retrieval.py`, `evidence.py` | Seed for Recall@K / MRR |
| Optional live generation eval | `evaluate_generation.py` | Concept coverage + abstention heuristic |
| Stage timing logs | `rag.py`, middleware in `main.py` | Latency measurement substrate |
| Fast deterministic tests + CI | `backend/tests/`, `.github/workflows/ci.yml` | Regression safety net |

### 3.2 Documented historical experiment (implemented results, small corpus)

`backend/evals/experiments/chunking_experiment.md` (2026-09-12):

| Metric | Fixed-character baseline | Boundary-aware candidate |
|---|---|---|
| Hit Rate@4 | 85.7% (6/7) | 100.0% (7/7) |
| MRR | 0.857 | 1.000 |
| `ans-006` | rank 5 | rank 1 |

These figures apply only to the 7 answerable cases in `golden_dataset.json`. They are **engineering evidence**, not results for the new research study.

### 3.3 Not implemented (research gaps)

| Gap | Notes |
|---|---|
| Cross-encoder / reranking stage | No rerank module; README lists hybrid/rerank as future work |
| Evidence threshold abstention in runtime | Distances are not used as a refuse gate |
| Confidence field in `AskResponse` | Schema is `{ answer, sources }` only |
| Multi-document research corpus (60–100 Qs) | Only `sample-rag-overview.md` + 11 golden cases |
| Dev/test splits for calibration | Not present |
| Faithfulness / unsupported-answer metrics in harness | Generation eval uses lightweight concept + abstention heuristics only |
| Experiment ID / results artefact store | CLI stdout + markdown notes; no standardised JSON run store |
| Hybrid BM25 | Explicitly out of current implementation |
| AuthN/AuthZ | Explicitly out of scope |

---

## 4. Reliability and safety mechanisms (verified)

| Mechanism | Status | Behaviour |
|---|---|---|
| Prompt: answer only from context | Implemented | Soft constraint on Gemini |
| Prompt: abstain if insufficient | Implemented | Soft; model-dependent |
| Treat retrieved text as untrusted | Implemented | Prompt rules 4–5 |
| Empty knowledge base | Implemented | HTTP 400 |
| Zero retrieved chunks | Implemented | HTTP 404 `NoRelevantContextError` |
| Distance / similarity threshold refuse | **Absent** | Non-empty collections typically still return top-K nearest neighbours |
| NLI / support verification gate | **Absent** | — |
| Post-hoc abstention detector | Eval-only | `looks_like_abstention()` heuristic in `evals/evidence.py` |

**Implication for Condition C:** Evidence-based abstention must be **added** as new runtime logic; it cannot be claimed as existing functionality.

---

## 5. Evaluation and testing (verified)

### Automated tests

- Fast suite: `pytest -m "not slow"` (documented as 35 tests; CI uses this)
- Full suite includes 2 `@pytest.mark.slow` embedding/Chroma cases
- API tests override `get_rag_service` with `FakeRagService` (no Gemini in unit/integration fast path)

### Current golden set

`backend/evals/golden_dataset.json`:

- 11 cases total
- 7 answerable / 4 unanswerable
- Source: `sample-rag-overview.md`
- Evidence matching: normalised substring (`evidence_hit`)

### Metrics currently computed

| Metric | Where | Notes |
|---|---|---|
| Hit Rate@K | `evaluate_retrieval.py` | Answerable only |
| MRR | `evaluate_retrieval.py` | Answerable only |
| Concept coverage | `evaluate_generation.py` | Live Gemini; lightweight |
| Citation present | `evaluate_generation.py` | Checks sample filename |
| Abstention heuristic hits | `evaluate_generation.py` | Unanswerable only; wording-fragile |

**Not currently computed as first-class research metrics:** Faithfulness/Groundedness scores, Unsupported Answer Rate (formal), False Refusal Rate (formal), Recall with chunk-ID labels, calibrated threshold curves.

---

## 6. Reproducibility assets already present

- Config defaults centralised in `get_settings()`
- Deterministic chunk IDs (`make_chunk_id`)
- `--clean` indexing
- Dependency version ranges in `requirements.txt` / `requirements-dev.txt`
- Docker build for backend
- Secret-free CI (no Gemini)
- Structured experiment write-up template (chunking experiment)

### Reproducibility gaps to close before publication runs

- Pin or record exact installed package versions per experiment (`pip freeze` artefact)
- Versioned research dataset card + split files
- Standardised run manifest (experiment ID, git commit, model IDs, \(N\), \(K\), \(\tau\))
- Raw per-case JSON export directory convention
- Explicit CPU-only torch install notes for Linux image size (documented limitation; not a research blocker)

---

## 7. Mapping to experimental conditions

| Condition | What exists today | What must be built later |
|---|---|---|
| **A Baseline RAG** | Full path operational | Research-scale dataset + richer metrics export |
| **B Reranking** | Dense top-K only | Retrieve-\(N\) → cross-encoder → top-\(K\); config flag |
| **C Evidence abstention** | Prompt abstention + distances available | Score definition, dev calibration, runtime gate, response semantics |

---

## 8. Recommendations (documentation-phase only)

1. Treat Condition A as the frozen engineering baseline (boundary-aware chunking + current defaults).
2. Keep the 11-case portfolio set for smoke tests; create a **new** dataset version for research.
3. Implement B and C behind explicit configuration flags without rewriting the FastAPI architecture.
4. Prefer single-variable comparisons for core hypotheses; treat B+C as optional.
5. Do not reinterpret historical Hit Rate 100% (7/7) as a research headline for the new study.

---

## 9. Audit conclusion

**Reuse:** pipeline modules, offline eval harness, tests/CI, observability, citation design, experiment discipline.  
**Extend:** dataset scale, reranking, evidence threshold abstention, reliability metrics, run artefacts.  
**Do not replace:** FastAPI application architecture or the existing modular service boundaries.
