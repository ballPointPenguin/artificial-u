from fastapi import APIRouter, Depends
from pydantic import BaseModel

from artificial_u.api.config import Settings, get_settings

router = APIRouter(tags=["Root"])


class APIInfo(BaseModel):
    """Response model for API information"""

    name: str
    version: str
    description: str
    docs_url: str


@router.get("/", response_model=APIInfo)
async def index(settings: Settings = Depends(get_settings)):
    """
    Root endpoint that provides basic API information
    """
    return {
        "name": "Artificial University API",
        "version": "v1",
        "description": """
        API for Artificial University, managing audio generations and model interactions
        """,
        "docs_url": "/api/docs",
    }
