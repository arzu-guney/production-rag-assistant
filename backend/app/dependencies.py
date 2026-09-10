from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.services.embeddings import EmbeddingService
from app.services.gemini import GeminiService
from app.services.rag import RagService
from app.services.retrieval import RetrievalService
from app.services.vector_store import VectorStore


@lru_cache
def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    return EmbeddingService(settings.embedding_model_name)


@lru_cache
def get_vector_store() -> VectorStore:
    settings = get_settings()
    return VectorStore(
        persist_path=settings.vector_db_path,
        collection_name=settings.collection_name,
    )


def get_rag_service() -> RagService:
    settings = get_settings()
    retrieval = RetrievalService(
        embedding_service=get_embedding_service(),
        vector_store=get_vector_store(),
        top_k=settings.retrieval_top_k,
    )
    gemini = GeminiService(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
    )
    return RagService(retrieval_service=retrieval, gemini_service=gemini)


def clear_service_caches() -> None:
    """Test helper to reset cached settings-backed services."""
    get_embedding_service.cache_clear()
    get_vector_store.cache_clear()
    get_settings.cache_clear()
