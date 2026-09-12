from __future__ import annotations

import asyncio
import time

from app.core.exceptions import NoRelevantContextError
from app.core.logging import get_logger
from app.prompts import SYSTEM_INSTRUCTION, build_user_prompt
from app.schemas.ask import AskResponse, SourceCitation
from app.services.context import build_context
from app.services.gemini import GeminiService
from app.services.retrieval import RetrievedChunk, RetrievalService

logger = get_logger("app.rag")


class RagService:
    """Orchestrate retrieve → context → generate → citations with stage observability."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        gemini_service: GeminiService,
    ) -> None:
        self._retrieval = retrieval_service
        self._gemini = gemini_service

    async def ask(self, question: str) -> AskResponse:
        rag_start = time.perf_counter()
        logger.info(
            "rag_request_started",
            extra={
                "question_length": len(question),
                "top_k": self._retrieval.top_k,
            },
        )

        # Stage 1: Retrieval (CPU/disk bound → run in worker thread)
        retrieval_start = time.perf_counter()
        chunks = await asyncio.to_thread(self._retrieval.retrieve, question)
        retrieval_duration_ms = round((time.perf_counter() - retrieval_start) * 1000, 2)

        distinct_sources = len({c.source for c in chunks if c.source})
        logger.info(
            "retrieval_completed",
            extra={
                "top_k": self._retrieval.top_k,
                "chunks_returned": len(chunks),
                "source_count": distinct_sources,
                "duration_ms": retrieval_duration_ms,
            },
        )

        if not chunks:
            raise NoRelevantContextError(
                "No relevant document chunks were retrieved for this question."
            )

        context = build_context(chunks)
        user_prompt = build_user_prompt(question=question, context=context)

        # Stage 2: Generation (Network I/O bound → async SDK client)
        gen_start = time.perf_counter()
        answer = await self._gemini.generate(
            system_instruction=SYSTEM_INSTRUCTION,
            user_prompt=user_prompt,
        )
        gen_duration_ms = round((time.perf_counter() - gen_start) * 1000, 2)

        citations = _citations_from_chunks(chunks)
        logger.info(
            "generation_completed",
            extra={
                "model": self._gemini.model,
                "duration_ms": gen_duration_ms,
                "citation_count": len(citations),
            },
        )

        # Stage 3: Total pipeline completion
        total_duration_ms = round((time.perf_counter() - rag_start) * 1000, 2)
        logger.info(
            "rag_request_completed",
            extra={
                "duration_ms": total_duration_ms,
            },
        )

        return AskResponse(
            answer=answer,
            sources=citations,
        )


def _citations_from_chunks(chunks: list[RetrievedChunk]) -> list[SourceCitation]:
    """Build deterministic citations from retrieval metadata (not from the LLM)."""
    citations: list[SourceCitation] = []
    seen: set[str] = set()
    for chunk in chunks:
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        citations.append(
            SourceCitation(
                source=chunk.source_name,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
            )
        )
    return citations
