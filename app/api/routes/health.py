from fastapi import APIRouter
from typing import Dict

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy"}


@router.get("/readiness")
def readiness_check() -> Dict[str, str]:
    """Readiness check endpoint (can be expanded later)."""
    return {"status": "ready"}
