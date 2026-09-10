from __future__ import annotations

import argparse
import asyncio
import time

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, GenerationError, RagError
from app.dependencies import get_rag_service
from app.services.gemini import DEFAULT_HTTP_RETRY_ATTEMPTS, DEFAULT_HTTP_TIMEOUT_MS
from evals.evidence import (
    concepts_present,
    load_golden_dataset,
    looks_like_abstention,
)

# Suitable default for a free-tier style limit around ~5 generate_content calls/minute.
DEFAULT_DELAY_SECONDS = 15.0
# Keep live Gemini usage cheap/safe by default.
DEFAULT_MAX_CASES = 3


def _classify_provider_error(exc: BaseException) -> str:
    text = str(exc).lower()
    cause = str(exc.__cause__).lower() if exc.__cause__ else ""
    blob = f"{text} {cause}"
    if "429" in blob or "resource_exhausted" in blob or "rate" in blob:
        return "rate_limit"
    if "timeout" in blob or "timed out" in blob:
        return "timeout"
    if "api_key_invalid" in blob or "api key not valid" in blob:
        return "authentication"
    if "model" in blob and ("not found" in blob or "invalid" in blob):
        return "model"
    return "provider_error"


def _public_case_error(exc: BaseException) -> str:
    category = _classify_provider_error(exc)
    if category == "rate_limit":
        return (
            "Gemini rate limit/quota reached for this case. "
            "No automatic retry was performed."
        )
    if category == "timeout":
        return "Gemini request timed out for this case. No automatic retry was performed."
    if category == "authentication":
        return "Gemini authentication failed for this case."
    if category == "model":
        return "Gemini model request failed for this case."
    if isinstance(exc, RagError):
        return exc.message
    return "Provider request failed for this case."


def _select_cases(
    cases: list[dict],
    *,
    max_cases: int | None,
    run_all: bool,
) -> list[dict]:
    if run_all:
        return list(cases)
    limit = DEFAULT_MAX_CASES if max_cases is None else max_cases
    if limit < 1:
        raise ValueError("--max-cases must be >= 1")
    return list(cases[:limit])


async def _run_all(
    cases: list[dict],
    delay_seconds: float,
    *,
    stop_on_provider_error: bool,
) -> list[dict]:
    print("Loading local embedding model and services (no Gemini call yet)...")
    started_load = time.perf_counter()
    rag = get_rag_service()
    print(f"Local services ready in {time.perf_counter() - started_load:.1f}s")

    results: list[dict] = []
    total = len(cases)

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{total}] Evaluating {case['id']}...")
        started = time.perf_counter()
        try:
            # No automatic retries: avoid multiplying external API usage.
            response = await rag.ask(case["question"])
            elapsed = time.perf_counter() - started
            print(f"[{index}/{total}] Request completed in {elapsed:.1f}s")
            results.append(
                {
                    "id": case["id"],
                    "question": case["question"],
                    "answerable": case["answerable"],
                    "status": "success",
                    "answer": response.answer,
                    "sources": [source.model_dump() for source in response.sources],
                    "expected_answer_concepts": case.get("expected_answer_concepts")
                    or [],
                    "error_category": None,
                    "error_message": None,
                }
            )
        except (ConfigurationError, GenerationError, RagError, Exception) as exc:
            elapsed = time.perf_counter() - started
            category = _classify_provider_error(exc)
            message = _public_case_error(exc)
            print(
                f"[{index}/{total}] Provider error after {elapsed:.1f}s: {category}"
            )
            results.append(
                {
                    "id": case["id"],
                    "question": case["question"],
                    "answerable": case["answerable"],
                    "status": "provider_failure",
                    "answer": None,
                    "sources": [],
                    "expected_answer_concepts": case.get("expected_answer_concepts")
                    or [],
                    "error_category": category,
                    "error_message": message,
                }
            )
            if stop_on_provider_error:
                print("Stopping early because --stop-on-provider-error is set.")
                break

        if index < total and delay_seconds > 0:
            print(f"  waiting {delay_seconds:.0f}s before next case...")
            await asyncio.sleep(delay_seconds)

    return results


