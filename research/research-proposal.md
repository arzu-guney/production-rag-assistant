# Research Proposal

**Author:** Arzu Guney  
**Document status:** Provisional research planning document (not a peer-reviewed paper)  
**Target publication date:** 27 November 2026  
**Host repository:** `production-rag-assistant`

---

## 1. Research title

**Evaluating the Reliability of Retrieval-Augmented Generation Systems**

---

## 2. Abstract (provisional)

Retrieval-Augmented Generation (RAG) systems can fail even when a capable language model is available: incorrect or incomplete retrieval, and answers produced without sufficient supporting evidence, both undermine reliability. This project studies how retrieval strategy and evidence-based abstention affect answer reliability in a controlled RAG setting built on an existing production-oriented FastAPI system (local Sentence Transformers embeddings, persistent ChromaDB retrieval, and Gemini grounded generation).

Three conditions are compared: (A) baseline dense retrieval with prompt-instructed abstention; (B) dense retrieval with cross-encoder reranking; and (C) dense retrieval with an explicit, development-set-calibrated evidence threshold that abstains when support is insufficient. Evaluation uses a versioned multi-document dataset (target 60–100 labelled questions) with answerable and unanswerable items, separate development and held-out test splits, and metrics spanning retrieval quality, answer correctness, faithfulness/groundedness, unsupported answers, false refusals, abstention rate, and latency.

This abstract states research intent only. No new experimental outcomes are claimed here; measured results will be reported after the planned corpus and conditions are implemented and evaluated.

---

## 3. Problem statement

RAG pipelines couple a retriever and a generator. Engineering practice often optimises generation prompts while treating retrieval as a fixed black box. Prior work in this repository showed that a single chunk-boundary defect could move required evidence outside `top_k` and fail a golden-set case (`ans-006`), even though the text existed in the corpus. Separately, the current runtime relies on **prompt-based** abstention: unanswerable queries still receive nearest-neighbour chunks and a generation call, with “I don’t know”-style behaviour depending on model compliance rather than an explicit evidence gate.

For reliability-focused evaluation, two failure modes must be distinguished:

1. **Retrieval failure** — supporting evidence is not ranked highly enough (or at all) among retrieved chunks.
2. **Generation / abstention failure** — the system answers when evidence is insufficient (unsupported answer), or refuses when evidence is sufficient (false refusal).

Without controlled ablations and labelled unanswerable questions, these failure modes are easy to conflate.

---

## 4. Primary research question

> How do retrieval strategies and evidence-based abstention affect answer reliability in Retrieval-Augmented Generation systems?

Secondary questions:

- Does cross-encoder reranking improve Recall@K / MRR relative to dense-only retrieval under fixed chunking and embedding settings?
- Does a calibrated evidence threshold reduce unsupported answers on unanswerable questions without excessive false refusals on answerable questions?
- Can retrieval gains and abstention gains be attributed separately by comparing conditions that change only one mechanism at a time?

---

## 5. Three testable hypotheses

**H1 (Reranking improves retrieval ranking).**  
Under fixed corpus, chunking, embedding model, and final context size \(K\), retrieving \(N>K\) candidates and reranking with a cross-encoder will yield higher Recall@K and MRR on held-out answerable questions than dense-only top-\(K\) retrieval (Condition B vs Condition A).

**H2 (Evidence-based abstention reduces unsupported answers).**  
Under fixed retrieval settings, adding a development-set-calibrated evidence threshold that abstains when evidence is insufficient will reduce Unsupported Answer Rate on held-out unanswerable questions relative to prompt-only abstention (Condition C vs Condition A), at an acceptable False Refusal Rate on answerable questions.

**H3 (Effects are separable).**  
When conditions are compared under single-variable controls, improvements in retrieval metrics (Recall@K, MRR) will not be explained merely by changes in abstention rate, and improvements in Unsupported Answer Rate will not be explained merely by changes in Recall@K—i.e., retrieval-oriented and abstention-oriented interventions produce distinguishable metric profiles.

---

## 6. Research methodology

### 6.1 System under study

Reuse the existing application stack (no replacement architecture):

