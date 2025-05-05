"""
API models for Department resources.
"""

from typing import Any, Dict, List, Optional

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


# Department generation model
class DepartmentGenerate(BaseModel):
    """Model for generating a new department."""

    name: Optional[str] = Field(None, description="Department name")
    code: Optional[str] = Field(None, description="Department code")
    faculty: Optional[str] = Field(None, description="Faculty name")
    description: Optional[str] = Field(None, description="Department description")
    freeform_prompt: Optional[str] = Field(
        None, description="Optional freeform text prompt for additional guidance"
    )

    def get_attributes(self) -> Dict[str, Any]:
        """
        Get combined attributes from both direct fields and nested partial_attributes.
        Direct fields take precedence over nested ones.
        """
        # Start with nested attributes if they exist
        attrs = self.partial_attributes or {}

        # Add direct fields if they have values
        direct_fields = {
            "name": self.name,
            "code": self.code,
            "faculty": self.faculty,
            "description": self.description,
        }
        attrs.update({k: v for k, v in direct_fields.items() if v is not None})

        return attrs


# Department response model
class DepartmentResponse(DepartmentBase):
    """Model for department responses."""

    id: Optional[int] = None

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
