from fastapi import APIRouter

from app.models.schemas import HealthStatus
from app.services.qdrant_service import qdrant_service
from app.services.embedding_service import embedding_service

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Health check endpoint.
    Verifies Qdrant connectivity and DashScope API access.
    """
    # Check Qdrant
    try:
        qdrant_ok = qdrant_service.collection_exists()
    except Exception:
        qdrant_ok = False

    # Check DashScope
    try:
        dashscope_ok = embedding_service.check_api_health()
    except Exception:
        dashscope_ok = False

    overall_status = "healthy" if (qdrant_ok and dashscope_ok) else "degraded"

    return HealthStatus(
        status=overall_status,
        qdrant=qdrant_ok,
        dashscope=dashscope_ok,
    )
