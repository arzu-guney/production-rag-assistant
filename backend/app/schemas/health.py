from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Simple liveness response for GET /health."""

    status: str = Field(..., description="Service health status.")
    service: str = Field(..., description="Service name.")
