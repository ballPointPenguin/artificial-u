"""
Standardized error codes for the API.

This module defines the application-specific error codes used across the API.
Each error code has a unique identifier and a description to help diagnose issues.
"""

from enum import Enum
from typing import Dict


class ErrorCode(str, Enum):
    """Enumeration of all error codes used in the API"""

    # General errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"

    # Resource-specific errors
    PROFESSOR_NOT_FOUND = "PROFESSOR_NOT_FOUND"
    COURSE_NOT_FOUND = "COURSE_NOT_FOUND"
    DEPARTMENT_NOT_FOUND = "DEPARTMENT_NOT_FOUND"

    # Data errors
    INVALID_DATA = "INVALID_DATA"
    DUPLICATE_ENTITY = "DUPLICATE_ENTITY"

    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"

    # External service errors
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"

    # Rate limiting
    RATE_LIMITED = "RATE_LIMITED"


# Detailed descriptions for each error code
ERROR_CODE_DESCRIPTIONS: Dict[str, str] = {
    ErrorCode.INTERNAL_ERROR: "An unexpected internal server error occurred.",
    ErrorCode.BAD_REQUEST: "The request was invalid or cannot be served.",
    ErrorCode.VALIDATION_ERROR: "The request data failed validation checks.",
    ErrorCode.NOT_FOUND: "The requested resource was not found.",
    ErrorCode.UNAUTHORIZED: "Authentication is required to access this resource.",
    ErrorCode.FORBIDDEN: "You don't have permission to access this resource.",
    ErrorCode.CONFLICT: "The request conflicts with the current state of the resource.",
    ErrorCode.PROFESSOR_NOT_FOUND: "The specified professor does not exist.",
    ErrorCode.COURSE_NOT_FOUND: "The specified course does not exist.",
    ErrorCode.DEPARTMENT_NOT_FOUND: "The specified department does not exist.",
    ErrorCode.INVALID_DATA: "The provided data is invalid or malformed.",
    ErrorCode.DUPLICATE_ENTITY: "An entity with the same unique identifiers already exists.",
    ErrorCode.INVALID_CREDENTIALS: "The provided credentials are invalid.",
    ErrorCode.TOKEN_EXPIRED: "The authentication token has expired.",
    ErrorCode.INVALID_TOKEN: "The authentication token is invalid or malformed.",
    ErrorCode.SERVICE_UNAVAILABLE: "A required service is currently unavailable.",
    ErrorCode.EXTERNAL_API_ERROR: "An error occurred while communicating with an external API.",
    ErrorCode.RATE_LIMITED: "You have exceeded the rate limit for this endpoint.",
}


def get_error_description(error_code: str) -> str:
    """
    Get the description for an error code

    Args:
        error_code: The error code to look up

    Returns:
        The description for the error code, or a generic message if not found
    """
    return ERROR_CODE_DESCRIPTIONS.get(error_code, "An error occurred with code: " + error_code)
