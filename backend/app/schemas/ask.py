from pydantic import BaseModel, Field, field_validator

# Keep questions readable for humans and safe for later RAG prompts.
QUESTION_MAX_LENGTH = 2000


class AskRequest(BaseModel):
    """Incoming question for the RAG pipeline."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=QUESTION_MAX_LENGTH,
        description="The user's question.",
        examples=["What is retrieval-augmented generation?"],
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be empty or whitespace only")
        return stripped


class SourceCitation(BaseModel):
    """Deterministic citation built from retrieved chunk metadata."""

    source: str = Field(..., description="Source filename of the retrieved chunk.")
    page: int | None = Field(
        default=None,
        description="PDF page number when available; null for txt/md.",
    )
    chunk_id: str = Field(..., description="Stable chunk identifier from the index.")


class AskResponse(BaseModel):
    """Grounded answer plus retrieval-based source citations."""

    answer: str = Field(..., description="Generated answer text.")
    sources: list[SourceCitation] = Field(
        default_factory=list,
        description="Citations derived from retrieved chunks (not invented by the LLM).",
    )
