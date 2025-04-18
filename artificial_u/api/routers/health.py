import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from artificial_u.api.config import Settings, get_settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""

    status: str
    api_version: str
    timestamp: float


@router.get("", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Health check endpoint to verify API is running
    """
    return {"status": "ok", "api_version": "v1", "timestamp": time.time()}
