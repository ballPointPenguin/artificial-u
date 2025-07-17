"""
API models for Course resources.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Base Course model with common fields
class CourseBase(BaseModel):
    """Base Course model with common fields."""

    code: str = Field(..., description="Course code (e.g., CS101, MATH201)")
    title: str = Field(..., description="Course title")
    department_id: int = Field(..., description="ID of the department offering the course")
    level: str = Field(..., description="Course level (e.g., Undergraduate, Graduate)")
    credits: int = Field(default=3, ge=0, description="Number of credit hours")
    professor_id: int = Field(..., description="ID of the professor teaching the course")
    description: str = Field(..., description="Course description and overview")
    lectures_per_week: int = Field(default=14, description="Number of lectures per week")
    total_weeks: int = Field(default=1, description="Total number of weeks in the course")
    topics: Optional[List[Dict[str, Any]]] = Field(None, description="List of course topics")


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
    credits: Optional[int] = Field(default=None, ge=0, description="Updated number of credits")
    professor_id: Optional[int] = Field(None, description="Updated professor ID")
    description: Optional[str] = Field(None, description="Updated course description")
    lectures_per_week: Optional[int] = Field(None, description="Updated lectures per week")
    total_weeks: Optional[int] = Field(None, description="Updated total weeks")


# Course response model
class CourseResponse(CourseBase):
    """Model for course responses."""

    id: int = Field(..., description="Unique course identifier")

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


# Professor brief info model for course's professor endpoint
class ProfessorBrief(BaseModel):
    """Brief professor information for course's professor endpoint."""

    id: int = Field(..., description="Unique professor identifier")
    name: str = Field(..., description="Professor's name")
    title: str = Field(..., description="Academic title")
    department_id: int = Field(..., description="Department ID")
    specialization: str = Field(..., description="Area of specialization")


# Lecture brief info model for course's lectures endpoint
class LectureBrief(BaseModel):
    """Brief lecture information for course's lectures endpoint."""

    id: int = Field(..., description="Unique lecture identifier")
    title: str = Field(..., description="Lecture title")
    week_number: int = Field(..., description="Week number in the course")
    order_in_week: int = Field(..., description="Order within the week")
    description: str = Field(..., description="Lecture description")


# Course's lectures response model
class CourseLecturesResponse(BaseModel):
    """Model for course's lectures response."""

    course_id: int = Field(..., description="ID of the course")
    lectures: List[LectureBrief] = Field(..., description="List of lectures in the course")
    total: int = Field(..., description="Total number of lectures")


# Course's department brief info model
class DepartmentBrief(BaseModel):
    """Brief department information for course's department endpoint."""

    id: int = Field(..., description="Unique department identifier")
    name: str = Field(..., description="Department name")
    code: str = Field(..., description="Department code")
    faculty: str = Field(..., description="Faculty name")


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
    credits: Optional[int] = Field(default=None, ge=0, description="Generated number of credits")
    professor_id: Optional[int] = Field(None, description="Generated professor ID")
    description: Optional[str] = Field(None, description="Generated course description")
    lectures_per_week: Optional[int] = Field(None, description="Generated lectures per week")
    total_weeks: Optional[int] = Field(None, description="Generated total weeks")
    topics: Optional[List[Dict[str, Any]]] = Field(None, description="Generated course topics")

    class Config:
        from_attributes = True
