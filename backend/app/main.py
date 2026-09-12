"""FastAPI application entrypoint with structured logging and request correlation."""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from app.core.config import get_settings
from app.core.logging import (
    configure_logging,
    get_logger,
    reset_request_id,
    resolve_request_id,
    set_request_id,
)
from app.routers.ask import router as ask_router
from app.schemas.health import HealthResponse

# Initialize logging eagerly on module import with current settings
_settings = get_settings()
configure_logging(
    log_level=_settings.log_level,
    log_format=_settings.log_format,
)

http_logger = get_logger("app.http")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Ensure logging is properly configured for the application lifecycle."""
    settings = get_settings()
    configure_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
    )
    yield


app = FastAPI(
    title="production-rag-assistant",
    description=(
        "Production-oriented RAG learning project. "
        "Indexes local documents and answers questions with Gemini grounding."
    ),
    version="0.2.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def correlation_and_request_logging_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """Assign/reuse correlation ID, trace execution, and log request completion."""
    raw_id = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    request_id = resolve_request_id(raw_id)
    token = set_request_id(request_id)

    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception:
        status_code = 500
        raise
    finally:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        _log_http_completion(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
            request_id=request_id,
        )
        reset_request_id(token)


def _log_http_completion(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    request_id: str,
) -> None:
    """Log one completion event per request with safe metadata only.

    Routine successful /health probes are logged at DEBUG level to avoid flooding
    container logs. Failed health checks (>= 400) are logged at WARNING/ERROR.
    """
    if path == "/health" and status_code < 400:
        log_fn = http_logger.debug
    elif status_code >= 500:
        log_fn = http_logger.error
    elif status_code >= 400:
        log_fn = http_logger.warning
    else:
        log_fn = http_logger.info

    log_fn(
        "http_request_completed",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        },
    )


app.include_router(ask_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="production-rag-assistant")
