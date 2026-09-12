"""Unit tests for structured logging and request correlation utilities."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime

from app.core.logging import (
    PlainTextFormatter,
    StructuredJsonFormatter,
    get_request_id,
    is_valid_request_id,
    reset_request_id,
    resolve_request_id,
    set_request_id,
)


def test_is_valid_request_id() -> None:
    # Valid IDs
    assert is_valid_request_id("valid-req-id-123")
    assert is_valid_request_id(str(uuid.uuid4()))
    assert is_valid_request_id("client_abc.01")
    assert is_valid_request_id("a" * 128)

    # Invalid IDs
    assert not is_valid_request_id("")
    assert not is_valid_request_id("   ")
    assert not is_valid_request_id(None)
    assert not is_valid_request_id("invalid id with spaces")
    assert not is_valid_request_id("newline\ninjection")
    assert not is_valid_request_id("carriage\rreturn")
    assert not is_valid_request_id("a" * 129)  # exceeds 128 chars
    assert not is_valid_request_id("<script>")


def test_resolve_request_id_reuses_valid_id() -> None:
    client_id = "safe-client-correlation-42"
    assert resolve_request_id(client_id) == client_id


def test_resolve_request_id_generates_uuid_for_invalid_id() -> None:
    bad_id = "bad id with spaces\n"
    resolved = resolve_request_id(bad_id)
    assert resolved != bad_id
    # Must be a valid UUID4
    parsed = uuid.UUID(resolved, version=4)
    assert str(parsed) == resolved


def test_resolve_request_id_generates_uuid_when_omitted() -> None:
    resolved = resolve_request_id(None)
    parsed = uuid.UUID(resolved, version=4)
    assert str(parsed) == resolved


def test_contextvar_set_get_reset() -> None:
    assert get_request_id() is None

    test_id = "test-correlator-999"
    token = set_request_id(test_id)
    assert get_request_id() == test_id

    reset_request_id(token)
    assert get_request_id() is None


def test_structured_json_formatter_standard_fields() -> None:
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="test_event_name",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert parsed["event"] == "test_event_name"
    assert "timestamp" in parsed
    # Timestamp should parse cleanly as ISO-8601
    dt = datetime.fromisoformat(parsed["timestamp"])
    assert dt is not None
    # No request_id set in context
    assert "request_id" not in parsed


def test_structured_json_formatter_with_request_id_and_extras() -> None:
    formatter = StructuredJsonFormatter()
    token = set_request_id("req-json-formatter-test")
    try:
        record = logging.LogRecord(
            name="app.rag",
            level=logging.INFO,
            pathname=__file__,
            lineno=25,
            msg="retrieval_completed",
            args=(),
            exc_info=None,
        )
        record.top_k = 4  # type: ignore[attr-defined]
        record.chunks_returned = 2  # type: ignore[attr-defined]
        record.duration_ms = 14.5  # type: ignore[attr-defined]

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["event"] == "retrieval_completed"
        assert parsed["request_id"] == "req-json-formatter-test"
        assert parsed["top_k"] == 4
        assert parsed["chunks_returned"] == 2
        assert parsed["duration_ms"] == 14.5
    finally:
        reset_request_id(token)


def test_structured_json_formatter_formats_exceptions_safely() -> None:
    formatter = StructuredJsonFormatter()
    try:
        raise ValueError("simulated internal error")
    except ValueError:
        import sys

        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="app.error",
        level=logging.ERROR,
        pathname=__file__,
        lineno=50,
        msg="unexpected_failure",
        args=(),
        exc_info=exc_info,
    )

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["event"] == "unexpected_failure"
    assert parsed["level"] == "ERROR"
    assert "exception" in parsed
    assert "ValueError: simulated internal error" in parsed["exception"]


def test_plain_text_formatter_with_request_id() -> None:
    formatter = PlainTextFormatter(fmt="%(levelname)s %(message)s")
    token = set_request_id("plain-req-123")
    try:
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=60,
            msg="simple text message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)
        assert "[req:plain-req-123]" in formatted
        assert "simple text message" in formatted
    finally:
        reset_request_id(token)
