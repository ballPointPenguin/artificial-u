"""
API models for Professor resources.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Base Professor model with common fields
class ProfessorBase(BaseModel):
    """Base Professor model with common fields."""

    name: Optional[str] = Field(None, description="Professor's full name")
    title: Optional[str] = Field(
        None, description="Academic title (e.g., Professor, Associate Professor)"
    )
    department_id: Optional[int] = Field(
        None, description="ID of the department this professor belongs to"
    )
    specialization: Optional[str] = Field(None, description="Area of academic specialization")
    background: Optional[str] = Field(None, description="Academic and professional background")
    personality: Optional[str] = Field(None, description="Teaching personality and characteristics")
    teaching_style: Optional[str] = Field(
        None, description="Preferred teaching methodology and approach"
    )
    gender: Optional[str] = Field(None, description="Gender identity")
    accent: Optional[str] = Field(None, description="Regional or linguistic accent")
    description: Optional[str] = Field(None, description="General description of the professor")
    age: Optional[int] = Field(None, description="Age of the professor")
    image_url: Optional[str] = Field(None, description="URL to professor's profile image")
    voice_id: Optional[int] = Field(None, description="ID of the voice assigned to this professor")


# Professor creation model
class ProfessorCreate(ProfessorBase):
    """Model for creating a new professor."""

    pass


# Professor update model
class ProfessorUpdate(ProfessorBase):
    """Model for updating an existing professor."""

    pass


# Professor generation model
class ProfessorGenerate(BaseModel):
    """Model for generating a new professor profile based on partial attributes."""

    partial_attributes: Optional[Dict[str, Any]] = Field(
        None, description="Optional dictionary of known attributes to guide generation."
    )
    freeform_prompt: Optional[str] = Field(
        None, description="Optional freeform text prompt for additional guidance."
    )


# Professor response model
class ProfessorResponse(ProfessorBase):
    """Model for professor responses, including generated ones."""

    id: Optional[int] = Field(
        None, description="Unique professor identifier"
    )  # Make ID optional for generated responses

    class Config:
        from_attributes = True


# Professors list response model
class ProfessorsListResponse(BaseModel):
    """Model for list of professors response."""

    items: List[ProfessorResponse] = Field(..., description="List of professors")
    total: int = Field(..., description="Total number of matching professors")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


# Course brief info model for professor's courses endpoint
class CourseBrief(BaseModel):
    """Brief course information for professor's courses endpoint."""

    id: int = Field(..., description="Unique course identifier")
    code: str = Field(..., description="Course code")
    title: str = Field(..., description="Course title")
    department_id: Optional[int] = Field(None, description="ID of the department")
    level: str = Field(..., description="Course level (e.g., Undergraduate, Graduate)")
    credits: int = Field(..., description="Number of credits")


# Lecture brief info model for professor's lectures endpoint
class LectureBrief(BaseModel):
    """Brief lecture information for professor's lectures endpoint."""

    id: int = Field(..., description="Unique lecture identifier")
    course_id: int = Field(..., description="ID of the course this lecture belongs to")
    topic_id: int = Field(..., description="ID of the topic this lecture belongs to")
    title: str = Field(..., description="Lecture title")
    summary: Optional[str] = Field(None, description="Lecture summary")
    audio_url: Optional[str] = Field(None, description="Audio URL if generated for this lecture")


# Professor's courses response model
class ProfessorCoursesResponse(BaseModel):
    """Model for professor's courses response."""

    professor_id: int = Field(..., description="ID of the professor")
    courses: List[CourseBrief] = Field(..., description="List of courses taught by the professor")
    total: int = Field(..., description="Total number of courses")


# Professor's lectures response model
class ProfessorLecturesResponse(BaseModel):
    """Model for professor's lectures response."""

    professor_id: int = Field(..., description="ID of the professor")
    lectures: List[LectureBrief] = Field(..., description="List of lectures by the professor")
    total: int = Field(..., description="Total number of lectures")
