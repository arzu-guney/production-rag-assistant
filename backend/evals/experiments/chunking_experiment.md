# Retrieval Improvement Experiment: Boundary-Aware Semantic Chunking

## 1. Overview and Controlled Conditions

- **Experiment Date:** 2026-09-12
- **Objective:** Improve retrieval performance on golden dataset failure `ans-006` without regressing other cases or gaming evaluation metrics.
- **Independent Variable:** Chunking boundary strategy (fixed-character windowing vs boundary-aware semantic chunking).
- **Controlled Variables (Held Constant):**
  - Dataset: `evals/golden_dataset.json` (11 cases, 7 answerable, 4 unanswerable — completely unchanged).
  - Target chunk size: `CHUNK_SIZE=500` (unchanged).
  - Target overlap: `CHUNK_OVERLAP=100` (unchanged).
  - Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (unchanged).
  - Retrieval depth: `RETRIEVAL_TOP_K=4` (unchanged).
  - Vector similarity metric: Cosine distance in Chroma (unchanged).
  - Document corpus: `data/documents/sample-rag-overview.md` (unchanged).

---

## 2. Baseline Measurement & Failure Diagnosis

### Baseline Metrics
- **Hit Rate @ 4:** 6/7 (85.7%)
- **MRR:** 0.857
- **Failed Case:** `ans-006` ("How does POST /ask use retrieved chunks in this project?")

### Diagnosis of `ans-006`
In the original character-windowing chunker (`chunk_size=500`, `chunk_overlap=100`, step = 400):
- **Chunk 3 (chars 1200..1700):** Ended mid-sentence after `"derived from retrieval metadata.\n\n## Safety note\n\nDo not place private or copyrighted documents in this sample"`.
- **Chunk 4 (chars 1600..1761):** Started mid-word at character index 1600: `"om retrieval metadata.\n\n## Safety note\n\nDo not place private or copyrighted documents in this sample folder for demos.\nUse only content you are allowed to share."`
- The query specifically asked about `POST /ask`. In the vector search, Chunk 3 ranked at #5 (distance = 0.7348), falling outside top-4. Chunk 4 ranked at #4 (distance = 0.7281), but because its text began with the severed fragment `"om retrieval metadata"`, the expected evidence phrase `"source citations derived from retrieval metadata"` was broken across the window boundary.
- **Root Cause:** Character-based slicing produced fragmented phrases and severed words across window boundaries, diluting embedding similarity and cutting expected evidence strings.

---

## 3. Hypothesis

> If chunking respects paragraph and sentence boundaries while keeping the target chunk size (500) and overlap (100) constant, the relevant evidence for `ans-006` will remain intact within a coherent semantic chunk, ranking within top-4 without regressing retrieval on any other answerable question in the golden dataset.

---

## 4. Implementation

Modified `backend/app/ingestion/chunking.py`:
- Replaced fixed character step (`text[start:start+size]`) with a boundary-aware boundary locator.
- **Boundary hierarchy:**
  1. Paragraph break (`\n\n`)
  2. Line break (`\n`)
  3. Sentence termination (`. `, `? `, `! `)
  4. Word boundary (` `)
  5. Fallback hard cut (for unbroken strings exceeding `chunk_size`)
- **Overlap start locator:** Searches the overlap window (`chunk_end - chunk_overlap`) for the nearest natural break to prevent subsequent chunks from starting mid-word.
- Added `VectorStore.clear()` and `indexer.py --clean` to ensure evaluation collections are cleanly rebuilt without residue from previous chunk IDs.

---

## 5. Experimental Results

| Metric | Baseline (Fixed Character) | Candidate (Boundary-Aware) | Delta |
|---|---|---|---|
| **Hit Rate @ 4** | 6/7 (85.7%) | **7/7 (100.0%)** | **+14.3%** |
| **MRR** | 0.857 | **1.000** | **+0.143** |
| **Failed Answerable Cases** | 1 (`ans-006`) | **0** | **-1** |
| **`ans-006` Rank** | Rank 5 (outside top-4) | **Rank 1** | **+4 ranks** |
| **Regressions on Other Cases**| None | **None** | All 6 other cases remain Rank 1 |

### Per-Case Comparison

| Case ID | Baseline Rank | Candidate Rank | Status |
|---|---|---|---|
| `ans-001` | 1 | 1 | Stable |
| `ans-002` | 1 | 1 | Stable |
| `ans-003` | 1 | 1 | Stable |
| `ans-004` | 1 | 1 | Stable |
| `ans-005` | 1 | 1 | Stable |
| `ans-006` | 5 (Miss) | **1 (Hit)** | **Resolved** |
| `ans-007` | 1 | 1 | Stable |

---

## 6. Decision: KEEP

- **Evidence:** The change directly addressed the root cause (severed boundary cutting evidence) by preserving semantic sentence/paragraph boundaries.
- **Impact:** `ans-006` jumped from rank 5 to rank 1. All other cases remained at rank 1 with no regressions.
- **Complexity:** The implementation uses standard library regex and string methods with zero external dependencies.
- **Note on Small Dataset:** While 100% Hit Rate is achieved on this 7-case controlled portfolio evaluation, this is a local baseline improvement and should not be misconstrued as a claim of universal production RAG accuracy across arbitrary corpora.
