"""
Professor service for handling business logic related to professors.
"""

import logging
from math import ceil
from typing import Optional

from fastapi import HTTPException, status

from artificial_u.api.models.professors import (
    CourseBrief,
    LectureBrief,
    ProfessorCoursesResponse,
    ProfessorCreate,
    ProfessorGenerate,
    ProfessorLecturesResponse,
    ProfessorResponse,
    ProfessorsListResponse,
    ProfessorUpdate,
)
from artificial_u.models.core import Professor
from artificial_u.services import ProfessorService
from artificial_u.services.content_service import ContentService
from artificial_u.services.image_service import ImageService
from artificial_u.services.voice_service import VoiceService
from artificial_u.utils.exceptions import (
    DatabaseError,
    GenerationError,
    ProfessorNotFoundError,
)


class ProfessorApiService:
    """API Service for professor-related operations."""

    def __init__(
        self,
        repository,
        content_service: ContentService,
        image_service: ImageService,
        voice_service: Optional[VoiceService] = None,
        logger=None,
    ):
        """
        Initialize with all required services.

        Args:
            repository: Database repository factory
            content_service: Content generation service
            image_service: Image generation service
            voice_service: Voice service for voice assignment (optional)
            logger: Optional logger instance
        """
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)

        # Initialize core service with all required dependencies
        self.core_service = ProfessorService(
            repository=repository,
            content_service=content_service,
            image_service=image_service,
            voice_service=voice_service,
            logger=self.logger,
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

    async def create_professor(
        self, professor_data: ProfessorCreate
    ) -> ProfessorResponse:
        """
        Create a new professor.

        Args:
            professor_data: Professor data for creation

        Returns:
            Created professor with ID

        Raises:
             HTTPException: If creation fails.
        """
        # Extract data from the Pydantic model
        data = professor_data.model_dump(
            exclude_unset=True
        )  # Use exclude_unset for partial updates

        try:
            # Instantiate the core Professor model
            professor_to_create = Professor(**data)

            # Pass the Professor instance to the core service method
            # Note: core_service.create_professor is currently sync, but we await it.
            # This works but might block. Ideally, core service/repo would be async too.
            created_professor = self.core_service.create_professor(professor_to_create)

            # Convert to API response model
            return ProfessorResponse.model_validate(created_professor.model_dump())
        except (DatabaseError, Exception) as e:
            self.logger.error(f"Error creating professor: {e}", exc_info=True)
            # Raise a generic 500 error for the API layer
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create professor: {e}",
            )

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

    async def generate_professor_image(
        self, professor_id: int
    ) -> Optional[ProfessorResponse]:
        """
        Triggers image generation for a professor and returns the updated professor.

        Args:
            professor_id: The ID of the professor

        Returns:
            The updated ProfessorResponse if successful, None otherwise
        """
        try:
            # Call the core service method
            updated_professor = (
                await self.core_service.generate_and_set_professor_image(
                    professor_id=str(professor_id)
                )
            )

            if updated_professor:
                return ProfessorResponse.model_validate(updated_professor.model_dump())
            else:
                return None

        except ProfessorNotFoundError:
            return None

        except Exception as e:
            # Log the exception
            self.logger.error(
                f"Error generating image for professor {professor_id}: {e}",
                exc_info=True,
            )
            return None

    async def generate_professor(
        self, generation_data: ProfessorGenerate
    ) -> ProfessorResponse:
        """
        Generate a professor profile using AI based on provided partial data.

        Args:
            generation_data: Input data containing optional partial attributes.

        Returns:
            ProfessorResponse: The generated professor profile (not saved).
        """
        from datetime import datetime

        log_attrs = (
            list(generation_data.partial_attributes.keys())
            if generation_data.partial_attributes
            else "None"
        )
        self.logger.info(
            f"Received request to generate professor with partial attributes: {log_attrs}"
        )
        try:
            # Pass the partial attributes dictionary (or empty dict) to the core service
            partial_attrs = generation_data.partial_attributes or {}
            generated_dict = await self.core_service.generate_professor_profile(
                partial_attributes=partial_attrs
            )

            # Convert the dictionary to the API response model
            response = ProfessorResponse(
                **generated_dict,
            )
            self.logger.info(f"Successfully generated professor data: {response.name}")
            return response

        except GenerationError as e:
            self.logger.error(f"Professor generation failed: {e}", exc_info=True)
            # Re-raise as HTTPException for the API layer
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate professor profile: {e}",
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error during professor generation: {e}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=("An unexpected error occurred during profile generation."),
            )
