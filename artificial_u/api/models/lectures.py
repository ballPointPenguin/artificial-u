"""
Lecture API models for request and response validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LectureBase(BaseModel):
    """Base Lecture model with common fields."""

    course_id: int = Field(..., description="ID of the course this lecture belongs to")
    topic_id: int = Field(..., description="ID of the topic this lecture is associated with")
    revision: Optional[int] = Field(None, description="Revision number of the lecture content")
    content: str = Field(..., description="Full lecture content text")
    summary: Optional[str] = Field(None, description="Brief summary of the lecture content")
    title: str = Field(..., description="Title of the lecture")
    audio_url: Optional[str] = Field(None, description="URL to audio file if available")
    transcript_url: Optional[str] = Field(None, description="URL to transcript file if available")
    created_by: Optional[int] = Field(
        None, description="ID of the student who created this lecture"
    )
    created_with: Optional[str] = Field(None, description="AI model used to generate this lecture")
    created_at: Optional[datetime] = Field(None, description="Timestamp when lecture was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when lecture was last updated")


class LectureCreate(LectureBase):
    """Model for creating a new lecture."""

    pass


class LectureUpdate(BaseModel):
    """Model for updating lecture details (all fields optional)."""

    course_id: Optional[int] = Field(
        None, description="Updated ID of the course this lecture belongs to"
    )
    topic_id: Optional[int] = Field(
        None, description="Updated ID of the topic this lecture is associated with"
    )
    content: Optional[str] = Field(None, description="Updated lecture content text")
    summary: Optional[str] = Field(None, description="Updated summary of the lecture content")
    title: Optional[str] = Field(None, description="Updated title of the lecture")
    audio_url: Optional[str] = Field(None, description="Updated audio URL")
    transcript_url: Optional[str] = Field(None, description="Updated transcript URL")
    revision: Optional[int] = Field(None, description="Updated revision number")
    created_by: Optional[int] = Field(None, description="Updated student ID")
    created_with: Optional[str] = Field(None, description="Updated AI model name")


# Student brief info model for lecture responses
class StudentBrief(BaseModel):
    """Brief student information for lecture responses."""

    id: int = Field(..., description="Student ID")
    name: str = Field(..., description="Student name")
    email: Optional[str] = Field(None, description="Student email")


class Lecture(LectureBase):
    """Lecture model matching the core model, including ID."""

    id: int = Field(..., description="Unique lecture identifier")
    student: Optional[StudentBrief] = Field(None, description="Student who created the lecture")

    class Config:
        from_attributes = True


class LectureListResponse(BaseModel):
    """Paginated list of lectures."""

    items: List[Lecture] = Field(..., description="List of lectures")
    total: int = Field(..., description="Total number of matching lectures")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


class LectureGenerate(BaseModel):
    """Model for requesting lecture generation."""

    partial_attributes: Optional[Dict[str, Any]] = Field(
        None, description="Optional dictionary of known attributes to guide generation."
    )
    freeform_prompt: Optional[str] = Field(
        None, description="Optional freeform text prompt for additional guidance."
    )
