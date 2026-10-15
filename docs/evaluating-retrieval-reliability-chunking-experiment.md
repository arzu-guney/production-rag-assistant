# Evaluating Retrieval Reliability in a Production-Oriented RAG System: A Controlled Chunking Experiment

**Author:** Arzu Guney  

**Technical project report** based on the open repository [`production-rag-assistant`](https://github.com/arzu-guney/production-rag-assistant).

This document is a writing sample derived from implemented code and recorded evaluation artefacts. It is **not** a peer-reviewed publication and does not claim general production accuracy beyond the controlled corpus described below.

**Primary evidence sources (repository):**

- `README.md`
- `backend/evals/experiments/chunking_experiment.md`
- `backend/evals/golden_dataset.json`
- `backend/evals/evaluate_retrieval.py`, `backend/evals/evidence.py`
- `backend/app/ingestion/chunking.py`
- `backend/app/core/config.py`, `backend/app/services/retrieval.py`, `backend/app/services/rag.py`
- `backend/tests/` and `.github/workflows/ci.yml`

---

## Abstract

Retrieval-Augmented Generation (RAG) systems depend on reliable retrieval: if the correct evidence is not ranked highly enough, grounded generation cannot succeed regardless of language-model quality. This report describes a production-oriented RAG backend and a controlled experiment that isolates one retrieval design choice—document chunk boundary strategy—while holding chunk size, overlap, embedding model, vector similarity metric, retrieval depth, and evaluation dataset constant.

On a small golden set of seven answerable questions over a single sample knowledge document, fixed-character windowing achieved Hit Rate@4 of 85.7% (6/7) and Mean Reciprocal Rank (MRR) of 0.857. The sole failure, case `ans-006`, ranked the needed evidence at position 5 (outside `top_k=4`) after character slicing severed an expected evidence phrase across chunk boundaries. Replacing fixed-character slicing with boundary-aware semantic chunking improved Hit Rate@4 to 100.0% (7/7) and MRR to 1.000; `ans-006` moved from rank 5 to rank 1 with no regressions on the other six answerable cases.

These results demonstrate a measurable, single-variable reliability improvement on a controlled portfolio corpus. They are not a claim of universal RAG accuracy. The report also documents how offline retrieval evaluation, deterministic automated tests, and separation of live LLM calls support reproducible engineering practice.

---

## 1. Introduction and Motivation

RAG pipelines combine three stages: (1) indexing documents into a vector store, (2) retrieving nearest chunks for a query, and (3) generating an answer conditioned on retrieved context. In practice, generation quality is bounded by retrieval reliability. A language model cannot ground an answer in evidence that never entered the prompt.

Chunking is a central indexing decision. Large documents are split into windows before embedding. If windows cut mid-sentence or mid-word, embeddings can represent fragmented text, and expected evidence strings may be broken across adjacent chunks. Overlap mitigates some boundary loss, but fixed character offsets can still place a clean break inside a critical phrase.

The repository under study implements an end-to-end RAG API with local embeddings, persistent vector storage, grounded generation via Google Gemini, deterministic source citations assembled from retrieval metadata, offline golden-set retrieval evaluation, automated tests that do not call the LLM, Docker packaging, and secret-free continuous integration. Within that system, a documented failure on one golden-set case motivated a controlled chunking experiment rather than an ad hoc multi-parameter retune.

The goals of this report are to:

1. summarise the system architecture as implemented;
2. describe the golden-set retrieval evaluation methodology;
3. reconstruct the controlled chunking experiment from repository evidence;
4. report measured baseline and candidate metrics;
5. discuss reliability and reproducibility implications, including explicit limitations.

---

## 2. System Architecture

The backend is organised as a modular FastAPI application (Python 3.11) with clear separation between ingestion, retrieval, generation, evaluation, and testing.

### 2.1 Ingestion and indexing

Source documents under `backend/data/documents/` (currently the sample Markdown file `sample-rag-overview.md`) are loaded, chunked, embedded, and stored in a persistent ChromaDB collection. Default configuration values from `backend/app/core/config.py` are:

| Setting | Default |
|---|---|
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Chunk size | 500 characters |
| Chunk overlap | 100 characters |
| Retrieval depth | `top_k = 4` |
| Vector space | Cosine (`hnsw:space: cosine` in Chroma) |

Embeddings are produced locally by Sentence Transformers so that document and query vectors share the same model and vector space without an embedding API. Indexing and retrieval evaluation therefore incur no Gemini quota.

### 2.2 Query path

`POST /ask` orchestrates:

1. **Retrieval** — embed the question; query Chroma for the nearest `top_k` chunks.
2. **Context construction** — assemble labelled chunk text for the prompt.
3. **Generation** — call Gemini with a grounded system instruction and the retrieved context.
4. **Citation assembly** — build source citations from retrieval metadata (source name, page, chunk ID), not from free-form LLM text.

This citation design is intentional: source attribution is treated as an application responsibility rather than a generative claim.

### 2.3 Observability and packaging

The service emits structured JSON logs to `stdout`, correlates requests with `X-Request-ID` via `contextvars.ContextVar`, and records stage timings with `time.perf_counter()`. Sensitive payloads (user questions, document text, answers, embeddings, API keys) are excluded from logs. The backend is packaged with Docker (`python:3.11-slim`); vector store data is kept out of the image and mounted as a volume for persistence.

These production-oriented practices support operational reliability; the experiment below focuses specifically on retrieval correctness under a controlled evaluation protocol.

---

## 3. Evaluation Methodology

### 3.1 Golden dataset

Retrieval quality is measured against `backend/evals/golden_dataset.json`. The dataset is explicitly described in-repo as a **small golden set** for the sample knowledge base. It contains:

- **11 cases total**
- **7 answerable** cases (`ans-001` … `ans-007`) with `expected_evidence` phrase lists
- **4 unanswerable** cases (`unans-001` … `unans-004`) with empty evidence lists
- **Source document:** `sample-rag-overview.md`

Answerable cases include short questions about RAG concepts, chunking, embeddings, vector storage, the `POST /ask` behaviour described in the sample document, and the safety note. Evidence phrases are chosen as literal or near-literal substrings expected to appear in retrieved chunk text.

### 3.2 Offline retrieval harness

`backend/evals/evaluate_retrieval.py` evaluates retrieval **without calling Gemini**. For each answerable case it:

1. retrieves `top_k` chunks via `RetrievalService`;
2. computes the 1-based rank of the first retrieved chunk whose text matches any expected evidence phrase;
3. aggregates Hit Rate@K and MRR.

Evidence matching (`backend/evals/evidence.py`) is a **normalised substring check**: lowercase, collapsed whitespace, then phrase containment. The harness itself prints that this matching strategy is for the portfolio corpus and is **not** a universal semantic relevance metric.

Definitions used:

- **Hit Rate@K** — fraction of answerable cases for which at least one expected evidence phrase appears in any of the top-\(K\) retrieved chunks (\(K=4\) by default).
- **MRR** — mean over answerable cases of \(1/\mathrm{rank}\) for the first evidence-bearing chunk, or \(0\) if no hit within the retrieved set.

### 3.3 Separation from live generation evaluation

Live generation evaluation (`backend/evals/evaluate_generation.py`) is optional, opt-in, and quota-consuming. It is rate-limited by design (default delay between requests, bounded case counts, disabled SDK retries, HTTP timeout). Automated unit/integration tests and CI never invoke it.

### 3.4 Deterministic testing and CI

The repository maintains automated pytest suites. As documented in the README and CI workflow:

- **35 fast tests** (`pytest -m "not slow"`) run in CI without `GEMINI_API_KEY`;
- **2 slow tests** exercise temporary embedding/Chroma behaviour locally;
- API tests override `get_rag_service` with a `FakeRagService` so HTTP behaviour can be checked without live LLM calls;
- GitHub Actions also validates Docker image buildability without secrets or deployment.

This separation keeps retrieval evaluation and regression testing reproducible and free of provider flakiness.

---

## 4. Controlled Chunking Experiment

### 4.1 Motivation from a measured failure

Experiment date recorded in `chunking_experiment.md`: **2026-09-12**.

Under fixed-character windowing (`chunk_size=500`, `chunk_overlap=100`, step effectively 400), baseline retrieval evaluation produced:

- Hit Rate@4 = **6/7 (85.7%)**
- MRR = **0.857**
- Failed case: **`ans-006`** — *“How does POST /ask use retrieved chunks in this project?”*

Diagnosis (from the experiment log) showed that character slicing cut the sample document mid-phrase near the `POST /ask` description:

- One chunk ended mid-sentence after text including `"derived from retrieval metadata."`
- The next chunk began mid-word at character index 1600 with the fragment `"om retrieval metadata."`
- The expected evidence phrase `"source citations derived from retrieval metadata"` was therefore broken across the window boundary.
- In vector search, the more complete neighbouring chunk ranked at **#5** (outside top-4), while the fragmented chunk ranked at **#4** but did not contain the intact evidence string needed for the substring check.

Root cause attributed in the experiment record: **character-based slicing fragmented phrases and severed words**, diluting embedding similarity and cutting expected evidence strings.

### 4.2 Hypothesis

If chunking respects paragraph and sentence boundaries while keeping target chunk size (500) and overlap (100) constant, the relevant evidence for `ans-006` will remain intact within a coherent semantic chunk, ranking within top-4, without regressing retrieval on any other answerable golden-set question.

### 4.3 Independent variable and controls

| Role | Variable | Value / treatment |
|---|---|---|
| **Independent** | Chunk boundary strategy | Fixed-character windows → boundary-aware semantic chunking |
| **Held constant** | Dataset | `golden_dataset.json` unchanged |
| **Held constant** | Chunk size | 500 |
| **Held constant** | Chunk overlap | 100 |
| **Held constant** | Embedding model | `all-MiniLM-L6-v2` |
| **Held constant** | Retrieval depth | `top_k=4` |
| **Held constant** | Similarity metric | Cosine distance in Chroma |
| **Held constant** | Corpus | `sample-rag-overview.md` |

No change was made to the evaluation dataset, embedding model, or `top_k` to “game” the metric. Clean re-indexing (`indexer --clean` / vector store clear) was used so candidate results were not contaminated by residue from previous chunk IDs.

### 4.4 Candidate implementation

`backend/app/ingestion/chunking.py` implements boundary-aware end and start locators. The recorded boundary hierarchy for choosing a chunk end at or before the size limit is:

1. paragraph break (`\n\n`);
2. line break (`\n`);
3. sentence termination (`.`, `?`, `!`);
4. word boundary (` `);
5. hard cut fallback for unbroken strings longer than `chunk_size`.

Overlap starts are likewise aligned to nearby natural breaks so subsequent chunks prefer not to begin mid-word. Unit tests in `backend/tests/unit/test_chunking.py` cover paragraph/sentence splits, overlap token boundaries, deterministic chunk IDs, configuration validation, and vector-store clearing.

---

## 5. Results

Measured comparison from the experiment artefact and README evaluation table:

| Metric | Baseline (fixed-character) | Candidate (boundary-aware) | Delta |
|---|---:|---:|---:|
| Hit Rate@4 | 6/7 (85.7%) | **7/7 (100.0%)** | +14.3 percentage points |
| MRR | 0.857 | **1.000** | +0.143 |
| Failed answerable cases | 1 (`ans-006`) | **0** | −1 |
| `ans-006` rank | 5 (miss) | **1 (hit)** | +4 ranks |
| Regressions on other answerable cases | — | **None** | all six others remained rank 1 |

### Per-case ranks (answerable subset)

| Case ID | Baseline rank | Candidate rank | Status |
|---|---:|---:|---|
| `ans-001` | 1 | 1 | Stable |
| `ans-002` | 1 | 1 | Stable |
| `ans-003` | 1 | 1 | Stable |
| `ans-004` | 1 | 1 | Stable |
| `ans-005` | 1 | 1 | Stable |
| `ans-006` | 5 (miss) | **1 (hit)** | Resolved |
| `ans-007` | 1 | 1 | Stable |

**Decision recorded in the experiment log: KEEP.** The change addressed the diagnosed root cause (severed evidence at a character boundary), improved the failing case, produced no regressions on the remaining answerable cases, and added no external chunking dependencies beyond the standard library.

---

## 6. Discussion

### 6.1 What the experiment shows

Within this controlled setting, retrieval failure was not primarily an embedding-model or `top_k` problem. The needed text existed in the corpus, but fixed offsets destroyed phrase integrity and pushed an intact evidence-bearing window just outside the retrieval budget. Preserving semantic boundaries restored both substring matchability and ranking.

Because only the boundary strategy changed, the improvement can be attributed to that factor under the stated controls. This is a stronger engineering claim than a multi-parameter retune where causal credit is ambiguous.

### 6.2 Practical reliability implications

Several repository practices reinforce reliable iteration:

1. **Baseline before change** — metrics and the failing rank were recorded before editing chunking code.
2. **Single-variable change** — size, overlap, model, and `top_k` remained fixed.
3. **Offline retrieval metrics** — Hit Rate@K and MRR do not depend on Gemini stochasticity or quota.
4. **Deterministic tests** — chunking behaviour and API contracts are checked without live generation.
5. **Clean re-index** — evaluation collections can be rebuilt without leftover chunk IDs.
6. **Deterministic citations** — even when generation is used in production paths, source lists are derived from retrieval metadata.

Together, these practices treat retrieval reliability as a measurable property rather than an anecdotal observation.

### 6.3 What the results do *not* show

A Hit Rate of 100% on seven answerable questions over one short sample document does **not** imply general production RAG accuracy. The evidence matcher is a transparent substring check for a known corpus; it is not semantic relevance labelling at scale. Absolute percentages on \(n=7\) are fragile: one additional hard case could change the headline rate substantially. The experiment is best read as a **causal case study** of a chunk-boundary failure mode and its fix under controlled conditions.

---

## 7. Limitations

The following limitations are documented in the repository and apply directly to this report:

1. **Small evaluation corpus** — 11 golden cases on one sample Markdown document. The setup demonstrates methodology and a local improvement, not universal accuracy across domains, layouts, or document types.
2. **Evidence matching simplicity** — normalised substring matching can miss paraphrased relevance and can be sensitive to exact phrasing; it is appropriate for this controlled portfolio corpus, not as a general IR relevance judge.
3. **Single-node vector store** — embedded Chroma with SQLite/HNSW suits local/single-instance use; it is not a distributed production vector cluster.
4. **No hybrid retrieval or reranking** — retrieval uses bi-encoder cosine nearest neighbours only.
5. **Generation path not the subject of the KEEP decision** — the KEEP decision concerns retrieval metrics; live generation quality is evaluated separately under optional, quota-bounded tooling and is outside the primary claims of this experiment.
6. **Operational constraints** — Docker image size on Linux is large because default PyPI PyTorch wheels pulled by `sentence-transformers` include NVIDIA CUDA runtime packages despite CPU-only usage; cold-start embedding initialisation adds latency on CPU; generation depends on external Gemini availability.

---

## 8. Future Work

The following items are **documented as future work** in the repository and are **not** claimed as implemented results of this experiment:

- Expand golden datasets across multiple documents, layouts, tables, and domains.
- Benchmark hybrid BM25 + dense retrieval and cross-encoder reranking.
- Reduce image size / CPU cost via CPU-specific PyTorch wheels or ONNX / quantised embedding export.
- Export OpenTelemetry spans from existing stage timers.
- Support managed/external vector databases where multi-node deployment is required.

Any evaluation of those directions would require new experimental protocols and must not be confused with the measured chunking results above.

---

## 9. Conclusion

This report examined retrieval reliability in a production-oriented RAG system through a controlled chunking experiment grounded entirely in repository artefacts. Fixed-character windowing left one golden-set case (`ans-006`) with needed evidence at rank 5, outside `top_k=4`, after mid-word/mid-phrase cuts. Boundary-aware semantic chunking, under identical chunk size (500), overlap (100), embedding model (`all-MiniLM-L6-v2`), cosine similarity, corpus, and evaluation set, raised Hit Rate@4 from 85.7% (6/7) to 100.0% (7/7) and MRR from 0.857 to 1.000, moving `ans-006` to rank 1 with no measured regressions on other answerable cases.

The broader engineering lesson is methodological: treat retrieval as an empirically measurable component; isolate one independent variable; keep evaluation offline and deterministic where possible; and state scope limits clearly. On this small controlled portfolio corpus, boundary-aware chunking was a justified KEEP. Claims beyond that corpus remain future work.

---

## Appendix A — How to reproduce the retrieval metrics

Commands documented in the repository (from `backend/`, after installing dependencies and without requiring Gemini for retrieval evaluation):

```bash
python -m app.ingestion.indexer --path data/documents --clean
python -m evals.evaluate_retrieval
```

Fast deterministic tests (no Gemini):

```bash
python -m pytest -m "not slow"
```

---

## Appendix B — Key repository paths

| Artefact | Path |
|---|---|
| Experiment log | `backend/evals/experiments/chunking_experiment.md` |
| Golden dataset | `backend/evals/golden_dataset.json` |
| Retrieval eval harness | `backend/evals/evaluate_retrieval.py` |
| Evidence helpers | `backend/evals/evidence.py` |
| Chunking implementation | `backend/app/ingestion/chunking.py` |
| Sample corpus | `backend/data/documents/sample-rag-overview.md` |
| Settings defaults | `backend/app/core/config.py` |
| CI workflow | `.github/workflows/ci.yml` |
