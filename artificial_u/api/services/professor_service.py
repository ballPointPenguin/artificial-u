"""
Professor service for handling business logic related to professors.
"""

from typing import Optional

from fastapi import HTTPException

from artificial_u.api.models.professors import (
    CourseBrief,
    ProfessorCoursesResponse,
    ProfessorCreate,
    ProfessorResponse,
    ProfessorsListResponse,
    ProfessorUpdate,
)
from artificial_u.api.services.base_service import BaseApiService
from artificial_u.models.core import Professor as CoreProfessor
from artificial_u.models.core import Student
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.models.visibility import discoverable_courses
from artificial_u.services import (
    ContentService,
    ImageService,
    ProfessorService,
    VoiceService,
)
from artificial_u.utils import (
    DatabaseError,
    ProfessorNotFoundError,
)


class ProfessorApiService(BaseApiService[CoreProfessor, ProfessorResponse, ProfessorsListResponse]):
    """API Service for professor-related operations."""

    def __init__(
        self,
        content_service: ContentService,
        image_service: ImageService,
        repository_factory: RepositoryFactory,
        voice_service: VoiceService,
        logger=None,
    ):
        """
        Initialize with all required services.

        Args:
            repository_factory: Repository factory instance
            content_service: Content generation service
            image_service: Image generation service
            voice_service: Voice service
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.repository_factory = repository_factory

        # Initialize job enqueue service for background processing
        from artificial_u.services.job_enqueue_service import JobEnqueueService

        job_enqueue_service = JobEnqueueService(
            repository_factory=repository_factory,
            logger=self.logger,
        )

        # Initialize core service (CRUD only) and generator service
        self.core_service = ProfessorService(
            repository_factory=repository_factory,
            voice_service=voice_service,
            job_enqueue_service=job_enqueue_service,
            logger=self.logger,
        )

        # Initialize generator service for AI generation workflows
        from artificial_u.services.professor_generator_service import ProfessorGeneratorService

        self.generator_service = ProfessorGeneratorService(
            professor_service=self.core_service,
            content_service=content_service,
            image_service=image_service,
            repository_factory=repository_factory,
            logger=self.logger,
        )

    def get_professors(
        self,
        page: int = 1,
        size: int = 10,
        department_id: Optional[int] = None,
        faculty_id: Optional[int] = None,
        name: Optional[str] = None,
        specialization: Optional[str] = None,
        language: Optional[str] = None,
    ) -> ProfessorsListResponse:
        """
        Get a paginated list of professors with optional filtering.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            department_id: Filter by department ID
            faculty_id: Filter by faculty ID (through department relationship)
            name: Filter by name (partial match)
            specialization: Filter by specialization (partial match)

        Returns:
            ProfessorsListResponse with paginated professors
        """
        # Build filters dictionary
        filters = {}
        if faculty_id is not None:
            filters["faculty_id"] = faculty_id
        if department_id is not None:
            filters["department_id"] = department_id
        if name:
            filters["name"] = name
        if specialization:
            filters["specialization"] = specialization
        if language is not None:
            filters["language"] = language

        try:
            # Call core service directly with filters
            all_professors = self.core_service.list_professors(
                filters=filters,
                page=page,
                size=size,
            )

            # Convert to response models
            response_items = [
                ProfessorResponse.model_validate(p.model_dump()) for p in all_professors
            ]

            # Get total count (core service already handled pagination)
            # So we need to get the full count
            all_professors_unpaginated = self.core_service.list_professors(
                filters=filters,
                page=None,
                size=None,
            )
            total = len(all_professors_unpaginated)

            # Calculate pages
            pages = self._calculate_pages(total, size)

            return ProfessorsListResponse(
                items=response_items,
                total=total,
                page=page,
                size=size,
                pages=pages,
            )
        except Exception as e:
            self._handle_general_error("get professors", e)

    def get_professor(self, professor_id: int) -> Optional[ProfessorResponse]:
        """
        Get a professor by ID.

        Args:
            professor_id: ID of the professor to retrieve

        Returns:
            ProfessorResponse or None if not found
        """
        try:
            professor = self.core_service.get_professor(professor_id)
            return ProfessorResponse.model_validate(professor.model_dump())
        except ProfessorNotFoundError:
            return None

    def create_professor(
        self, professor_data: ProfessorCreate, created_by: int = None
    ) -> ProfessorResponse:
        """
        Create a new professor.

        Args:
            professor_data: Professor data for creation
            created_by: Optional student ID who created the professor

        Returns:
            Created professor with ID

        Raises:
             HTTPException: If creation fails.
        """
        try:
            # Extract data from the Pydantic model
            data = professor_data.model_dump(
                exclude_unset=True
            )  # Use exclude_unset for partial updates

            # Add created_by if provided
            if created_by is not None:
                data["created_by"] = created_by

            # Instantiate the core Professor model
            professor_to_create = CoreProfessor(**data)

            # Pass the Professor instance to the core service method
            # Note: core_service.create_professor is currently sync, but we await it.
            # This works but might block. Ideally, core service/repo would be async too.
            created_professor = self.core_service.create_professor(professor_to_create)

            # Convert to API response model
            return ProfessorResponse.model_validate(created_professor.model_dump())
        except (DatabaseError, Exception) as e:
            self._handle_general_error("create professor", e)

    def update_professor(
        self,
        professor_id: int,
        professor_data: ProfessorUpdate,
        student_id: int,
        role: str,
    ) -> Optional[ProfessorResponse]:
        """
        Update an existing professor.

        Args:
            professor_id: ID of the professor to update
            professor_data: New professor data
            student_id: ID of the requesting student
            role: Role of the requesting student

        Returns:
            Updated professor or None if not found

        Raises:
            HTTPException: 403 if user doesn't own the professor (unless admin)
        """
        try:
            # First, get the professor to check ownership
            professor_model = self.core_service.get_professor(professor_id)

            # Verify ownership (admins can modify any professor, creators only their own)
            from artificial_u.api.security.auth0 import verify_asset_ownership

            verify_asset_ownership(student_id, professor_model.created_by, role, "professor")

            # Extract non-None values for update
            update_data = {k: v for k, v in professor_data.model_dump().items() if v is not None}

            # Use core service to update
            updated_professor = self.core_service.update_professor(professor_id, update_data)

            # Convert to response model
            return ProfessorResponse.model_validate(updated_professor.model_dump())
        except ProfessorNotFoundError:
            return None
        except DatabaseError:
            return None

    def delete_professor(self, professor_id: int, student_id: int, role: str) -> bool:
        """
        Delete a professor.

        Args:
            professor_id: ID of the professor to delete
            student_id: ID of the requesting student
            role: Role of the requesting student

        Returns:
            True if deleted successfully, False otherwise

        Raises:
            HTTPException: 403 if user doesn't own the professor (unless admin)
        """
        try:
            # First, get the professor to check ownership
            professor_model = self.core_service.get_professor(professor_id)

            # Verify ownership (admins can delete any professor, creators only their own)
            from artificial_u.api.security.auth0 import verify_asset_ownership

            verify_asset_ownership(student_id, professor_model.created_by, role, "professor")

            return self.core_service.delete_professor(professor_id)
        except ProfessorNotFoundError, DatabaseError:
            return False

    def get_professor_courses(
        self, professor_id: int, viewer: Optional[Student] = None
    ) -> Optional[ProfessorCoursesResponse]:
        """
        Get courses taught by a professor that `viewer` may discover.

        Args:
            professor_id: ID of the professor
            viewer: The requesting student, if authenticated

        Returns:
            ProfessorCoursesResponse or None if professor not found
        """
        try:
            # Use core service to get courses
            courses = self.core_service.list_professor_courses(
                professor_id, course_filter=discoverable_courses(viewer)
            )

            # Convert to brief format
            course_briefs = [
                CourseBrief(
                    id=c.id,
                    code=c.code,
                    title=c.title,
                    department_id=c.department_id,
                    level=c.level,
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

    async def generate_professor_image(
        self, professor_id: int, student_id: int, role: str
    ) -> Optional[ProfessorResponse]:
        """
        Triggers image generation for a professor and returns the updated professor.

        Args:
            professor_id: The ID of the professor
            student_id: ID of the requesting student
            role: Role of the requesting student

        Returns:
            The updated ProfessorResponse if successful, None otherwise

        Raises:
            HTTPException: 403 if user doesn't own the professor (unless admin)
        """
        try:
            # First, get the professor to check ownership
            professor_model = self.core_service.get_professor(professor_id)

            # Verify ownership (admins can modify any professor, creators only their own)
            from artificial_u.api.security.auth0 import verify_asset_ownership

            verify_asset_ownership(student_id, professor_model.created_by, role, "professor")

            # Call the generator service method
            updated_professor = await self.generator_service.generate_and_set_professor_image(
                professor_id=professor_id
            )

            if updated_professor:
                return ProfessorResponse.model_validate(updated_professor.model_dump())
            else:
                return None

        except ProfessorNotFoundError:
            return None

        except HTTPException:
            # Ownership failures (403) must reach the client unchanged
            raise

        except Exception as e:
            self.logger.error(
                f"Error generating image for professor {professor_id}: {e}",
                exc_info=True,
            )
            return None

    def assign_voice_to_professor(
        self, professor_id: int, student_id: int, role: str
    ) -> Optional[ProfessorResponse]:
        """
        Assign a voice to an existing professor.

        Args:
            professor_id: ID of the professor to assign voice to
            student_id: ID of the requesting student
            role: Role of the requesting student

        Returns:
            Updated professor with assigned voice, or None if professor not found

        Raises:
            HTTPException: 403 if user doesn't own the professor (unless admin)
        """
        try:
            # First, get the professor to check ownership
            professor_model = self.core_service.get_professor(professor_id)

            # Verify ownership (admins can modify any professor, creators only their own)
            from artificial_u.api.security.auth0 import verify_asset_ownership

            verify_asset_ownership(student_id, professor_model.created_by, role, "professor")

            updated_professor = self.core_service.assign_voice_to_professor(professor_id)
            return ProfessorResponse.model_validate(updated_professor.model_dump())
        except ProfessorNotFoundError:
            return None
        except DatabaseError:
            return None
