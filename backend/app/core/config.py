from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

# backend/ is the working directory when running: python -m app.ingestion.indexer
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    """Typed settings for the local RAG indexing pipeline.

    Override fields with environment variables (see get_settings).
    """

    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Local Sentence Transformers model used for embeddings.",
    )
    chunk_size: int = Field(
        default=500,
        ge=1,
        description="Maximum characters per chunk.",
    )
    chunk_overlap: int = Field(
        default=100,
        ge=0,
        description="Character overlap between consecutive chunks.",
    )
    vector_db_path: Path = Field(
        default=BACKEND_ROOT / "data" / "vector_store",
        description="Persistent ChromaDB directory (local, gitignored).",
    )
    collection_name: str = Field(
        default="documents",
        min_length=1,
        description="Chroma collection name for indexed chunks.",
    )
    documents_path: Path = Field(
        default=BACKEND_ROOT / "data" / "documents",
        description="Default directory for source documents.",
    )

    @model_validator(mode="after")
    def overlap_must_be_less_than_size(self) -> Settings:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self


def _env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


@lru_cache
def get_settings() -> Settings:
    """Load settings from environment variables with development defaults."""
    chunk_size = _env("CHUNK_SIZE")
    chunk_overlap = _env("CHUNK_OVERLAP")
    vector_db_path = _env("VECTOR_DB_PATH")
    documents_path = _env("DOCUMENTS_PATH")

    return Settings(
        embedding_model_name=_env(
            "EMBEDDING_MODEL_NAME",
            "sentence-transformers/all-MiniLM-L6-v2",
        )
        or "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size=int(chunk_size) if chunk_size else 500,
        chunk_overlap=int(chunk_overlap) if chunk_overlap else 100,
        vector_db_path=Path(vector_db_path)
        if vector_db_path
        else BACKEND_ROOT / "data" / "vector_store",
        collection_name=_env("COLLECTION_NAME", "documents") or "documents",
        documents_path=Path(documents_path)
        if documents_path
        else BACKEND_ROOT / "data" / "documents",
    )
