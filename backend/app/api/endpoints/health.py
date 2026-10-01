from fastapi import APIRouter
from backend.app.schemas.health import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health() -> HealthResponse:
    """Return health status of the GlaucoMap backend service."""
    return HealthResponse(
        status="ok",
        service="glaucomap-backend",
    )
