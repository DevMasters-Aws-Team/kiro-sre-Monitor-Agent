from fastapi import APIRouter

from src.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "environment": settings.environment}
