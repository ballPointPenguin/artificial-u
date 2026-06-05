"""
Faculty service for handling business logic related to faculties.
"""

from typing import Optional

from artificial_u.api.models.faculties import FacultiesListResponse, FacultyResponse
from artificial_u.models.repositories import RepositoryFactory


class FacultyApiService:
    """Service for faculty-related operations."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        logger=None,
    ):
        """
        Initialize with required services.

        Args:
            repository_factory: Repository factory instance
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.logger = logger

    def list_faculties(self, language: Optional[str] = None) -> FacultiesListResponse:
        """
        Get a list of faculties, optionally filtered by language.

        Returns:
            FacultiesListResponse with matching faculties
        """
        try:
            # Get faculties from repository, filtered by language if provided
            faculties = self.repository_factory.faculty.list(language=language)

            # Convert to response models
            faculty_responses = [
                FacultyResponse(
                    id=f.id,
                    name=f.name,
                    description=f.description,
                    language=f.language,
                )
                for f in faculties
            ]

            return FacultiesListResponse(
                items=faculty_responses,
                total=len(faculty_responses),
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing faculties: {e}", exc_info=True)
            raise
