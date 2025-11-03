"""
Student API models for request and response validation.
"""

from typing import Optional

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
