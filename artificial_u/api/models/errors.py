"""
Error response models for the API.
Provides a consistent structure for all API error responses.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error information for field-level validation errors"""

    loc: List[str] = Field(
        default_factory=list, description="Location of the error (e.g. field name)"
    )
    msg: str = Field(description="Error message explaining the error")
    type: str = Field(description="Error type identifier")


class ErrorResponse(BaseModel):
    """Standardized error response model for API endpoints"""

    status_code: int = Field(description="HTTP status code")
    error_code: str = Field(description="Application-specific error code")
    message: str = Field(description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Additional error details, usually for validation errors",
    )

    class Config:
        """Pydantic model configuration"""

        schema_extra = {
            "example": {
                "status_code": 400,
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": [
                    {
                        "loc": ["body", "name"],
                        "msg": "Field required",
                        "type": "value_error.missing",
                    }
                ],
            }
        }
