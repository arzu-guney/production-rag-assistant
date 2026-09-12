"""Structured JSON logging and request correlation.

Provides:
- ContextVar-based request correlation ID propagation across async tasks
- A lightweight standard-library JSON formatter for structured runtime logs
- Request ID validation for client-supplied headers
- Global logging configuration directing structured logs to stdout
"""

from __future__ import annotations

import json
import logging
import re
import sys
import uuid
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any

# Correlation ID context variable for async execution
_REQUEST_ID_CTX: ContextVar[str | None] = ContextVar("request_id", default=None)

# Valid client request ID: alphanumeric, underscores, hyphens, dots, 1-128 chars
_REQUEST_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]{1,128}$")

# Standard LogRecord attributes to exclude from extra payload fields
_RESERVED_RECORD_ATTRS: frozenset[str] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }
)


def get_request_id() -> str | None:
    """Return the correlation ID for the current async execution context."""
    return _REQUEST_ID_CTX.get()


def set_request_id(request_id: str) -> Token[str | None]:
    """Bind a correlation ID to the current async context and return a reset token."""
    return _REQUEST_ID_CTX.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    """Reset the correlation ID to the state before set_request_id was called."""
    _REQUEST_ID_CTX.reset(token)


def is_valid_request_id(request_id: str | None) -> bool:
    """Validate client-supplied request ID for length and safe characters."""
    if not request_id or not isinstance(request_id, str):
        return False
    return bool(_REQUEST_ID_PATTERN.match(request_id))


def resolve_request_id(client_id: str | None = None) -> str:
    """Reuse valid client-supplied request ID or generate a new UUID4 string."""
    if client_id and is_valid_request_id(client_id):
        return client_id
    return str(uuid.uuid4())


class StructuredJsonFormatter(logging.Formatter):
    """Format LogRecord instances as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(
            record.created, tz=timezone.utc
        ).isoformat()

        event = getattr(record, "event", None) or record.getMessage()

        payload: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "event": event,
        }

        # Inject correlation ID: record explicit attribute or context variable
        request_id = getattr(record, "request_id", None) or get_request_id()
        if request_id is not None:
            payload["request_id"] = request_id

        # Merge custom extra fields, excluding standard LogRecord internals
        for key, value in record.__dict__.items():
            if (
                key not in _RESERVED_RECORD_ATTRS
                and key not in payload
                and key != "event"
            ):
                payload[key] = value

        # Exception formatting
        if record.exc_info:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            payload["exception"] = record.exc_text
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        return json.dumps(payload, default=str)


class PlainTextFormatter(logging.Formatter):
    """Human-readable formatter with request ID when available."""

    def format(self, record: logging.LogRecord) -> str:
        request_id = getattr(record, "request_id", None) or get_request_id()
        req_tag = f" [req:{request_id}]" if request_id else ""
        record.msg = f"{req_tag} {record.msg}" if req_tag else record.msg
        return super().format(record)


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "json",
) -> None:
    """Configure root logging to emit structured logs to stdout."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    if log_format.lower() == "text":
        handler.setFormatter(
            PlainTextFormatter(
                fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
            )
        )
    else:
        handler.setFormatter(StructuredJsonFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Suppress redundant default uvicorn access logs; custom middleware handles this
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a standard logger for the given name."""
    return logging.getLogger(name)
