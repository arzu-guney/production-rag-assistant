from __future__ import annotations

import argparse
import sys

from app.core.config import get_settings
from app.dependencies import get_embedding_service, get_vector_store
from app.services.retrieval import RetrievalService
from evals.evidence import (
    first_evidence_rank,
    load_golden_dataset,
)


def evaluate_retrieval(*, top_k: int | None = None) -> int:
    settings = get_settings()
    k = top_k or settings.retrieval_top_k
    dataset = load_golden_dataset()
    cases = dataset["cases"]
    answerable = [case for case in cases if case.get("answerable")]

    retrieval = RetrievalService(
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
        top_k=k,
    )

    if get_vector_store().count == 0:
        print(
            "ERROR: vector collection is empty. "
            "Run indexing before retrieval evaluation:\n"
            "  python -m app.ingestion.indexer --path data/documents"
        )
        return 1

    hits = 0
    reciprocal_ranks: list[float] = []
    failures: list[dict] = []

    for case in answerable:
        chunks = retrieval.retrieve(case["question"])
        rank = first_evidence_rank(chunks, case.get("expected_evidence") or [])
        if rank is None:
            reciprocal_ranks.append(0.0)
            failures.append(
                {
                    "id": case["id"],
                    "question": case["question"],
                    "expected_evidence": case.get("expected_evidence") or [],
                    "retrieved": [
                        {
                            "rank": index,
                            "source": chunk.source_name,
                            "distance": chunk.distance,
                            "preview": chunk.text[:160].replace("\n", " "),
                        }
                        for index, chunk in enumerate(chunks, start=1)
                    ],
                }
            )
        else:
            hits += 1
            reciprocal_ranks.append(1.0 / rank)

    total = len(answerable)
    hit_rate = (hits / total) if total else 0.0
    mrr = (sum(reciprocal_ranks) / total) if total else 0.0

    print("\n=== Retrieval Evaluation ===")
    print(f"Dataset              : {dataset.get('description', '')[:80]}...")
    print(f"Cases                : {len(cases)}")
    print(f"Answerable cases     : {total}")
    print(f"Top-k                : {k}")
    print(f"Hit Rate @{k:<3}         : {hits}/{total} ({hit_rate:.1%})")
    print(f"MRR                  : {mrr:.3f}")
    print(
        "Evidence matching    : normalized substring check against expected_evidence "
        "(portfolio corpus only)"
    )

    if failures:
        print("\n--- Failures ---")
        for item in failures:
            print(f"\n[{item['id']}] {item['question']}")
            print(f"  expected_evidence: {item['expected_evidence']}")
            if not item["retrieved"]:
                print("  retrieved: (none)")
            for row in item["retrieved"]:
                print(
                    f"  rank={row['rank']} source={row['source']} "
                    f"distance={row['distance']} preview={row['preview']!r}"
                )
    else:
        print("\nFailures: none")

    print("============================\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval Hit Rate@K and MRR on the golden dataset."
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Override retrieval top_k (defaults to RETRIEVAL_TOP_K settings).",
    )
    args = parser.parse_args(argv)
    return evaluate_retrieval(top_k=args.top_k)


if __name__ == "__main__":
    raise SystemExit(main())
