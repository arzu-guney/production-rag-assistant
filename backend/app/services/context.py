from __future__ import annotations

from app.services.retrieval import RetrievedChunk


def build_context(chunks: list[RetrievedChunk]) -> str:
    """Build labelled context blocks for the LLM from retrieved chunks.

    Structured labels preserve a clear mapping from each block to source
    metadata. That helps citations, debugging, evaluation, and makes it
    clearer that retrieved text is reference material — not system instructions.
    """
    if not chunks:
        return ""

    blocks: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        page_line = (
            f"Page: {chunk.page}" if chunk.page is not None else "Page: n/a"
        )
        distance_line = (
            f"Distance: {chunk.distance:.4f}"
            if chunk.distance is not None
            else "Distance: n/a"
        )
        blocks.append(
            "\n".join(
                [
                    f"[SOURCE {index}]",
                    f"File: {chunk.source_name}",
                    f"Chunk ID: {chunk.chunk_id}",
                    page_line,
                    distance_line,
                    "Content:",
                    chunk.text,
                ]
            )
        )
    return "\n\n".join(blocks)
