"""
Topic API models for request and response validation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class TopicBase(BaseModel):
    """Base model for topic attributes."""

    title: str = Field(..., description="Topic title")
    course_id: int = Field(..., description="ID of the course this topic belongs to")
    week: int = Field(..., ge=1, description="Week number in the course for this topic")
    order: int = Field(..., ge=1, description="Order of this topic within the week")


class TopicCreate(TopicBase):
    """Model for creating a new topic."""

    pass


class TopicUpdate(BaseModel):
    """Model for updating topic details (all fields optional)."""

    title: Optional[str] = Field(None, description="Updated topic title")
    course_id: Optional[int] = Field(None, description="Updated ID of the course")
    week: Optional[int] = Field(None, ge=1, description="Updated week number")
    order: Optional[int] = Field(None, ge=1, description="Updated order in week")


class Topic(TopicBase):
    """Topic model matching the core model, including ID."""

    id: int = Field(..., description="Unique topic identifier")

    class Config:
        orm_mode = True  # Alias for from_attributes = True


class TopicList(BaseModel):
    """Paginated list of topics."""

    items: List[Topic] = Field(..., description="List of topics")
    total: int = Field(..., description="Total number of matching topics")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")


class TopicsGenerate(BaseModel):
    """Model for requesting topic generation for a course."""

    course_id: int = Field(..., description="ID of the course for which to generate topics")
    freeform_prompt: Optional[str] = Field(
        None, description="Optional freeform text prompt for additional guidance."
    )
