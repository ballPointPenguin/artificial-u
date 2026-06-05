"""
API models for Department resources.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Base Department model with common fields
class DepartmentBase(BaseModel):
    """Base Department model with common fields."""

    name: str = Field(..., description="Department name")
    code: str = Field(..., description="Department code (e.g., CS, MATH)")
    faculty_id: Optional[int] = Field(
        None, description="ID of the faculty this department belongs to"
    )
    description: Optional[str] = Field(None, description="Department description and overview")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'fr')")


# Department creation model
class DepartmentCreate(DepartmentBase):
    """Model for creating a new department."""

    pass


# Department update model
class DepartmentUpdate(DepartmentBase):
    """Model for updating an existing department."""

    pass


# Department generation model
class DepartmentGenerate(BaseModel):
    """Model for generating a new department."""

    partial_attributes: Optional[Dict[str, Any]] = Field(
        None, description="Optional dictionary of known attributes to guide generation."
    )
    freeform_prompt: Optional[str] = Field(
        None, description="Optional freeform text prompt for additional guidance."
    )
    department_id: Optional[int] = Field(
        None, description="ID of existing department being edited (for context)."
    )
    language: Optional[str] = Field(
        "en", description="Language code for generation context (e.g., 'en', 'fr')."
    )


# Department response model
class DepartmentResponse(DepartmentBase):
    """Model for department responses."""

    id: Optional[int] = Field(None, description="Unique department identifier")
    faculty_name: Optional[str] = Field(
        None, description="Faculty name (populated from faculty_id)"
    )

    class Config:
        from_attributes = True


# Departments list response model
class DepartmentsListResponse(BaseModel):
    """Model for list of departments response."""

    items: List[DepartmentResponse] = Field(..., description="List of departments")
    total: int = Field(..., description="Total number of matching departments")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


# Professor brief info model for department's professors endpoint
class ProfessorBrief(BaseModel):
    """Brief professor information for department's professors endpoint."""

    id: int = Field(..., description="Unique professor identifier")
    name: str = Field(..., description="Professor's name")
    title: str = Field(..., description="Academic title")
    specialization: str = Field(..., description="Area of specialization")
    image_url: Optional[str] = Field(None, description="URL of the professor's image")


# Course brief info model for department's courses endpoint
class CourseBrief(BaseModel):
    """Brief course information for department's courses endpoint."""

    id: int = Field(..., description="Unique course identifier")
    code: str = Field(..., description="Course code")
    title: str = Field(..., description="Course title")
    level: str = Field(..., description="Course level")
    professor_id: Optional[int] = Field(None, description="ID of the professor")


# Department's professors response model
class DepartmentProfessorsResponse(BaseModel):
    """Model for department's professors response."""

    department_id: int = Field(..., description="ID of the department")
    professors: List[ProfessorBrief] = Field(
        ..., description="List of professors in the department"
    )
    total: int = Field(..., description="Total number of professors")


# Department's courses response model
class DepartmentCoursesResponse(BaseModel):
    """Model for department's courses response."""

    department_id: int = Field(..., description="ID of the department")
    courses: List[CourseBrief] = Field(..., description="List of courses in the department")
    total: int = Field(..., description="Total number of courses")
