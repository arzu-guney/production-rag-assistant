from fastapi import FastAPI

from app.routers.ask import router as ask_router
from app.schemas.health import HealthResponse

app = FastAPI(
    title="production-rag-assistant",
    description="Learning project backend. RAG is not implemented yet.",
    version="0.1.0",
)

app.include_router(ask_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="production-rag-assistant")
