# Experiment Plan

**Author:** Arzu Guney  
**Study title:** Evaluating the Reliability of Retrieval-Augmented Generation Systems  
**Target publication date:** 27 November 2026  
**Status:** Planning only — Conditions B and C are **not** implemented in the runtime yet

This plan specifies how experiments will be run on top of the existing FastAPI / Chroma / Sentence Transformers / Gemini system. It must stay consistent with [`research-proposal.md`](research-proposal.md) and [`repository-audit.md`](repository-audit.md).

---

## 1. Goals

1. Compare Conditions **A**, **B**, and **C** under controlled variables.
2. Separate **retrieval** effects from **abstention** effects using complementary metrics.
3. Produce reproducible artefacts (configs, raw outputs, aggregates) suitable for a November 2026 write-up.
4. Avoid inventing results: all numeric outcomes are recorded only after actual runs.

---

## 2. System freeze for Condition A (verified defaults)

Unless a later commit deliberately changes and documents them, Condition A uses:

| Parameter | Value | Source |
|---|---|---|
| Chunking strategy | Boundary-aware semantic | `backend/app/ingestion/chunking.py` |
| `CHUNK_SIZE` | 500 | `backend/app/core/config.py` |
| `CHUNK_OVERLAP` | 100 | `config.py` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` | `config.py` / `EmbeddingService` |
| Embedding normalisation | `normalize_embeddings=True` | `embeddings.py` |
| Vector DB | Chroma persistent | `vector_store.py` |
| Similarity | Cosine (`hnsw:space: cosine`) | `vector_store.py` |
| `RETRIEVAL_TOP_K` (\(K\)) | 4 | `config.py` |
| Generator | `gemini-3.6-flash` | `config.py` / `GeminiService` |
| Temperature | 0.2 | `gemini.py` |
| HTTP timeout | 60_000 ms | `gemini.py` |
| SDK retries | 1 (disabled multi-retry) | `gemini.py` |
| Abstention | Prompt instructions only | `SYSTEM_INSTRUCTION` |
| Citations | Deterministic from retrieval metadata | `rag.py` |

**Index rebuild:** `python -m app.ingestion.indexer --path <corpus> --clean`

---

## 3. Experimental conditions

### 3.1 Condition A — Baseline RAG (**implemented**)

1. Embed query with the frozen embedding model.
2. Retrieve top-\(K=4\) neighbours from Chroma.
3. Build labelled context; call Gemini with existing system prompt.
4. Return answer + metadata citations.
5. Abstention occurs only if the model follows prompt rules (or if zero chunks / empty KB errors fire).

### 3.2 Condition B — RAG with Reranking (**planned**)

1. Dense retrieve top-\(N\) candidates (\(N > K\); exact \(N\) fixed before runs, e.g. 20).
2. Score candidates with a **cross-encoder** reranker (model ID pinned in run manifest).
3. Keep top-\(K\) after rerank as generation context.
4. Hold constant: corpus, chunking, embeddings, \(K\), Gemini settings, prompts.
5. Keep prompt-based abstention (same as A) so the independent variable is ranking only.

### 3.3 Condition C — RAG with Evidence-Based Abstention (**planned**)

1. Dense retrieve top-\(K\) (same as A; **no** rerank in the core C contrast).
2. Compute an **evidence score** from retrieval signals (initial candidate: best/mean cosine similarity derived from Chroma distances; exact formula fixed before calibration).
3. Calibrate threshold \(\tau\) on the **development split only**.
4. If evidence score fails \(\tau\), abstain **without** producing a substantive answer (application-level decision).
5. Otherwise generate as in A.
6. Hold constant: corpus, chunking, embeddings, \(K\), Gemini settings when generation occurs.

### 3.4 Optional combined conditions

| ID | Composition | When to run |
|---|---|---|
| **B+C** | Rerank then evidence threshold | Exploratory complementarity; not required for H1/H2 |
| **A-prompt vs C-threshold** | Same retriever, different abstention | Already the A vs C contrast |

Do not expand into BM25 hybrid, multi-reranker bake-offs, or multi-LLM comparisons in the core study.

---

## 4. Distinguishing retrieval vs abstention improvements

### 4.1 Design principle

Change **one** mechanism per core contrast:

| Contrast | Isolates |
|---|---|
| A vs B | Retrieval ranking (rerank) |
| A vs C | Abstention policy (threshold) |
| B vs B+C (optional) | Threshold on top of better ranking |

### 4.2 Metric profile checklist (pre-registered interpretation aid)

After held-out evaluation:

1. Report retrieval metrics for A and B **on the same answerable test items**, using the retrieved contexts **before** abstention logic.
2. Report Unsupported Answer Rate / False Refusal Rate / Abstention Rate for A and C (and optionally B+C).
3. If B improves Recall@K/MRR but Unsupported Answer Rate is unchanged vs A, attribute ranking—not abstention.
4. If C reduces Unsupported Answer Rate with similar Recall@K to A, attribute abstention—not ranking.
5. If both move, require B+C (or staged analysis) before claiming joint benefit; do not collapse both into one narrative.

### 4.3 Abstention labelling

Every case output must record:

- `abstained: true|false`
- `abstention_mechanism: none | prompt_model | evidence_threshold | empty_retrieval | empty_kb | error`
- `evidence_score` and `threshold` when Condition C (or B+C) applies

---

## 5. Dataset plan

### 5.1 Targets

| Property | Plan |
|---|---|
| Size | 60–100 labelled questions |
| Sources | Multiple documents (not only `sample-rag-overview.md`) |
| Types | Answerable + unanswerable |
| Labels | Question, answerability, supporting evidence (phrases and/or chunk/span IDs), optional reference answer concepts |
| Splits | Development (calibration) + held-out test |
| Versioning | Dataset ID + semantic version (e.g. `reliability-v1.0`) |

### 5.2 Split policy

- Development split: threshold tuning for Condition C; optional prompt inspection; **no** final claim metrics.
- Held-out test: all reported A/B/C metrics for publication tables.
- Do not retune \(\tau\) after seeing test results.

### 5.3 Relationship to existing golden set

| Artefact | Role |
|---|---|
| `backend/evals/golden_dataset.json` (11 cases) | Engineering / smoke / historical chunking experiment |
| New research dataset (planned) | Primary corpus for this study |

Do not silently overwrite the 11-case file with research items; add a new versioned path under `backend/evals/` or `research/datasets/` when implementation begins.

### 5.4 No fabricated results

Until the dataset exists and runs complete, papers/docs must not invent Recall@K, MRR, correctness, or abstention rates for Conditions B/C.

---

## 6. Metrics specification

### 6.1 Retrieval metrics

| Metric | Population | Denominator notes |
|---|---|---|
| **Recall@K / Hit Rate@K** | Answerable test questions | 1 if any labelled evidence appears in top-\(K\) chunks |
| **MRR** | Answerable test questions | \(1/\mathrm{rank}\) of first evidence hit; 0 if miss within retrieved set |

These are **retrieval-stage** metrics. Compute them from retriever output even when Condition C would later abstain (store both “raw retrieval” and “post-gate” views if needed).

### 6.2 Generation / reliability metrics

| Metric | Population | Handling of abstentions |
|---|---|---|
| **Answer Correctness** | Answerable ∩ answered | Abstentions excluded from denominator (primary); optionally report secondary policy-aware score |
| **Faithfulness / Groundedness** | Answered questions | Abstentions excluded; protocol fixed before runs |
| **Unsupported Answer Rate** | Unanswerable | Abstention = not unsupported (good); non-abstaining answer = unsupported (bad) |
| **False Refusal Rate** | Answerable | Abstention = false refusal (bad) |
| **Abstention Rate** | All / stratified | Report overall and by answerability |
| **Latency** | All successful pipeline executions | Report p50/p95 if sample size allows; always report mean stage times |

### 6.3 Mapping metrics to conditions

| Metric | A | B | C |
|---|---|---|---|
| Recall@K, MRR | Yes | Yes (primary contrast) | Yes (should match A if retriever unchanged) |
| Answer Correctness, Faithfulness | Yes | Yes | Yes (answered only) |
| Unsupported / False Refusal / Abstention Rate | Yes | Yes (expect ≈ A if prompt-only) | Yes (primary contrast) |
| Latency | Yes | Yes (expect rerank cost) | Yes (expect cheap gate + fewer generations if abstain) |

---

## 7. Reproducibility protocol

### 7.1 Record for every run

Create a run manifest (JSON) including at least:

```text
experiment_id          e.g. 2026-XX-XX_cond-B_reliability-v1.0_test
git_commit             full SHA
dataset_id / version
split                  dev | test
condition              A | B | C | B+C
chunk_size / overlap / chunking_strategy
embedding_model_id
vector_space
K                      final context size
N                      candidate pool (B / B+C only)
reranker_model_id      (B / B+C only)
evidence_score_def     (C / B+C only)
threshold_tau          (C / B+C only; from dev calibration)
gemini_model_id
temperature
prompt_version         hash or filename+commit
hardware_notes         CPU/GPU, OS
dependency_lock        pip freeze artefact path
started_at / finished_at (UTC)
```

### 7.2 Raw results format

Per-case JSONL or JSON array with fields such as:

- `case_id`, `answerable`, `question`
- `retrieved_chunk_ids`, `ranks`, `distances` / similarities
- `evidence_hit`, `first_evidence_rank`
- `abstained`, `abstention_mechanism`, `evidence_score`, `threshold`
- `answer` (omit or redact if privacy policy requires; research corpus should be non-sensitive)
- `sources`
- `latency_ms` stages
- `condition`, `experiment_id`

Aggregate CSV/Markdown tables derived only from these raw files.

### 7.3 Suggested artefact layout (to create during implementation phase)

```text
research/runs/<experiment_id>/
  manifest.json
  pip-freeze.txt
  cases.jsonl
  summary.json
  notes.md
