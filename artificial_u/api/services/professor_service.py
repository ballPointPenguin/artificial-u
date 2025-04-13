"""
Professor service for handling business logic related to professors.
"""

from math import ceil
from typing import Optional

from artificial_u.api.models.professors import (
    CourseBrief,
    LectureBrief,
    ProfessorCoursesResponse,
    ProfessorCreate,
    ProfessorLecturesResponse,
    ProfessorResponse,
    ProfessorsListResponse,
    ProfessorUpdate,
)
from artificial_u.services.professor_service import (
    ProfessorService as CoreProfessorService,
)
from artificial_u.utils.exceptions import DatabaseError, ProfessorNotFoundError


class ProfessorService:
    """API Service for professor-related operations."""

    def __init__(self, repository, core_professor_service=None):
        """
        Initialize with database repository and core professor service.

        Args:
            repository: Database repository factory
            core_professor_service: Core professor service (will be created if not provided)
        """
        self.repository = repository

        # Set up the core professor service if not provided
        self.core_service = core_professor_service
        if not self.core_service:
            self.core_service = CoreProfessorService(
                repository=repository,
                content_generator=None,  # API service doesn't need content generation
            )

    def get_professors(
        self,
        page: int = 1,
        size: int = 10,
        department_id: Optional[int] = None,
        name: Optional[str] = None,
        specialization: Optional[str] = None,
    ) -> ProfessorsListResponse:
        """
        Get a paginated list of professors with optional filtering.

        Args:
            page: Page number (starting from 1)
            size: Number of items per page
            department_id: Filter by department ID
            name: Filter by name (partial match)
            specialization: Filter by specialization (partial match)

        Returns:
            ProfessorsListResponse with paginated professors
        """
        # Create filters dictionary for the core service
        filters = {}
        if department_id is not None:
            filters["department_id"] = department_id
        if name:
            filters["name"] = name
        if specialization:
            filters["specialization"] = specialization

        # Get all professors with filters
        all_professors = self.core_service.list_professors(filters=filters)

        # Count total before pagination
        total = len(all_professors)

        # Apply pagination
        paginated_professors = self.core_service.list_professors(
            filters=filters, page=page, size=size
        )

        # Calculate total pages
        total_pages = ceil(total / size) if total > 0 else 1

        # Convert to response models
        professor_responses = [
            ProfessorResponse.model_validate(p.model_dump())
            for p in paginated_professors
        ]

        return ProfessorsListResponse(
            items=professor_responses,
            total=total,
            page=page,
            size=size,
            pages=total_pages,
        )

    def get_professor(self, professor_id: int) -> Optional[ProfessorResponse]:
        """
        Get a professor by ID.

        Args:
            professor_id: ID of the professor to retrieve

        Returns:
            ProfessorResponse or None if not found
        """
        try:
            professor = self.core_service.get_professor(str(professor_id))
            return ProfessorResponse.model_validate(professor.model_dump())
        except ProfessorNotFoundError:
            return None

    def create_professor(self, professor_data: ProfessorCreate) -> ProfessorResponse:
        """
        Create a new professor.

        Args:
            professor_data: Professor data for creation

        Returns:
            Created professor with ID
        """
        # Extract data from the create model
        data = professor_data.model_dump()

        # Use the core service to create the professor
        created_professor = self.core_service.create_professor(**data)

        # Convert to API response model
        return ProfessorResponse.model_validate(created_professor.model_dump())

    def update_professor(
        self, professor_id: int, professor_data: ProfessorUpdate
    ) -> Optional[ProfessorResponse]:
        """
        Update an existing professor.

        Args:
            professor_id: ID of the professor to update
            professor_data: New professor data

        Returns:
            Updated professor or None if not found
        """
        try:
            # Extract non-None values for update
            update_data = {
                k: v for k, v in professor_data.model_dump().items() if v is not None
            }

            # Use core service to update
            updated_professor = self.core_service.update_professor(
                str(professor_id), update_data
            )

            # Convert to response model
            return ProfessorResponse.model_validate(updated_professor.model_dump())
        except ProfessorNotFoundError:
            return None
        except DatabaseError:
            return None

    def delete_professor(self, professor_id: int) -> bool:
        """
        Delete a professor.

        Args:
            professor_id: ID of the professor to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            return self.core_service.delete_professor(str(professor_id))
        except (ProfessorNotFoundError, DatabaseError):
            return False

    def get_professor_courses(
        self, professor_id: int
    ) -> Optional[ProfessorCoursesResponse]:
        """
        Get courses taught by a professor.

        Args:
            professor_id: ID of the professor

        Returns:
            ProfessorCoursesResponse or None if professor not found
        """
        try:
            # Use core service to get courses
            courses = self.core_service.list_professor_courses(str(professor_id))

            # Convert to brief format
            course_briefs = [
                CourseBrief(
                    id=c.id,
                    code=c.code,
                    title=c.title,
                    department_id=c.department_id,
                    level=c.level,
                    credits=c.credits,
                )
                for c in courses
            ]

            return ProfessorCoursesResponse(
                professor_id=professor_id,
                courses=course_briefs,
                total=len(course_briefs),
            )
        except ProfessorNotFoundError:
            return None

    def get_professor_lectures(
        self, professor_id: int
    ) -> Optional[ProfessorLecturesResponse]:
        """
        Get lectures by a professor.

        Args:
            professor_id: ID of the professor

        Returns:
            ProfessorLecturesResponse or None if professor not found
        """
        try:
            # Use core service to get lectures
            lectures = self.core_service.list_professor_lectures(str(professor_id))

            # Convert to brief format
            lecture_briefs = [
                LectureBrief(
                    id=lecture.id,
                    title=lecture.title,
                    course_id=lecture.course_id,
                    week_number=lecture.week_number,
                    order_in_week=lecture.order_in_week,
                    description=lecture.description,
                )
                for lecture in lectures
            ]

            return ProfessorLecturesResponse(
                professor_id=professor_id,
                lectures=lecture_briefs,
                total=len(lecture_briefs),
            )
        except ProfessorNotFoundError:
            return None
