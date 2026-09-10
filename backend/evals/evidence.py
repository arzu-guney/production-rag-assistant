from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


EVALS_DIR = Path(__file__).resolve().parent
GOLDEN_DATASET_PATH = EVALS_DIR / "golden_dataset.json"


def normalize_text(value: str) -> str:
    """Lowercase and collapse whitespace for lightweight phrase matching."""
    return re.sub(r"\s+", " ", value.lower()).strip()


def load_golden_dataset(path: Path | None = None) -> dict[str, Any]:
    dataset_path = path or GOLDEN_DATASET_PATH
    return json.loads(dataset_path.read_text(encoding="utf-8"))


def evidence_hit(chunk_text: str, expected_evidence: list[str]) -> bool:
    """Return True if any expected evidence phrase appears in the chunk text.

    This is a transparent substring check for a controlled portfolio corpus.
    It is not a universal semantic relevance metric.
    """
    haystack = normalize_text(chunk_text)
    for phrase in expected_evidence:
        needle = normalize_text(phrase)
        if needle and needle in haystack:
            return True
    return False


def first_evidence_rank(chunks: list[Any], expected_evidence: list[str]) -> int | None:
    """1-based rank of the first retrieved chunk containing expected evidence."""
    for index, chunk in enumerate(chunks, start=1):
        text = chunk.text if hasattr(chunk, "text") else str(chunk)
        if evidence_hit(text, expected_evidence):
            return index
    return None


def looks_like_abstention(answer: str) -> bool:
    """Heuristic abstention detector for unanswerable questions.

    Limitation: wording can change; this is not a formal entailment check.
    """
    text = normalize_text(answer)
    cues = [
        "do not contain",
        "does not contain",
        "not contain enough",
        "insufficient",
        "not enough information",
        "provided documents",
        "provided context",
        "cannot answer",
        "can't answer",
        "no information",
        "not mentioned",
        "outside the provided",
    ]
    return any(cue in text for cue in cues)


def concepts_present(answer: str, concepts: list[str]) -> list[str]:
    """Return which expected concept tokens appear in the generated answer."""
    haystack = normalize_text(answer)
    return [concept for concept in concepts if normalize_text(concept) in haystack]
