"""
API models for Faculty resources.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# Faculty response model
class FacultyResponse(BaseModel):
    """Model for faculty responses."""

    id: int = Field(..., description="Unique faculty identifier")
    name: str = Field(..., description="Faculty name")
    description: Optional[str] = Field(None, description="Faculty description")

    class Config:
        from_attributes = True


# Faculties list response model
class FacultiesListResponse(BaseModel):
    """Model for list of faculties response."""

    items: List[FacultyResponse] = Field(..., description="List of faculties")
    total: int = Field(..., description="Total number of faculties")
