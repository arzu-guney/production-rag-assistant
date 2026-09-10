from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings


def _sanitize_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Chroma only accepts str/int/float/bool metadata values."""
    cleaned: dict[str, str | int | float | bool] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        else:
            cleaned[key] = str(value)
    return cleaned


class VectorStore:
    """Persistent ChromaDB store for chunk text, embeddings, and metadata."""

    def __init__(self, persist_path: Path, collection_name: str) -> None:
        self.persist_path = Path(persist_path)
        self.collection_name = collection_name
        self.persist_path.mkdir(parents=True, exist_ok=True)
        # Disable anonymized telemetry via supported Chroma settings.
        # Also keep PostHog pinned <4 in requirements.txt: newer PostHog breaks
        # Chroma's capture() call and logs noisy Client*Event failures even when
        # anonymized_telemetry=False.
        self._client = chromadb.PersistentClient(
            path=str(self.persist_path),
            settings=Settings(
                anonymized_telemetry=False,
                is_persistent=True,
            ),
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return int(self._collection.count())

    def query(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
    ) -> dict[str, list]:
        """Return nearest chunks for a query embedding.

        Chroma is configured with cosine space. Returned ``distances`` are
        cosine distances (lower is closer), not similarity scores.
        """
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        return self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

    def upsert_chunks(
        self,
        *,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> int:
        """Insert or update chunks by stable IDs (avoids accidental duplicates)."""
        if not (len(ids) == len(documents) == len(embeddings) == len(metadatas)):
            raise ValueError(
                "ids, documents, embeddings, and metadatas must have the same length"
            )
        if not ids:
            return 0

        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=[_sanitize_metadata(item) for item in metadatas],
        )
        return len(ids)
