"""
Base service class providing standardized patterns for API services.
"""

import logging
from math import ceil
from typing import Generic, List, NoReturn, Optional, Type, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel

# Type variables for generic base service
T = TypeVar("T", bound=BaseModel)  # Core model type
R = TypeVar("R", bound=BaseModel)  # Response model type
L = TypeVar("L", bound=BaseModel)  # List response model type


class BaseApiService(Generic[T, R, L]):
    """
    Base class for API services providing standardized list operations.

    Generic types:
    - T: Core model type (e.g., CoreLecture, CoreProfessor)
    - R: Response model type (e.g., Lecture, Professor)
    - L: List response model type (e.g., LectureListResponse, ProfessorsListResponse)
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def _calculate_pages(self, total: int, size: int) -> int:
        """
        Standardized page calculation.

        Args:
            total: Total number of items
            size: Items per page

        Returns:
            Total number of pages
        """
        return ceil(total / size) if total > 0 else 1

    def _create_list_response(
        self, items: List[R], total: int, page: int, size: int, response_class: Type[L]
    ) -> L:
        """
        Create a standardized list response.

        Args:
            items: List of response models
            total: Total number of items
            page: Current page number
            size: Items per page
            response_class: The list response model class

        Returns:
            List response model instance
        """
        pages = self._calculate_pages(total, size)
        return response_class(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def _handle_database_error(self, operation: str, error: Exception) -> NoReturn:
        """
        Standardized database error handling.

        Args:
            operation: Description of the operation that failed
            error: The database error that occurred

        Raises:
            HTTPException: Standardized HTTP error response
        """
        self.logger.error(f"Database error during {operation}: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during {operation}: {error}",
        )

    def _handle_general_error(self, operation: str, error: Exception) -> NoReturn:
        """
        Standardized general error handling.

        Args:
            operation: Description of the operation that failed
            error: The error that occurred

        Raises:
            HTTPException: Standardized HTTP error response. An HTTPException raised
                inside the operation (e.g. a 403 from an ownership check) is re-raised as is.
        """
        if isinstance(error, HTTPException):
            raise error
        self.logger.error(f"Unexpected error during {operation}: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during {operation}",
        )
