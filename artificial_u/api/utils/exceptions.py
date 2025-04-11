"""
Custom exception classes for the API.
Provides a hierarchy of exceptions for handling different types of API errors.
"""

from typing import List, Dict, Any, Optional
from fastapi import status


class APIError(Exception):
    """Base exception class for API errors"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or []
        super().__init__(message)


class BadRequestError(APIError):
    """Exception for invalid request data"""

    def __init__(
        self,
        message: str = "Bad request",
        error_code: str = "BAD_REQUEST",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            details=details,
        )


class NotFoundError(APIError):
    """Exception for resource not found errors"""

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code,
            details=details,
        )


class ValidationError(APIError):
    """Exception for validation errors"""

    def __init__(
        self,
        message: str = "Validation error",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            details=details,
        )


class UnauthorizedError(APIError):
    """Exception for authentication errors"""

    def __init__(
        self,
        message: str = "Unauthorized",
        error_code: str = "UNAUTHORIZED",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            details=details,
        )


class ForbiddenError(APIError):
    """Exception for permission errors"""

    def __init__(
        self,
        message: str = "Forbidden",
        error_code: str = "FORBIDDEN",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            details=details,
        )


class ConflictError(APIError):
    """Exception for resource conflict errors"""

    def __init__(
        self,
        message: str = "Resource conflict",
        error_code: str = "CONFLICT",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            details=details,
        )


class ServerError(APIError):
    """Exception for server errors"""

    def __init__(
        self,
        message: str = "Internal server error",
        error_code: str = "SERVER_ERROR",
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code,
            details=details,
        )
