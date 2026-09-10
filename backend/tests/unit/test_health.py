def test_health_returns_ok(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {"status": "ok", "service": "production-rag-assistant"}
