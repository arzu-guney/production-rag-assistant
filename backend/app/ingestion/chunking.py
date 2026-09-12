"""Document chunking strategies for vector indexing.

Provides boundary-aware semantic chunking that respects paragraphs,
headings, sentences, and words to avoid mid-token splits and preserve
coherent retrieval units.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from app.ingestion.loaders import LoadedDocument


@dataclass(frozen=True)
class Chunk:
    """A text chunk ready for embedding and vector storage."""

    id: str
    text: str
    metadata: dict[str, str | int | float | bool]


class ChunkConfigError(ValueError):
    """Raised when chunk size / overlap settings are invalid."""


def validate_chunk_config(chunk_size: int, chunk_overlap: int) -> None:
    if chunk_size <= 0:
        raise ChunkConfigError("chunk_size must be a positive integer")
    if chunk_overlap < 0:
        raise ChunkConfigError("chunk_overlap must be >= 0")
    if chunk_overlap >= chunk_size:
        raise ChunkConfigError("chunk_overlap must be smaller than chunk_size")


def make_chunk_id(source: str, chunk_index: int, page_number: int | None = None) -> str:
    """Deterministic ID so re-indexing the same file upserts instead of duplicating."""
    page_key = page_number if page_number is not None else "na"
    digest = hashlib.sha256(
        f"{source}::page::{page_key}::chunk::{chunk_index}".encode("utf-8")
    ).hexdigest()
    return f"chunk_{digest[:24]}"


_HEADER_PATTERN = re.compile(r"^\s*#{1,6}\s+", re.MULTILINE)
_SENTENCE_END_PATTERN = re.compile(r"([.?!])(?:\s+|\Z)")


def _find_chunk_end(text: str, start: int, max_end: int) -> int:
    """Find a natural boundary at or before max_end for text starting at start."""
    if max_end >= len(text):
        return len(text)

    window = text[start:max_end]

    # 1. Paragraph boundary (\n\n)
    p_idx = window.rfind("\n\n")
    if p_idx > 0:
        candidate_end = start + p_idx
        # Check if the text immediately following is a header, e.g. "\n\n## Title"
        # If candidate_end is chosen, the header starts cleanly in the next chunk.
        return candidate_end

    # 2. Line boundary (\n)
    n_idx = window.rfind("\n")
    if n_idx > 0:
        return start + n_idx

    # 3. Sentence boundary (. / ? / !)
    sentence_matches = list(_SENTENCE_END_PATTERN.finditer(window))
    if sentence_matches:
        last_match = sentence_matches[-1]
        # Break immediately after the punctuation mark
        return start + last_match.end(1)

    # 4. Word boundary (' ')
    sp_idx = window.rfind(" ")
    if sp_idx > 0:
        return start + sp_idx

    # 5. Fallback: hard cut at max_end (e.g. unbroken token)
    return max_end


def _find_next_start(text: str, start: int, chunk_end: int, chunk_overlap: int) -> int:
    """Find a clean boundary for the start of the next overlapping chunk."""
    if chunk_overlap <= 0:
        next_pos = chunk_end
    else:
        target_start = max(start + 1, chunk_end - chunk_overlap)
        overlap_window = text[target_start:chunk_end]

        # Look for clean start within the overlap window
        # Prefer starting after paragraph break, line break, sentence end, or space
        p_idx = overlap_window.find("\n\n")
        if p_idx != -1:
            next_pos = target_start + p_idx + 2
        else:
            n_idx = overlap_window.find("\n")
            if n_idx != -1:
                next_pos = target_start + n_idx + 1
            else:
                sent_match = _SENTENCE_END_PATTERN.search(overlap_window)
                if sent_match:
                    next_pos = target_start + sent_match.end()
                else:
                    sp_idx = overlap_window.find(" ")
                    if sp_idx != -1:
                        next_pos = target_start + sp_idx + 1
                    else:
                        next_pos = target_start

    # Guarantee forward progress
    if next_pos <= start:
        next_pos = start + 1

    # Skip leading whitespace at the beginning of the next chunk
    while next_pos < len(text) and text[next_pos].isspace() and next_pos < chunk_end:
        next_pos += 1

    return next_pos


def chunk_document(
    document: LoadedDocument,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    """Split one LoadedDocument into boundary-aware semantic chunks."""
    validate_chunk_config(chunk_size, chunk_overlap)

    text = document.text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        metadata: dict[str, str | int | float | bool] = {
            "source": document.source,
            "source_name": Path(document.source).name,
            "doc_type": document.doc_type,
            "chunk_index": 0,
            "char_start": 0,
            "char_end": len(text),
        }
        if document.page_number is not None:
            metadata["page_number"] = document.page_number
        return [
            Chunk(
                id=make_chunk_id(document.source, 0, page_number=document.page_number),
                text=text,
                metadata=metadata,
            )
        ]

    chunks: list[Chunk] = []
    start = 0
    chunk_index = 0
    source_name = Path(document.source).name

    while start < len(text):
        # Skip leading whitespace
        while start < len(text) and text[start].isspace():
            start += 1
        if start >= len(text):
            break

        max_end = min(start + chunk_size, len(text))
        chunk_end = _find_chunk_end(text, start, max_end)

        piece = text[start:chunk_end].strip()
        if piece:
            metadata = {
                "source": document.source,
                "source_name": source_name,
                "doc_type": document.doc_type,
                "chunk_index": chunk_index,
                "char_start": start,
                "char_end": chunk_end,
            }
            if document.page_number is not None:
                metadata["page_number"] = document.page_number

            chunks.append(
                Chunk(
                    id=make_chunk_id(
                        document.source,
                        chunk_index,
                        page_number=document.page_number,
                    ),
                    text=piece,
                    metadata=metadata,
                )
            )
            chunk_index += 1

        if chunk_end >= len(text):
            break

        start = _find_next_start(text, start, chunk_end, chunk_overlap)

    return chunks


def chunk_documents(
    documents: list[LoadedDocument],
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    """Chunk many loaded documents with the same configuration."""
    validate_chunk_config(chunk_size, chunk_overlap)
    results: list[Chunk] = []
    for document in documents:
        results.extend(
            chunk_document(
                document,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        )
    return results
