"""
API models for Professor resources.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


# Base Professor model with common fields
class ProfessorBase(BaseModel):
    """Base Professor model with common fields."""

    name: str
    title: str
    department: str
    specialization: str
    background: str
    personality: str
    teaching_style: str
    gender: Optional[str] = None
    accent: Optional[str] = None
    description: Optional[str] = None
    age: Optional[int] = None
    voice_settings: Dict[str, Any] = Field(default_factory=dict)
    image_path: Optional[str] = None


# Professor creation model
class ProfessorCreate(ProfessorBase):
    """Model for creating a new professor."""

    pass


# Professor update model
class ProfessorUpdate(ProfessorBase):
    """Model for updating an existing professor."""

    pass


# Professor response model
class ProfessorResponse(ProfessorBase):
    """Model for professor responses."""

    id: str

    class Config:
        from_attributes = True


# Professors list response model
class ProfessorsListResponse(BaseModel):
    """Model for list of professors response."""

    items: List[ProfessorResponse]
    total: int
    page: int
    size: int
    pages: int


# Course brief info model for professor's courses endpoint
class CourseBrief(BaseModel):
    """Brief course information for professor's courses endpoint."""

    id: str
    code: str
    title: str
    department: str
    level: str
    credits: int


# Lecture brief info model for professor's lectures endpoint
class LectureBrief(BaseModel):
    """Brief lecture information for professor's lectures endpoint."""

    id: str
    title: str
    course_id: str
    week_number: int
    order_in_week: int
    description: str


# Professor's courses response model
class ProfessorCoursesResponse(BaseModel):
    """Model for professor's courses response."""

    professor_id: str
    courses: List[CourseBrief]
    total: int


# Professor's lectures response model
class ProfessorLecturesResponse(BaseModel):
    """Model for professor's lectures response."""

    professor_id: str
    lectures: List[LectureBrief]
    total: int
