from pydantic import BaseModel, Field, field_validator

# Keep questions readable for humans and safe for later RAG prompts.
QUESTION_MAX_LENGTH = 2000


class AskRequest(BaseModel):
    """Incoming question for the future RAG pipeline."""

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


class AskResponse(BaseModel):
    """Answer contract for /ask. Sources will be filled when retrieval exists."""

    answer: str = Field(..., description="Generated answer text.")
    sources: list[str] = Field(
        default_factory=list,
        description="Document sources used for the answer. Empty until retrieval is implemented.",
    )
