"""RAG ask endpoint with structured error logging."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.exceptions import (
    ConfigurationError,
    EmptyKnowledgeBaseError,
    GenerationError,
    NoRelevantContextError,
    RagError,
    RetrievalError,
)
from app.core.logging import get_logger
from app.dependencies import get_rag_service
from app.schemas.ask import AskRequest, AskResponse
from app.services.rag import RagService

logger = get_logger("app.rag")
router = APIRouter(tags=["ask"])


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    payload: AskRequest,
    rag: RagService = Depends(get_rag_service),
) -> AskResponse:
    """Retrieve context, generate a grounded Gemini answer, and return citations."""
    try:
        return await rag.ask(payload.question)
    except ConfigurationError as exc:
        logger.warning(
            "rag_request_failed",
            extra={
                "error_category": "configuration",
                "stage": "configuration",
                "safe_message": exc.message,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc
    except EmptyKnowledgeBaseError as exc:
        logger.warning(
            "rag_request_failed",
            extra={
                "error_category": "empty_knowledge_base",
                "stage": "retrieval",
                "safe_message": exc.message,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        ) from exc
    except NoRelevantContextError as exc:
        logger.info(
            "rag_request_failed",
            extra={
                "error_category": "no_relevant_context",
                "stage": "retrieval",
                "safe_message": exc.message,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        ) from exc
    except RetrievalError as exc:
        logger.error(
            "rag_request_failed",
            extra={
                "error_category": "retrieval",
                "stage": "retrieval",
                "safe_message": exc.message,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.message,
        ) from exc
    except GenerationError as exc:
        logger.error(
            "rag_request_failed",
            extra={
                "error_category": "provider",
                "stage": "generation",
                "safe_message": exc.message,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=exc.message,
        ) from exc
    except RagError as exc:
        logger.error(
            "rag_request_failed",
            extra={
                "error_category": "rag_general",
                "stage": "pipeline",
                "safe_message": exc.message,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        ) from exc
    except Exception as exc:
        logger.exception(
            "rag_request_unexpected_failure",
            extra={
                "error_category": "unexpected",
                "stage": "unknown",
                "safe_message": str(exc),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during RAG processing.",
        ) from exc
