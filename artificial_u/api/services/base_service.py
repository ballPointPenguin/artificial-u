"""
Base service class providing standardized patterns for API services.
"""

import logging
from math import ceil
from typing import Any, Dict, Generic, List, NoReturn, Optional, Type, TypeVar

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
            HTTPException: Standardized HTTP error response
        """
        self.logger.error(f"Unexpected error during {operation}: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during {operation}",
        )

    def _convert_to_response_models(self, core_items: List[T], response_class: Type[R]) -> List[R]:
        """
        Convert core models to API response models.

        Args:
            core_items: List of core model instances
            response_class: The response model class

        Returns:
            List of response model instances
        """
        return [response_class.model_validate(item) for item in core_items]

    def _apply_filters(self, items: List[Any], filters: Dict[str, Any]) -> List[Any]:
        """
        Apply filters to a list of items.

        Args:
            items: List of items to filter
            filters: Dictionary of filter criteria

        Returns:
            Filtered list of items
        """
        if not filters:
            return items

        filtered_items = items

        for key, value in filters.items():
            if value is not None:
                if isinstance(value, str):
                    # Case-insensitive string matching
                    filtered_items = [
                        item
                        for item in filtered_items
                        if hasattr(item, key)
                        and value.lower() in str(getattr(item, key, "")).lower()
                    ]
                else:
                    # Exact value matching
                    filtered_items = [
                        item
                        for item in filtered_items
                        if hasattr(item, key) and getattr(item, key) == value
                    ]

        return filtered_items

    def _paginate_items(self, items: List[Any], page: int, size: int) -> List[Any]:
        """
        Apply pagination to a list of items.

        Args:
            items: List of items to paginate
            page: Page number (1-indexed)
            size: Items per page

        Returns:
            Paginated list of items
        """
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        return items[start_idx:end_idx]

    def _standard_list_operation(
        self,
        core_service_method: str,
        response_class: Type[R],
        list_response_class: Type[L],
        page: int = 1,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> L:
        """
        Standardized list operation template.

        This method provides a consistent pattern for list operations across all services.

        Args:
            core_service_method: Name of the core service method to call
            response_class: The response model class for individual items
            list_response_class: The list response model class
            page: Page number (1-indexed)
            size: Items per page
            filters: Optional filters to apply
            **kwargs: Additional arguments to pass to the core service method

        Returns:
            List response model instance

        Raises:
            HTTPException: If the operation fails
        """
        try:
            # Get core service method
            core_method = getattr(self.core_service, core_service_method)

            # Get all items from core service
            all_items = core_method(**kwargs)

            # Apply filters if provided
            if filters:
                all_items = self._apply_filters(all_items, filters)

            # Count total before pagination
            total = len(all_items)

            # Apply pagination
            paginated_items = self._paginate_items(all_items, page, size)

            # Convert to response models
            response_items = self._convert_to_response_models(paginated_items, response_class)

            # Create and return list response
            return self._create_list_response(
                response_items, total, page, size, list_response_class
            )

        except Exception as e:
            self._handle_general_error(f"list operation ({core_service_method})", e)
