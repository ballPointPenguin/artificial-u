"""
API models for Department resources.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


# Base Department model with common fields
class DepartmentBase(BaseModel):
    """Base Department model with common fields."""

    name: str
    code: str
    faculty: Optional[str] = None
    description: Optional[str] = None


# Department creation model
class DepartmentCreate(DepartmentBase):
    """Model for creating a new department."""

    pass


# Department update model
class DepartmentUpdate(DepartmentBase):
    """Model for updating an existing department."""

    pass


# Department response model
class DepartmentResponse(DepartmentBase):
    """Model for department responses."""

    id: int

    class Config:
        from_attributes = True


# Departments list response model
class DepartmentsListResponse(BaseModel):
    """Model for list of departments response."""

    items: List[DepartmentResponse]
    total: int
    page: int
    size: int
    pages: int


# Professor brief info model for department's professors endpoint
class ProfessorBrief(BaseModel):
    """Brief professor information for department's professors endpoint."""

    id: int
    name: str
    title: str
    specialization: str


# Course brief info model for department's courses endpoint
class CourseBrief(BaseModel):
    """Brief course information for department's courses endpoint."""

    id: int
    code: str
    title: str
    level: str
    credits: int
    professor_id: Optional[int] = None


# Department's professors response model
class DepartmentProfessorsResponse(BaseModel):
    """Model for department's professors response."""

    department_id: int
    professors: List[ProfessorBrief]
    total: int


# Department's courses response model
class DepartmentCoursesResponse(BaseModel):
    """Model for department's courses response."""

    department_id: int
    courses: List[CourseBrief]
    total: int
