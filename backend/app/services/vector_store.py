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
        # Avoids noisy ClientStartEvent / ClientCreateCollectionEvent warnings
        # from a telemetry client mismatch while leaving real errors visible.
        self._client = chromadb.PersistentClient(
            path=str(self.persist_path),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return int(self._collection.count())

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
