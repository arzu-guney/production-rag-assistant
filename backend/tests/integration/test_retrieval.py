from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import Settings
from app.ingestion.indexer import index_documents
from app.services.embeddings import EmbeddingService
from app.services.retrieval import RetrievalService
from app.services.vector_store import VectorStore


@pytest.mark.slow
def test_relevant_query_retrieves_expected_evidence(tmp_path: Path) -> None:
    docs_dir = tmp_path / "documents"
    docs_dir.mkdir()
    (docs_dir / "kb.md").write_text(
        "\n".join(
            [
                "Retrieval-Augmented Generation retrieves relevant text before answering.",
                "Chunk size controls how much text each embedding vector represents.",
                "The same embedding model must be used for documents and queries.",
                "A vector database stores embeddings, chunk text, and metadata.",
            ]
        ),
        encoding="utf-8",
    )

    vector_dir = tmp_path / "vector_store"
    settings = Settings(
        embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
        chunk_size=200,
        chunk_overlap=40,
        vector_db_path=vector_dir,
        collection_name="test_retrieval",
        documents_path=docs_dir,
        retrieval_top_k=3,
    )
    summary = index_documents(docs_dir, settings=settings)
    assert summary.chunks_indexed > 0

    retrieval = RetrievalService(
        embedding_service=EmbeddingService(settings.embedding_model_name),
        vector_store=VectorStore(vector_dir, "test_retrieval"),
        top_k=3,
    )
    chunks = retrieval.retrieve("Why must documents and queries use the same embedding model?")
    joined = " ".join(chunk.text.lower() for chunk in chunks)
    assert "same embedding model" in joined or "documents and queries" in joined
