"""Application-level errors for the RAG pipeline."""


class RagError(Exception):
    """Base class for RAG failures that can be mapped to HTTP responses."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ConfigurationError(RagError):
    """Missing or invalid configuration (for example Gemini API key)."""


class EmptyKnowledgeBaseError(RagError):
    """Vector collection has no indexed documents."""


class NoRelevantContextError(RagError):
    """Retrieval returned no usable chunks for the question."""


class RetrievalError(RagError):
    """Embedding or vector-store failure during retrieval."""


class GenerationError(RagError):
    """Gemini API or response failure."""