def evaluate_generation(
    *,
    delay_seconds: float = DEFAULT_DELAY_SECONDS,
    max_cases: int | None = DEFAULT_MAX_CASES,
    run_all: bool = False,
    stop_on_provider_error: bool = False,
) -> int:
    """Optional live Gemini evaluation. Requires GEMINI_API_KEY and an indexed corpus."""
    settings = get_settings()
    if not settings.gemini_api_key.strip() or settings.gemini_api_key.lower().startswith(
        "your_"
    ):
        print(
            "ERROR: Set a real GEMINI_API_KEY in backend/.env before running "
            "generation evaluation."
        )
        return 1

    dataset = load_golden_dataset()
    all_cases = dataset["cases"]
    try:
        cases = _select_cases(all_cases, max_cases=max_cases, run_all=run_all)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    print("\nLive Gemini evaluation")
    print(f"Cases to run: {len(cases)} (dataset has {len(all_cases)} total)")
    print(f"Maximum external Gemini requests: {len(cases)}")
    print(f"Request timeout: {DEFAULT_HTTP_TIMEOUT_MS / 1000:.0f}s")
    print(
        f"Retry policy: disabled "
        f"(google-genai HttpRetryOptions attempts={DEFAULT_HTTP_RETRY_ATTEMPTS})"
    )
    print(f"Delay between requests: {delay_seconds:g}s")
    print(f"Stop on provider error: {stop_on_provider_error}")
    print(
        "This may take several minutes and can consume Gemini API quota. "
        "Billing is never enabled by this project; quotas depend on your Google account/plan."
    )
    print("No automatic retries will be performed on rate-limit or timeout errors.\n")

    results = asyncio.run(
        _run_all(
            cases,
            delay_seconds=delay_seconds,
            stop_on_provider_error=stop_on_provider_error,
        )
    )

    successful = [row for row in results if row["status"] == "success"]
    provider_failures = [row for row in results if row["status"] == "provider_failure"]
    answerable_ok = [row for row in successful if row["answerable"]]
    unanswerable_ok = [row for row in successful if not row["answerable"]]

    concept_hits = 0
    citation_ok = 0
    for row in answerable_ok:
        found = concepts_present(row["answer"], row["expected_answer_concepts"])
        if found:
            concept_hits += 1
        if any(src.get("source") == "sample-rag-overview.md" for src in row["sources"]):
            citation_ok += 1

    abstentions = sum(
        1 for row in unanswerable_ok if looks_like_abstention(row["answer"] or "")
    )

    print("\n=== Generation Evaluation (live Gemini) ===")
    print("NOTE: Explicit opt-in command. Not part of pytest or retrieval evaluation.")
    print(f"Cases requested               : {len(results)}")
    print(f"Evaluated successfully        : {len(successful)}")
    print(f"Provider/rate-limit failures  : {len(provider_failures)}")
    print(f"Answerable evaluated          : {len(answerable_ok)}")
    if answerable_ok:
        print(
            f"Concept coverage (lightweight): {concept_hits}/{len(answerable_ok)} "
            f"({concept_hits / len(answerable_ok):.1%})"
        )
        print(
            f"Citation present for sample   : {citation_ok}/{len(answerable_ok)} "
            f"({citation_ok / len(answerable_ok):.1%})"
        )
    else:
        print("Concept coverage (lightweight): n/a (no successful answerable cases)")
        print("Citation present for sample   : n/a (no successful answerable cases)")
    print(f"Unanswerable evaluated        : {len(unanswerable_ok)}")
    if unanswerable_ok:
        print(
            f"Abstention heuristic hits     : {abstentions}/{len(unanswerable_ok)} "
            f"({abstentions / len(unanswerable_ok):.1%})"
        )
    else:
        print("Abstention heuristic hits     : n/a (no successful unanswerable cases)")
    print(
        "Quality metrics above count ONLY successfully evaluated cases. "
        "Provider failures are reported separately and are not treated as model-quality results."
    )

    if provider_failures:
        print("\n--- Provider failures ---")
        for row in provider_failures:
            print(
                f"[{row['id']}] category={row['error_category']} "
                f"message={row['error_message']}"
            )

    print("\n--- Case summaries ---")
    for row in results:
        label = "ANSWERABLE" if row["answerable"] else "UNANSWERABLE"
        if row["status"] != "success":
            print(f"[{row['id']}] ({label}) STATUS=provider_failure")
            continue
        preview = (row["answer"] or "")[:180].replace("\n", " ")
        print(
            f"[{row['id']}] ({label}) sources={len(row['sources'])} answer={preview!r}"
        )

    print("==========================================\n")
    return 0 if not provider_failures else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Optional live Gemini generation evaluation. "
            "Defaults to a small subset to protect free/limited API quotas. "
            "Not run by pytest."
        )
    )
    parser.add_argument(
        "--delay-seconds",
        type=float,
        default=DEFAULT_DELAY_SECONDS,
        help=(
            "Seconds to wait between live Gemini cases "
            f"(default: {DEFAULT_DELAY_SECONDS:g})."
        ),
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=DEFAULT_MAX_CASES,
        help=(
            "Maximum golden-dataset cases to evaluate with live Gemini "
            f"(default: {DEFAULT_MAX_CASES})."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run the full golden dataset (uses more Gemini quota).",
    )
    parser.add_argument(
        "--stop-on-provider-error",
        action="store_true",
        help="Stop immediately after the first provider/rate-limit/timeout failure.",
    )
    args = parser.parse_args(argv)
    if args.delay_seconds < 0:
        print("ERROR: --delay-seconds must be >= 0")
        return 1
    if args.all and args.max_cases != DEFAULT_MAX_CASES:
        print("NOTE: --all is set; ignoring --max-cases and running the full dataset.")
    return evaluate_generation(
        delay_seconds=args.delay_seconds,
        max_cases=None if args.all else args.max_cases,
        run_all=args.all,
        stop_on_provider_error=args.stop_on_provider_error,
    )


if __name__ == "__main__":
    raise SystemExit(main())
