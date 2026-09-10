from fastapi import APIRouter

from app.schemas.ask import AskRequest, AskResponse

router = APIRouter(tags=["ask"])

PLACEHOLDER_ANSWER = (
    "RAG pipeline is not implemented yet. "
    "This endpoint currently defines the typed API contract only. "
    "Document ingestion, retrieval, embeddings, and LLM generation will be added later."
)


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest) -> AskResponse:
    """Accept a question and return a placeholder until the RAG pipeline exists."""
    return AskResponse(answer=PLACEHOLDER_ANSWER, sources=[])