| Component | Implementation (verified) |
|---|---|
| API / orchestration | FastAPI; `RagService.ask()` |
| Chunking | Boundary-aware semantic chunking |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2`, normalised |
| Vector store | ChromaDB persistent, cosine space |
| Generation | Google Gemini (`gemini-3.6-flash`, temperature 0.2) |
| Citations | Deterministic from retrieval metadata |
| Offline retrieval eval | `backend/evals/evaluate_retrieval.py` |
| Optional generation eval | `backend/evals/evaluate_generation.py` |

### 6.2 Experimental conditions

| Condition | Description | Independent change |
|---|---|---|
| **A — Baseline RAG** | Dense retrieve top-\(K\); prompt-based abstention only | Reference |
| **B — RAG + Reranking** | Dense retrieve top-\(N\); cross-encoder rerank; keep top-\(K\) | Retrieval ranking only |
| **C — RAG + Evidence-based abstention** | Dense retrieve top-\(K\); abstain if evidence score fails calibrated threshold | Abstention gate only |

**Optional combined conditions** (if schedule permits, without expanding core claims):

- **A+B:** reranked retrieval + prompt abstention (same as B if B already uses prompt abstention)
- **B+C:** reranked retrieval + evidence threshold (tests complementarity; reported as exploratory)

Core claims for publication will rest on A vs B vs C under single-variable controls.

### 6.3 Dataset methodology

Target a new versioned research dataset (not a silent mutation of the existing 11-case portfolio set):

- **60–100** labelled evaluation questions
- **Multiple** source documents
- Mix of **answerable** and **unanswerable** items
- Explicit **supporting evidence labels** (phrases and/or chunk/span IDs)
- Separate **development** (calibration / threshold tuning) and **held-out test** splits
- Dataset version identifier recorded in every run artefact

The existing `backend/evals/golden_dataset.json` (11 cases) remains an engineering smoke/portfolio artefact and is not the primary research corpus.

### 6.4 Evaluation procedure

1. Freeze Condition A configuration (chunk size/overlap, embedding model, \(K\), generation settings).
2. Index the research corpus with `--clean` and record index/build metadata.
3. Run retrieval evaluation for A and B on the held-out answerable subset (and report unanswerable retrieval diagnostics separately if useful).
4. Calibrate Condition C threshold **only** on the development split.
5. Evaluate generation-side reliability metrics for A and C (and optionally B / B+C) on the held-out test split with fixed generation settings.
6. Persist raw per-case JSON outputs and aggregate tables under versioned experiment IDs.

### 6.5 Distinguishing retrieval vs abstention improvements

| If we observe… | Prefer interpretation… |
|---|---|
| Recall@K / MRR ↑, unsupported-answer rate ≈ unchanged | Retrieval ranking improved (H1-type) |
| Unsupported-answer rate ↓, false-refusal may ↑, Recall@K ≈ unchanged | Abstention policy improved (H2-type) |
| Both move together | Inspect B vs C vs B+C; do not attribute both effects to one intervention |

Abstention decisions are scored independently of whether retrieval “hit” evidence, using the labelled answerability of each question.

---

## 7. Evaluation metrics

### 7.1 Retrieval metrics (apply before / without generation)

| Metric | Definition (operational) | Applies to |
|---|---|---|
| **Recall@K** (Hit Rate@K) | Fraction of answerable questions for which at least one labelled evidence unit appears in the top-\(K\) retrieved chunks | A, B (primary); C if same retriever |
| **MRR** | Mean reciprocal rank of the first evidence-bearing chunk among answerable questions | A, B (primary) |

*Note:* The current harness implements Hit Rate@K via normalised substring evidence matching. The research corpus may extend labels to chunk IDs; definitions will be fixed in the dataset card before runs.

### 7.2 Generation / reliability metrics

| Metric | Definition (operational) | Applies to |
|---|---|---|
| **Answer Correctness** | On answerable, non-abstained outputs: whether the answer covers required labelled concepts / reference criteria | A, B, C |
| **Faithfulness / Groundedness** | Whether answer claims are supported by the provided context (judge protocol to be fixed before runs; may be human and/or automated) | A, B, C when an answer is produced |
| **Unsupported Answer Rate** | Fraction of **unanswerable** questions where the system produces a non-abstaining answer | A, C (primary) |
| **False Refusal Rate** | Fraction of **answerable** questions where the system abstains | A, C (primary) |
| **Abstention Rate** | Fraction of all questions (or stratified by answerability) where the system abstains | A, C (primary) |
| **Latency** | End-to-end and stage timings (retrieval, optional rerank, generation) | All |

### 7.3 Handling abstained answers

- An **abstention** is a refused or insufficient-evidence response (runtime threshold abstain **or** explicit “documents do not contain enough information” style refusal under the fixed protocol).
- Abstentions are **excluded** from Answer Correctness and Faithfulness denominators (those metrics are conditional on producing an answer), unless a secondary “correctness including refusal policy” analysis is pre-registered.
- Abstentions on unanswerable items count as **successes** for Unsupported Answer Rate (they are not unsupported answers).
- Abstentions on answerable items count toward **False Refusal Rate**.
- Prompt-only vs threshold abstention must be labelled in run metadata so they are not conflated.

---

## 8. Experimental controls

Held constant across A/B/C unless a condition explicitly changes them:

- Document corpus and dataset version
- Chunk size = 500, overlap = 100, boundary-aware chunking
- Embedding model = `sentence-transformers/all-MiniLM-L6-v2`
- Vector similarity = cosine (Chroma)
- Final context size \(K\) (default 4, matching `RETRIEVAL_TOP_K`)
- Gemini model ID and temperature 0.2
- Prompt templates (except that Condition C adds an application-level abstention decision before/instead of unconstrained generation when the gate fires)
- Evaluation splits and labelling protocol
- Clean re-index before comparative runs

Condition-specific variables only:

- **B:** candidate pool size \(N\), cross-encoder model ID  
- **C:** evidence score definition and threshold \(\tau\) (tuned on development only)

---

## 9. Expected contributions

1. A controlled empirical comparison of dense RAG, reranked RAG, and evidence-threshold abstention on a versioned multi-document reliability dataset.
2. A practical methodology for separating retrieval ranking effects from abstention-policy effects using complementary metrics.
3. An open, reproducible extension of an existing production-oriented RAG codebase (FastAPI + Chroma + Sentence Transformers + Gemini) rather than a disposable demo notebook.
4. Transparent limitations and negative/ambiguous results where hypotheses are not supported.

---

## 10. Limitations and threats to validity

- **External validity:** Results will apply to the chosen corpus, models, and \(K\); they will not imply universal production RAG accuracy.
- **Label quality:** Evidence and correctness labels may contain annotator error; protocols will be documented.
- **Automated judges:** If faithfulness uses an LLM judge, judge bias is a threat; dual coding or human spot-checks will be preferred where feasible.
- **Provider variance:** Gemini responses may vary; temperature is fixed low (0.2), but residual non-determinism remains.
- **Threshold overfitting:** Condition C threshold must be calibrated only on development data.
- **Small historical artefact:** The existing 11-case portfolio set must not be over-interpreted as the research evaluation.
- **Scope:** Hybrid BM25, multi-agent systems, and auth/security hardening remain out of core experimental scope.
- **Construct validity of “abstention”:** Prompt refusals and threshold refusals differ mechanistically; both will be tagged.

---

## 11. Publication plan

| Milestone | Target window | Deliverable |
|---|---|---|
| Research docs + audit (this pass) | Immediate | `research/` documentation |
| Research dataset v1 + splits | Early–mid project | Versioned labelled questions + corpus |
| Condition B implementation + retrieval eval | Mid project | Rerank path + A vs B retrieval tables |
| Condition C implementation + calibration | Mid–late project | Threshold gate + A vs C reliability tables |
| Combined exploratory runs (optional) | Late project | B+C diagnostics |
| Paper draft + figures | Before freeze | Full write-up of methods/results |
| **Target publication** | **27 November 2026** | Public release of paper/report + reproducibility artefacts |

Publication venue is intentionally undecided in this document (workshop, arXiv preprint, institutional report, or course/PhD writing sample). The scientific claims will be scoped to measured conditions only.

---

## References to repository evidence (non-bibliographic)

This proposal is grounded in the current repository’s implemented components and documented engineering experiment (`backend/evals/experiments/chunking_experiment.md`). No external paper citations are asserted here to avoid inventing a literature review in this planning pass; a formal related-work section will be added in the paper draft with verified citations.
