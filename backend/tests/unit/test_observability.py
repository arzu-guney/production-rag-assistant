"""Deterministic tests for request correlation, HTTP logging, and RAG observability."""

from __future__ import annotations

import logging
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import (
    ConfigurationError,
    EmptyKnowledgeBaseError,
    GenerationError,
    NoRelevantContextError,
)
from app.core.logging import get_request_id
from app.dependencies import get_rag_service
from app.main import app
from app.services.rag import RagService
from app.services.retrieval import RetrievedChunk
from tests.conftest import FakeRagService


def test_health_response_contains_valid_uuid_request_id(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers or "X-Request-ID" in response.headers
    req_id = response.headers.get("X-Request-ID") or response.headers.get("x-request-id")
    assert req_id is not None
    # Validate UUID4 format
    parsed = uuid.UUID(req_id, version=4)
    assert str(parsed) == req_id


def test_client_supplied_request_id_is_preserved_when_safe(client) -> None:
    custom_id = "trace-client-correlation-42"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_invalid_client_supplied_request_id_is_replaced_with_uuid(client) -> None:
    bad_id = "malicious\r\ninjection\nvalue"
    response = client.get("/health", headers={"X-Request-ID": bad_id})
    assert response.status_code == 200
    returned_id = response.headers.get("X-Request-ID")
    assert returned_id != bad_id
    parsed = uuid.UUID(returned_id, version=4)
    assert str(parsed) == returned_id


def test_request_ids_do_not_leak_between_requests(client) -> None:
    # Verify no ambient context before request
    assert get_request_id() is None

    res1 = client.get("/health")
    res2 = client.get("/health")

    id1 = res1.headers.get("X-Request-ID")
    id2 = res2.headers.get("X-Request-ID")

    assert id1 is not None
    assert id2 is not None
    assert id1 != id2

    # ContextVar must be reset back to None after each request
    assert get_request_id() is None


def test_validation_error_response_still_receives_request_id(client) -> None:
    # Use fake RAG so validation test never depends on GEMINI_API_KEY
    app.dependency_overrides[get_rag_service] = FakeRagService
    try:
        # Empty question triggers Pydantic RequestValidationError (422)
        response = client.post("/ask", json={"question": "   "})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert "X-Request-ID" in response.headers
    parsed = uuid.UUID(response.headers["X-Request-ID"], version=4)
    assert str(parsed) == response.headers["X-Request-ID"]


@pytest.mark.anyio
async def test_rag_pipeline_stage_events_and_privacy(caplog) -> None:
    """Verify that stage events are emitted with safe metadata and no text leakage."""
    caplog.set_level(logging.INFO, logger="app.rag")

    sample_chunks = [
        RetrievedChunk(
            chunk_id="chunk_01",
            text="Confidential document text that should NEVER be logged.",
            source="docs/overview.md",
            source_name="overview.md",
            page=None,
            distance=0.15,
        ),
        RetrievedChunk(
            chunk_id="chunk_02",
            text="Second chunk content with proprietary information.",
            source="docs/arch.md",
            source_name="arch.md",
            page=1,
            distance=0.22,
        ),
    ]

    mock_retrieval = MagicMock()
    mock_retrieval.retrieve.return_value = sample_chunks
    mock_retrieval.top_k = 4

    mock_gemini = MagicMock()
    mock_gemini.model = "gemini-3.6-flash"
    mock_gemini.generate = AsyncMock(
        return_value="Answer mentioning overview and architecture."
    )

    rag = RagService(
        retrieval_service=mock_retrieval,
        gemini_service=mock_gemini,
    )

    sensitive_question = "What is the secret deployment key password?"
    response = await rag.ask(sensitive_question)

    assert response.answer.startswith("Answer mentioning")
    assert len(response.sources) == 2

    # Verify emitted events
    events = [record.getMessage() for record in caplog.records if record.name == "app.rag"]
    assert "rag_request_started" in events
    assert "retrieval_completed" in events
    assert "generation_completed" in events
    assert "rag_request_completed" in events

    # Inspect records for safe metadata and absence of sensitive payload data
    for record in caplog.records:
        if record.name != "app.rag":
            continue
        msg = record.getMessage()

        # PRIVACY ASSERTIONS: neither question, chunk texts, nor answer should be in logs
        assert sensitive_question not in str(record.__dict__)
        assert "Confidential document text" not in str(record.__dict__)
        assert "Second chunk content" not in str(record.__dict__)
        assert "Answer mentioning overview" not in str(record.__dict__)

        # METADATA ASSERTIONS
        if msg == "rag_request_started":
            assert record.question_length == len(sensitive_question)  # type: ignore[attr-defined]
            assert record.top_k == 4  # type: ignore[attr-defined]
        elif msg == "retrieval_completed":
            assert record.chunks_returned == 2  # type: ignore[attr-defined]
            assert record.source_count == 2  # type: ignore[attr-defined]
            assert record.duration_ms >= 0  # type: ignore[attr-defined]
        elif msg == "generation_completed":
            assert record.model == "gemini-3.6-flash"  # type: ignore[attr-defined]
            assert record.citation_count == 2  # type: ignore[attr-defined]
            assert record.duration_ms >= 0  # type: ignore[attr-defined]
        elif msg == "rag_request_completed":
            assert record.duration_ms >= 0  # type: ignore[attr-defined]


def test_structured_error_logging_on_empty_knowledge_base(client, caplog) -> None:
    caplog.set_level(logging.WARNING, logger="app.rag")

    class EmptyKbRag:
        async def ask(self, question: str) -> Any:
            raise EmptyKnowledgeBaseError("The knowledge base is empty.")

    app.dependency_overrides[get_rag_service] = EmptyKbRag
    try:
        response = client.post("/ask", json={"question": "Hello?"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "X-Request-ID" in response.headers

    # Verify structured error log was recorded
    records = [r for r in caplog.records if r.name == "app.rag"]
    assert any(
        r.getMessage() == "rag_request_failed"
        and getattr(r, "error_category", None) == "empty_knowledge_base"
        and getattr(r, "stage", None) == "retrieval"
        for r in records
    )


def test_structured_error_logging_on_provider_error(client, caplog) -> None:
    caplog.set_level(logging.ERROR, logger="app.rag")

    class FailingRag:
        async def ask(self, question: str) -> Any:
            raise GenerationError("Gemini rate limit reached.")

    app.dependency_overrides[get_rag_service] = FailingRag
    try:
        response = client.post("/ask", json={"question": "Trigger rate limit"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert "X-Request-ID" in response.headers

    records = [r for r in caplog.records if r.name == "app.rag"]
    assert any(
        r.getMessage() == "rag_request_failed"
        and getattr(r, "error_category", None) == "provider"
        and getattr(r, "stage", None) == "generation"
        for r in records
    )


def test_health_check_logged_at_debug_level(client, caplog) -> None:
    """Routine 200 /health checks should be logged at DEBUG level to minimize noise."""
    caplog.set_level(logging.DEBUG, logger="app.http")
    response = client.get("/health")
    assert response.status_code == 200

    http_records = [r for r in caplog.records if r.name == "app.http"]
    health_records = [r for r in http_records if getattr(r, "path", None) == "/health"]
    assert len(health_records) >= 1
    # Check that routine /health is logged at DEBUG, NOT INFO
    assert health_records[0].levelno == logging.DEBUG
