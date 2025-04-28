"""
API models for Course resources.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# Base Course model with common fields
class CourseBase(BaseModel):
    """Base Course model with common fields."""

    code: str
    title: str
    department_id: int
    level: str  # Undergraduate, Graduate, etc.
    credits: int = Field(default=3, ge=0)
    professor_id: int
    description: str
    lectures_per_week: int = Field(default=2, gt=0)
    total_weeks: int = Field(default=14, gt=0)
    syllabus: Optional[str] = None


# Course creation model
class CourseCreate(CourseBase):
    """Model for creating a new course."""

    pass


# Course update model
class CourseUpdate(CourseBase):
    """Model for updating an existing course."""

    pass


# Course response model
class CourseResponse(CourseBase):
    """Model for course responses."""

    id: int

    class Config:
        from_attributes = True


# Courses list response model
class CoursesListResponse(BaseModel):
    """Model for list of courses response."""

    items: List[CourseResponse]
    total: int
    page: int
    size: int
    pages: int


# Professor brief info model for course's professor endpoint
class ProfessorBrief(BaseModel):
    """Brief professor information for course's professor endpoint."""

    id: int
    name: str
    title: str
    department_id: int
    specialization: str


# Lecture brief info model for course's lectures endpoint
class LectureBrief(BaseModel):
    """Brief lecture information for course's lectures endpoint."""

    id: int
    title: str
    week_number: int
    order_in_week: int
    description: str
    audio_url: Optional[str] = None


# Course's lectures response model
class CourseLecturesResponse(BaseModel):
    """Model for course's lectures response."""

    course_id: int
    lectures: List[LectureBrief]
    total: int


# Course's department brief info model
class DepartmentBrief(BaseModel):
    """Brief department information for course's department endpoint."""

    id: int
    name: str
    code: str
    faculty: str
