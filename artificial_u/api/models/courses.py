"""
API models for Course resources.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# Base Course model with common fields
class CourseBase(BaseModel):
    """Base Course model with common fields."""

    code: str = Field(..., description="Course code (e.g., CS101, MATH201)")
    title: str = Field(..., description="Course title")
    department_id: Optional[int] = Field(
        None, description="ID of the department offering the course (optional for smart selection)"
    )
    level: str = Field(..., description="Course level (e.g., Undergraduate, Graduate)")
    credits: int = Field(
        default=3,
        ge=1,
        le=100,
        description="Number of credit hours (1-100)",
    )
    professor_id: Optional[int] = Field(
        None, description="ID of the professor teaching the course (optional for smart selection)"
    )
    description: str = Field(..., description="Course description and overview")
    lectures_per_week: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Number of lectures per week (1-5)",
    )
    total_weeks: int = Field(
        default=12,
        ge=1,
        le=50,
        description="Total number of weeks in the course (1-50)",
    )
    topics: Optional[List[Dict[str, Any]]] = Field(None, description="List of course topics")
    status: Literal["hidden", "published"] = Field(
        default="hidden", description="Course visibility status"
    )
    # Attribution (not required for create)
    created_by: Optional[int] = Field(None, description="Student ID who created the course")
    created_with: Optional[str] = Field(None, description="Name of LLM used, if any")
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Course creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Course last update timestamp")


# Course creation model
class CourseCreate(CourseBase):
    """Model for creating a new course."""

    pass


# Course update model
class CourseUpdate(BaseModel):
    """Model for updating an existing course. All fields are optional."""

    code: Optional[str] = Field(None, description="Updated course code")
    title: Optional[str] = Field(None, description="Updated course title")
    department_id: Optional[int] = Field(None, description="Updated department ID")
    level: Optional[str] = Field(None, description="Updated course level")
    credits: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Updated number of credits (1-100)",
    )
    professor_id: Optional[int] = Field(None, description="Updated professor ID")
    description: Optional[str] = Field(None, description="Updated course description")
    lectures_per_week: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Updated lectures per week (1-5)",
    )
    total_weeks: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Updated total weeks (1-50)",
    )
    status: Optional[Literal["hidden", "published"]] = Field(
        None, description="Updated course visibility status"
    )


# Student brief info model for course responses
class StudentBrief(BaseModel):
    """Brief student information for course responses."""

    id: int = Field(..., description="Student ID")
    name: str = Field(..., description="Student name")
    email: Optional[str] = Field(None, description="Student email")


# Professor brief info model for course responses
class ProfessorBrief(BaseModel):
    """Brief professor information for course responses."""

    id: int = Field(..., description="Professor ID")
    name: str = Field(..., description="Professor name")
    title: str = Field(..., description="Academic title")
    department_id: int = Field(..., description="Department ID")
    specialization: str = Field(..., description="Area of specialization")
    image_url: Optional[str] = Field(None, description="URL of the professor's image")


# Department brief info model for course responses
class DepartmentBrief(BaseModel):
    """Brief department information for course responses."""

    id: int = Field(..., description="Department ID")
    name: str = Field(..., description="Department name")
    code: str = Field(..., description="Department code")
    faculty_id: Optional[int] = Field(None, description="Faculty ID")
    faculty_name: Optional[str] = Field(None, description="Faculty name")


# Course response model
class CourseResponse(CourseBase):
    """Model for course responses."""

    id: int = Field(..., description="Unique course identifier")
    # Override to make these required in responses (should be populated after creation)
    department_id: int = Field(..., description="ID of the department offering the course")
    professor_id: int = Field(..., description="ID of the professor teaching the course")
    created_by: Optional[int] = Field(None, description="Student ID who created the course")
    created_with: Optional[str] = Field(None, description="Name of LLM used, if any")
    student: Optional[StudentBrief] = Field(None, description="Student who created the course")
    professor: Optional[ProfessorBrief] = Field(None, description="Professor teaching the course")
    department: Optional[DepartmentBrief] = Field(
        None, description="Department offering the course"
    )
    # Audio/Topic Counts
    lectures_with_audio_count: Optional[int] = Field(
        0, description="Number of lectures with audio files"
    )
    topics_count: Optional[int] = Field(0, description="Total number of topics in the course")

    class Config:
        from_attributes = True


# Courses list response model
class CoursesListResponse(BaseModel):
    """Model for list of courses response."""

    items: List[CourseResponse] = Field(..., description="List of courses")
    total: int = Field(..., description="Total number of matching courses")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


# Lecture brief info model for course's lectures endpoint
class LectureBrief(BaseModel):
    """Brief lecture information for course's lectures endpoint."""

    id: int = Field(..., description="Unique lecture identifier")
    course_id: int = Field(..., description="Course ID")
    topic_id: int = Field(..., description="Topic ID")
    title: str = Field(..., description="Lecture title")
    summary: Optional[str] = Field(None, description="Lecture summary")
    audio_url: Optional[str] = Field(None, description="Lecture audio URL if available")
    audio_download_url: Optional[str] = Field(
        None, description="Presigned URL for downloading audio file (mobile-friendly)"
    )
    transcript_url: Optional[str] = Field(None, description="Lecture transcript URL if available")


# Course's lectures response model
class CourseLecturesResponse(BaseModel):
    """Model for course's lectures response."""

    course_id: int = Field(..., description="ID of the course")
    lectures: List[LectureBrief] = Field(..., description="List of lectures in the course")
    total: int = Field(..., description="Total number of lectures")


# Model for generating a course
class CourseGenerate(BaseModel):
    """Model for requesting course generation."""

    partial_attributes: Optional[Dict[str, Any]] = Field(
        None, description="Optional dictionary of known attributes to guide generation."
    )
    freeform_prompt: Optional[str] = Field(
        None, description="Optional freeform text prompt for additional guidance."
    )


# Model for the response of a generated course, allowing partial data
class GeneratedCourseData(BaseModel):
    """
    Model for the response of a generated course.
    Allows for partial data, making most fields from CourseBase optional.
    Includes an ID, typically a placeholder for generated (non-persisted) courses.
    """

    id: Optional[int] = Field(
        default=-1,
        description="Placeholder ID for generated course, typically -1 if not persisted.",
    )
    code: Optional[str] = Field(None, description="Generated course code")
    title: Optional[str] = Field(None, description="Generated course title")
    department_id: Optional[int] = Field(None, description="Generated department ID")
    level: Optional[str] = Field(None, description="Generated course level")
    credits: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Generated number of credits (1-100)",
    )
    professor_id: Optional[int] = Field(None, description="Generated professor ID")
    description: Optional[str] = Field(None, description="Generated course description")
    lectures_per_week: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Generated lectures per week (1-5)",
    )
    total_weeks: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Generated total weeks (1-50)",
    )
    topics: Optional[List[Dict[str, Any]]] = Field(None, description="Generated course topics")
    created_with: Optional[str] = Field(None, description="Name of LLM used for generation")

    class Config:
        from_attributes = True
