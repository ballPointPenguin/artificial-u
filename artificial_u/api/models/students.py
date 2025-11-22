"""
Student API models for request and response validation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class StudentResponse(BaseModel):
    """Student response model."""

    id: int = Field(..., description="Unique student identifier")
    name: str = Field(..., description="Student's name")
    email: Optional[str] = Field(None, description="Student's email address")
    auth0_sub: Optional[str] = Field(None, description="Auth0 subject identifier")
    role: str = Field(..., description="User role (viewer, creator, admin)")
    coins: int = Field(..., description="Available coins for generation operations")
    is_active: bool = Field(..., description="Whether the account is active")

    class Config:
        from_attributes = True


class StudentUpdate(BaseModel):
    """Model for updating student profile."""

    name: Optional[str] = Field(None, description="Updated student name")
    email: Optional[str] = Field(None, description="Updated email address")


class StudentsListResponse(BaseModel):
    """Paginated list of students."""

    items: List[StudentResponse] = Field(..., description="List of students")
    total: int = Field(..., description="Total number of matching students")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")


class StudentRoleUpdate(BaseModel):
    """Model for updating a student's role."""

    role: str = Field(..., description="New role (viewer, creator, admin)")


class StudentCoinsAdd(BaseModel):
    """Model for adjusting coins on a student's account."""

    amount: int = Field(
        ...,
        ne=0,
        description="Coin adjustment amount. Use positive values to add coins and negative values to remove coins.",
    )
