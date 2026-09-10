from app.schemas.ask import QUESTION_MAX_LENGTH


def test_missing_question_rejected(client) -> None:
    response = client.post("/ask", json={})
    assert response.status_code == 422


def test_empty_question_rejected(client) -> None:
    response = client.post("/ask", json={"question": ""})
    assert response.status_code == 422


def test_whitespace_only_question_rejected(client) -> None:
    response = client.post("/ask", json={"question": "   "})
    assert response.status_code == 422


def test_excessively_long_question_rejected(client) -> None:
    response = client.post(
        "/ask",
        json={"question": "x" * (QUESTION_MAX_LENGTH + 1)},
    )
    assert response.status_code == 422
