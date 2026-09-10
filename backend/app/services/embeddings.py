from __future__ import annotations

from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Create dense vectors for document chunks and future queries.

    Documents and queries must use the same model so their vectors live
    in the same semantic space.
    """

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    @property
    def dimension(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed one or more texts. Returns one vector per input string."""
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [vector.tolist() for vector in vectors]

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string (used later for retrieval)."""
        return self.embed_texts([query])[0]