```

*(Directories above are planned; not created in this documentation-only pass beyond `research/*.md`.)*

### 7.4 Model and version discipline

- Pin embedding and reranker model IDs exactly as Hub identifiers.
- Record Gemini model string from settings at runtime.
- Prefer documenting installed `sentence-transformers`, `chromadb`, `torch`, `google-genai` versions via freeze files.
- Do not change generation temperature between conditions unless that change is itself an experiment (out of core scope).

---

## 8. Execution checklist (future implementation order)

1. Author and version the research dataset + splits (no results yet).
2. Extend offline retrieval export (per-case ranks/distances) without changing runtime behaviour.
3. Implement Condition B behind a config flag; A vs B retrieval evaluation on test.
4. Define evidence score; calibrate \(\tau\) on development; implement Condition C gate.
5. Evaluate A vs C reliability metrics on test; optionally B+C.
6. Freeze figures/tables for the 27 November 2026 publication draft.

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Threshold overfit | Dev-only calibration; single test peek for reporting |
| Tiny effect sizes on small \(n\) | Target 60–100 questions; report CIs or at least absolute counts |
| Gemini quota / flakiness | Bounded live eval; retries disabled; cache optional offline judgements |
| Confounding chunking changes | Freeze boundary-aware settings for all conditions |
| Scope creep (hybrid search, multi-agent) | Defer; not required for H1–H3 |

---

## 10. Consistency statement

This plan aligns with:

- Primary research question and H1–H3 in `research-proposal.md`
- Verified implemented vs missing features in `repository-audit.md`
- Existing runtime defaults in `backend/app/core/config.py` and related services

No Condition B/C code or fabricated evaluation numbers are introduced by this document.
