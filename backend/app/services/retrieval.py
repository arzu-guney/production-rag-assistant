from __future__ import annotations

from dataclasses import dataclass

from app.core.exceptions import EmptyKnowledgeBaseError, RetrievalError
from app.services.embeddings import EmbeddingService
from app.services.vector_store import VectorStore


@dataclass(frozen=True)
class RetrievedChunk:
    """One retrieved chunk with text and citation metadata."""

    chunk_id: str
    text: str
    source: str
    source_name: str
    page: int | None
    distance: float | None


class RetrievalService:
    """Embed a question and fetch the nearest chunks from ChromaDB."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        top_k: int,
    ) -> None:
        self._embeddings = embedding_service
        self._vector_store = vector_store
        self._top_k = top_k

    @property
    def top_k(self) -> int:
        """Configured number of nearest chunks to retrieve."""
        return self._top_k

    def retrieve(self, question: str) -> list[RetrievedChunk]:
        if self._vector_store.count == 0:
            raise EmptyKnowledgeBaseError(
                "The knowledge base is empty. Index documents before calling /ask."
            )

        try:
            query_vector = self._embeddings.embed_query(question)
            raw = self._vector_store.query(
                query_embedding=query_vector,
                top_k=min(self._top_k, self._vector_store.count),
            )
        except EmptyKnowledgeBaseError:
            raise
        except Exception as exc:  # noqa: BLE001 - map store/embed failures cleanly
            raise RetrievalError(f"Retrieval failed: {exc}") from exc

        return _parse_chroma_results(raw)


def _parse_chroma_results(raw: dict[str, list]) -> list[RetrievedChunk]:
    ids = (raw.get("ids") or [[]])[0]
    documents = (raw.get("documents") or [[]])[0]
    metadatas = (raw.get("metadatas") or [[]])[0]
    distances = (raw.get("distances") or [[]])[0]

    chunks: list[RetrievedChunk] = []
    for index, chunk_id in enumerate(ids):
        text = documents[index] if index < len(documents) else None
        if not text or not str(text).strip():
            continue
        metadata = metadatas[index] if index < len(metadatas) else None
        if not isinstance(metadata, dict):
            metadata = {}
        distance = distances[index] if index < len(distances) else None
        page_value = metadata.get("page_number")
        page: int | None
        if isinstance(page_value, int):
            page = page_value
        elif isinstance(page_value, str) and page_value.isdigit():
            page = int(page_value)
        else:
            page = None

        source = str(metadata.get("source") or "")
        source_name = str(metadata.get("source_name") or source or "unknown")
        chunks.append(
            RetrievedChunk(
                chunk_id=str(chunk_id),
                text=str(text).strip(),
                source=source,
                source_name=source_name,
                page=page,
                distance=float(distance) if distance is not None else None,
            )
        )
    return chunks
