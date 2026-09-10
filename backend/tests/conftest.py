from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ask import AskResponse, SourceCitation


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class FakeRagService:
    """Deterministic stand-in so API tests never call Gemini."""

    async def ask(self, question: str) -> AskResponse:
        return AskResponse(
            answer=f"Deterministic fake answer for: {question}",
            sources=[
                SourceCitation(
                    source="sample-rag-overview.md",
                    page=None,
                    chunk_id="chunk_fake_001",
                )
            ],
        )
