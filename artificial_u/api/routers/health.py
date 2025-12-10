import time
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from artificial_u.api.config import Settings, get_settings
from artificial_u.api.dependencies import get_repository_factory
from artificial_u.models.repositories import RepositoryFactory

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""

    status: str
    api_version: str
    timestamp: float


class PoolStatus(BaseModel):
    """Database connection pool status"""

    status: str
    pool_size: Optional[int] = None
    checked_in: Optional[int] = None
    checked_out: Optional[int] = None
    overflow: Optional[int] = None


class DetailedHealthResponse(BaseModel):
    """Response model for detailed health check endpoint"""

    status: str
    api_version: str
    timestamp: float
    database_pool: PoolStatus


@router.get("", response_model=HealthResponse)
async def health_check(settings: Settings = Depends(get_settings)):
    """
    Health check endpoint to verify API is running.

    This is a lightweight check suitable for load balancer health checks.
    """
    return {"status": "ok", "api_version": "v1", "timestamp": time.time()}


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    settings: Settings = Depends(get_settings),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Detailed health check endpoint including database pool status.

    This endpoint provides information about:
    - API status
    - Database connection pool utilization

    Use this for monitoring and debugging connection issues.
    """
    pool_status = repository_factory.get_pool_status()

    return {
        "status": "ok",
        "api_version": "v1",
        "timestamp": time.time(),
        "database_pool": PoolStatus(**pool_status),
    }
