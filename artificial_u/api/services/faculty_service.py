"""
Faculty service for handling business logic related to faculties.
"""

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

    def list_faculties(self) -> FacultiesListResponse:
        """
        Get a list of all faculties.

        Returns:
            FacultiesListResponse with all faculties
        """
        try:
            # Get all faculties from repository
            faculties = self.repository_factory.faculty.list()

            # Convert to response models
            faculty_responses = [
                FacultyResponse(
                    id=f.id,
                    name=f.name,
                    description=f.description,
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
