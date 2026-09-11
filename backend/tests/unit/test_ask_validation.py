from app.dependencies import get_rag_service
from app.main import app
from app.schemas.ask import QUESTION_MAX_LENGTH
from tests.conftest import FakeRagService


def _post_ask(client, payload: dict):
    """POST /ask with a fake RAG dependency so validation never needs Gemini."""
    app.dependency_overrides[get_rag_service] = FakeRagService
    try:
        return client.post("/ask", json=payload)
    finally:
        app.dependency_overrides.clear()


def test_missing_question_rejected(client) -> None:
    response = _post_ask(client, {})
    assert response.status_code == 422


def test_empty_question_rejected(client) -> None:
    response = _post_ask(client, {"question": ""})
    assert response.status_code == 422


def test_whitespace_only_question_rejected(client) -> None:
    response = _post_ask(client, {"question": "   "})
    assert response.status_code == 422


def test_excessively_long_question_rejected(client) -> None:
    response = _post_ask(
        client,
        {"question": "x" * (QUESTION_MAX_LENGTH + 1)},
    )
    assert response.status_code == 422
