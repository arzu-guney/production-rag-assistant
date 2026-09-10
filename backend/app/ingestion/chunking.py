from __future__ import annotations

import hashlib
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


def chunk_document(
    document: LoadedDocument,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Chunk]:
    """Split one LoadedDocument into overlapping character windows."""
    validate_chunk_config(chunk_size, chunk_overlap)

    text = document.text.strip()
    if not text:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[Chunk] = []
    start = 0
    chunk_index = 0
    source_name = Path(document.source).name

    while start < len(text):
        end = min(start + chunk_size, len(text))
        piece = text[start:end].strip()
        if piece:
            metadata: dict[str, str | int | float | bool] = {
                "source": document.source,
                "source_name": source_name,
                "doc_type": document.doc_type,
                "chunk_index": chunk_index,
                "char_start": start,
                "char_end": end,
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

        if end >= len(text):
            break
        start += step

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
