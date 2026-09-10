from __future__ import annotations

import asyncio

from app.core.exceptions import NoRelevantContextError
from app.prompts import SYSTEM_INSTRUCTION, build_user_prompt
from app.schemas.ask import AskResponse, SourceCitation
from app.services.context import build_context
from app.services.gemini import GeminiService
from app.services.retrieval import RetrievedChunk, RetrievalService


class RagService:
    """Orchestrate retrieve → context → generate → citations."""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        gemini_service: GeminiService,
    ) -> None:
        self._retrieval = retrieval_service
        self._gemini = gemini_service

    async def ask(self, question: str) -> AskResponse:
        # Local embedding + Chroma query are CPU/disk bound → run in a worker thread.
        chunks = await asyncio.to_thread(self._retrieval.retrieve, question)
        if not chunks:
            raise NoRelevantContextError(
                "No relevant document chunks were retrieved for this question."
            )

        context = build_context(chunks)
        user_prompt = build_user_prompt(question=question, context=context)

        # Gemini is network-bound → use the SDK async client.
        answer = await self._gemini.generate(
            system_instruction=SYSTEM_INSTRUCTION,
            user_prompt=user_prompt,
        )
        return AskResponse(
            answer=answer,
            sources=_citations_from_chunks(chunks),
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
