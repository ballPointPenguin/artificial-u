"""
Lecture API models for request and response validation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class LectureCreate(BaseModel):
    """Model for creating a new lecture"""

    title: str = Field(..., description="Lecture title")
    course_id: int = Field(..., description="ID of the course this lecture belongs to")
    week_number: int = Field(..., ge=1, description="Week number in the course")
    order_in_week: int = Field(1, ge=1, description="Order of this lecture within the week")
    description: str = Field(..., description="Brief description of the lecture content")
    content: str = Field(..., description="Full lecture content text")
    audio_url: Optional[str] = Field(None, description="URL to audio file if available")


class LectureUpdate(BaseModel):
    """Model for updating lecture details (all fields optional)"""

    title: Optional[str] = Field(None, description="Updated lecture title")
    description: Optional[str] = Field(None, description="Updated lecture description")
    content: Optional[str] = Field(None, description="Updated lecture content text")
    week_number: Optional[int] = Field(None, ge=1, description="Updated week number")
    order_in_week: Optional[int] = Field(None, ge=1, description="Updated order in week")
    audio_url: Optional[str] = Field(None, description="Updated audio URL")


class Lecture(BaseModel):
    """Lecture model matching the core model"""

    id: int = Field(..., description="Unique lecture identifier")
    title: str = Field(..., description="Lecture title")
    course_id: int = Field(..., description="ID of the course this lecture belongs to")
    week_number: int = Field(..., description="Week number in the course")
    order_in_week: int = Field(..., description="Order of this lecture within the week")
    description: str = Field(..., description="Brief description of the lecture content")
    content: str = Field(..., description="Full lecture content text")
    audio_url: Optional[str] = Field(None, description="URL to audio file if available")


class LectureList(BaseModel):
    """Paginated list of lectures"""

    items: List[Lecture] = Field(..., description="List of lectures")
    total: int = Field(..., description="Total number of matching lectures")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
