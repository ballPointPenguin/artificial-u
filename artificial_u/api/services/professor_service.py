"""
Professor service for handling business logic related to professors.
"""

import random
from typing import List, Optional

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
from artificial_u.api.services.base_service import BaseApiService
from artificial_u.models.core import Professor as CoreProfessor
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import (
    ContentService,
    ImageService,
    ProfessorService,
    VoiceService,
)
from artificial_u.utils import (
    ContentGenerationError,
    DatabaseError,
    GenerationError,
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
            job_enqueue_service=job_enqueue_service,
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
            page: Page number (1-indexed)
            size: Items per page
            department_id: Filter by department ID
            name: Filter by name (partial match)
            specialization: Filter by specialization (partial match)

        Returns:
            ProfessorsListResponse with paginated professors
        """
        # Build filters dictionary
        filters = {}
        if department_id is not None:
            filters["department_id"] = department_id
        if name:
            filters["name"] = name
        if specialization:
            filters["specialization"] = specialization

        return self._standard_list_operation(
            core_service_method="list_professors",
            response_class=ProfessorResponse,
            list_response_class=ProfessorsListResponse,
            page=page,
            size=size,
            filters=filters,
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
            professor = self.core_service.get_professor(professor_id)
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

        Raises:
             HTTPException: If creation fails.
        """
        try:
            # Extract data from the Pydantic model
            data = professor_data.model_dump(
                exclude_unset=True
            )  # Use exclude_unset for partial updates

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
            update_data = {k: v for k, v in professor_data.model_dump().items() if v is not None}

            # Use core service to update
            updated_professor = self.core_service.update_professor(professor_id, update_data)

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
            return self.core_service.delete_professor(professor_id)
        except (ProfessorNotFoundError, DatabaseError):
            return False

    def get_professor_courses(self, professor_id: int) -> Optional[ProfessorCoursesResponse]:
        """
        Get courses taught by a professor.

        Args:
            professor_id: ID of the professor

        Returns:
            ProfessorCoursesResponse or None if professor not found
        """
        try:
            # Use core service to get courses
            courses = self.core_service.list_professor_courses(professor_id)

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

    def get_professor_lectures(self, professor_id: int) -> Optional[ProfessorLecturesResponse]:
        """
        Get lectures by a professor.

        Args:
            professor_id: ID of the professor

        Returns:
            ProfessorLecturesResponse or None if professor not found
        """
        try:
            # First check if professor exists
            self.core_service.get_professor(professor_id)

            # Get lectures by professor using the lecture repository
            lectures = self.repository_factory.lecture.list(professor_id=professor_id)

            # Convert to brief format
            lecture_briefs = [
                LectureBrief(
                    id=lecture.id,
                    course_id=lecture.course_id,
                    topic_id=lecture.topic_id,
                    title=lecture.title,
                    summary=lecture.summary,
                    audio_url=lecture.audio_url,
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

    async def generate_professor_image(self, professor_id: int) -> Optional[ProfessorResponse]:
        """
        Triggers image generation for a professor and returns the updated professor.

        Args:
            professor_id: The ID of the professor

        Returns:
            The updated ProfessorResponse if successful, None otherwise
        """
        try:
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

        except Exception as e:
            # Log the exception
            self.logger.error(
                f"Error generating image for professor {professor_id}: {e}",
                exc_info=True,
            )
            return None

    async def generate_professor(self, generation_data: ProfessorGenerate) -> ProfessorResponse:
        """
        Generate a professor profile using AI based on provided partial data.

        Args:
            generation_data: Input data containing optional partial attributes.

        Returns:
            ProfessorResponse: The generated professor profile (not saved).
        """
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
            # Add freeform prompt if the model includes it (assuming ProfessorGenerate might)
            if hasattr(generation_data, "freeform_prompt") and generation_data.freeform_prompt:
                partial_attrs["freeform_prompt"] = generation_data.freeform_prompt

            generated_dict = await self.generator_service.generate_professor(
                partial_attributes=partial_attrs
            )

            # Convert the dictionary to the API response model
            # Add placeholder ID and validate
            generated_dict["id"] = -1  # Placeholder for validation
            response = ProfessorResponse.model_validate(generated_dict)

            self.logger.info(f"Successfully generated professor data: {response.name}")
            return response

        except (ContentGenerationError, DatabaseError, ValueError, GenerationError) as e:
            # Include GenerationError if core service can raise it specifically
            self.logger.error(f"Professor generation failed: {e}", exc_info=True)
            # Re-raise as HTTPException for the API layer
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate professor data: {e}",
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during professor generation: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=("An unexpected error occurred during profile generation."),
            )

    def get_featured_professors(self) -> List[ProfessorResponse]:
        """
        Get a list of up to 3 random featured professors.
        """
        try:
            all_professors_core = self.core_service.list_professors(filters=None)  # Get all

            if not all_professors_core:
                return []

            num_to_select = min(len(all_professors_core), 3)
            featured_professors_core = random.sample(all_professors_core, num_to_select)

            featured_responses = [
                ProfessorResponse.model_validate(p.model_dump()) for p in featured_professors_core
            ]
            self.logger.info(f"Returning {len(featured_responses)} featured professors.")
            return featured_responses

        except Exception as e:
            self._handle_general_error("get featured professors", e)

    def assign_voice_to_professor(self, professor_id: int) -> Optional[ProfessorResponse]:
        """
        Assign a voice to an existing professor.

        Args:
            professor_id: ID of the professor to assign voice to

        Returns:
            Updated professor with assigned voice, or None if professor not found
        """
        try:
            updated_professor = self.core_service.assign_voice_to_professor(professor_id)
            return ProfessorResponse.model_validate(updated_professor.model_dump())
        except ProfessorNotFoundError:
            return None
        except DatabaseError:
            return None
