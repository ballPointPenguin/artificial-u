"""
Lecture API models for request and response validation.
"""

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


class Lecture(LectureBase):
    """Lecture model matching the core model, including ID."""

    id: int = Field(..., description="Unique lecture identifier")

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
