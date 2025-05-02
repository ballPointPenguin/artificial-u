"""
Error handling utility functions for the API.
Provides helpers for common error handling patterns and exception creation.
"""

from typing import Any, Dict, List, Optional, Type

from pydantic import ValidationError as PydanticValidationError

from artificial_u.api.models.error_codes import ErrorCode
from artificial_u.api.utils.exceptions import (
    APIError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    UnauthorizedError,
    ValidationError,
)


def raise_not_found(
    resource_type: str,
    resource_id: Optional[Any] = None,
    error_code: Optional[str] = None,
    details: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Raise a not found exception with appropriate details

    Args:
        resource_type: Type of resource (e.g. "professor", "course")
        resource_id: Identifier of the resource
        error_code: Optional specific error code
        details: Optional additional error details

    Raises:
        NotFoundError: Always raises this exception
    """
    if resource_id is not None:
        message = f"{resource_type.capitalize()} with ID {resource_id} not found"
    else:
        message = f"{resource_type.capitalize()} not found"

    # Use resource-specific error code if available
    if error_code is None:
        error_code = f"{resource_type.upper()}_NOT_FOUND"
        # Fall back to generic NOT_FOUND if specific code doesn't exist
        if error_code not in [e.value for e in ErrorCode]:
            error_code = ErrorCode.NOT_FOUND

    raise NotFoundError(message=message, error_code=error_code, details=details)


def raise_validation_error(
    message: str = "Validation error",
    error_code: str = ErrorCode.VALIDATION_ERROR,
    details: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Raise a validation error with appropriate details

    Args:
        message: Error message
        error_code: Specific error code
        details: Additional error details

    Raises:
        ValidationError: Always raises this exception
    """
    raise ValidationError(message=message, error_code=error_code, details=details)


def handle_pydantic_validation_error(exc: PydanticValidationError) -> ValidationError:
    """
    Convert a Pydantic validation error to our custom ValidationError

    Args:
        exc: The Pydantic validation error

    Returns:
        A ValidationError exception that can be raised
    """
    details = []
    for error in exc.errors():
        details.append(
            {
                "loc": error.get("loc", []),
                "msg": error.get("msg", ""),
                "type": error.get("type", ""),
            }
        )

    return ValidationError(
        message="Data validation error",
        error_code=ErrorCode.VALIDATION_ERROR,
        details=details,
    )


def get_exception_by_status_code(status_code: int) -> Type[APIError]:
    """
    Get the appropriate exception class for a status code

    Args:
        status_code: HTTP status code

    Returns:
        The exception class matching the status code
    """
    error_classes = {
        400: BadRequestError,
        401: UnauthorizedError,
        403: ForbiddenError,
        404: NotFoundError,
        409: ConflictError,
        422: ValidationError,
        500: ServerError,
    }

    return error_classes.get(status_code, APIError)
