from app.dependencies import get_rag_service
from app.main import app
from tests.conftest import FakeRagService


def test_ask_with_fake_rag_returns_typed_response(client) -> None:
    app.dependency_overrides[get_rag_service] = FakeRagService
    try:
        response = client.post(
            "/ask",
            json={"question": "What is retrieval-augmented generation?"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"].startswith("Deterministic fake answer for:")
    assert payload["sources"] == [
        {
            "source": "sample-rag-overview.md",
            "page": None,
            "chunk_id": "chunk_fake_001",
        }
    ]
