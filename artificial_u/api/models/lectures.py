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
    audio_download_url: Optional[str] = Field(
        None, description="Presigned URL for downloading audio file (mobile-friendly)"
    )
    transcript_url: Optional[str] = Field(None, description="URL to transcript file if available")
    timeline_url: Optional[str] = Field(
        None,
        description="URL to forced-alignment timeline JSON for synchronized captions",
    )
    images_timeline_url: Optional[str] = Field(
        None,
        description="URL to image-slideshow timeline JSON for synced lecture images",
    )
    voice_id: Optional[int] = Field(None, description="ID of the voice used for this lecture")
    word_count: Optional[int] = Field(
        None, description="Approximate number of words in the lecture content"
    )
    duration: Optional[int] = Field(None, description="Audio duration in seconds")
    created_by: Optional[int] = Field(
        None, description="ID of the student who created this lecture"
    )
    created_with: Optional[str] = Field(None, description="AI model used to generate this lecture")
    created_at: Optional[datetime] = Field(None, description="Timestamp when lecture was created")
    updated_at: Optional[datetime] = Field(
        None, description="Timestamp when lecture was last updated"
    )


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
    timeline_url: Optional[str] = Field(None, description="Updated timeline JSON URL")
    images_timeline_url: Optional[str] = Field(None, description="Updated images timeline JSON URL")
    revision: Optional[int] = Field(None, description="Updated revision number")
    created_by: Optional[int] = Field(None, description="Updated student ID")
    created_with: Optional[str] = Field(None, description="Updated AI model name")
    word_count: Optional[int] = Field(None, description="Updated lecture word count")
    duration: Optional[int] = Field(None, description="Updated audio duration in seconds")


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


class AdminLectureListItem(BaseModel):
    """Compact lecture row for admin list views."""

    id: int = Field(..., description="Lecture ID")
    title: str = Field(..., description="Lecture title")
    course_id: int = Field(..., description="Course ID")
    course_code: Optional[str] = Field(None, description="Course code")
    topic_id: int = Field(..., description="Topic ID")
    voice_id: Optional[int] = Field(None, description="Voice ID")
    audio_url: Optional[str] = Field(None, description="Audio URL if available")
    timeline_url: Optional[str] = Field(None, description="Timeline URL if available")
    images_timeline_url: Optional[str] = Field(None, description="Image timeline URL if available")
    image_slots_done: Optional[int] = Field(
        None, description="Number of completed image timeline slots"
    )
    image_slots_total: Optional[int] = Field(
        None, description="Total number of image timeline slots"
    )
    image_slots_error: Optional[str] = Field(
        None, description="Error encountered while reading image timeline metadata"
    )


class AdminLectureListResponse(BaseModel):
    """Paginated compact admin lecture listing."""

    items: List[AdminLectureListItem] = Field(..., description="List of lecture rows")
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
