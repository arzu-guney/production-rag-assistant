from __future__ import annotations

from pathlib import Path

import pytest

from app.ingestion.indexer import index_documents
from app.core.config import Settings
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


@pytest.mark.slow
def test_indexing_is_idempotent(tmp_path: Path) -> None:
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    (docs_dir / "note.md").write_text(
        "Retrieval-Augmented Generation grounds answers in documents.\n" * 20,
        encoding="utf-8",
    )

    vector_dir = tmp_path / "vector_store"
    settings = Settings(
        embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
        chunk_size=120,
        chunk_overlap=20,
        vector_db_path=vector_dir,
        collection_name="test_idempotent",
        documents_path=docs_dir,
    )

    first = index_documents(docs_dir, settings=settings)
    assert first.chunks_indexed > 0
    assert not first.errors

    store = VectorStore(persist_path=vector_dir, collection_name="test_idempotent")
    count_after_first = store.count

    second = index_documents(docs_dir, settings=settings)
    assert second.chunks_indexed == first.chunks_indexed
    assert store.count == count_after_first
