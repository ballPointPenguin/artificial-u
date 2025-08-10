"""
Lecture API service for handling lecture operations in the API layer.
"""

from typing import Optional

from fastapi import HTTPException, status

# Import API models directly
from artificial_u.api.models.lectures import (
    Lecture,
    LectureCreate,
    LectureGenerate,
    LectureListResponse,
    LectureUpdate,
)
from artificial_u.api.services.base_service import BaseApiService
from artificial_u.models.core import Lecture as CoreLecture
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import (
    StorageService,  # Keep even if not used directly now, matches dependency injection
)
from artificial_u.services import (
    ContentService,
    CourseService,
)
from artificial_u.services import LectureService as CoreLectureService  # Rename to avoid conflict
from artificial_u.services import (
    ProfessorService,
    TopicService,
)
from artificial_u.utils import ContentGenerationError, DatabaseError, LectureNotFoundError


class LectureApiService(BaseApiService[CoreLecture, Lecture, LectureListResponse]):
    """Service for handling lecture API operations."""

    def __init__(
        self,
        content_service: ContentService,
        course_service: CourseService,
        professor_service: ProfessorService,
        repository_factory: RepositoryFactory,
        storage_service: StorageService,
        topic_service: TopicService,
        logger=None,
    ):
        """
        Initialize with required services.

        Args:
            repository_factory: Repository factory instance
            professor_service: Professor service for professor-related operations
            course_service: Course service for course-related operations
            content_service: Content service for content-related operations
            storage_service: Storage service for file operations (dependency injection)
            topic_service: Topic service for topic-related operations
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.repository_factory = repository_factory  # Keep repository factory

        # Initialize core service with dependencies it requires
        self.core_service = CoreLectureService(
            repository_factory=repository_factory,
            professor_service=professor_service,
            course_service=course_service,
            content_service=content_service,
            topic_service=topic_service,
            # storage_service is not passed to core service currently
            logger=self.logger,
        )
        # Keep references if needed, though core service should handle most logic
        self.professor_service = professor_service
        self.course_service = course_service
        self.content_service = content_service
        self.storage_service = storage_service
        self.topic_service = topic_service

    def list_lectures(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> LectureListResponse:
        """
        List lectures with filtering and pagination using the core service and repository.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            topic_id: Filter by topic ID
            search: Search query for title/description

        Returns:
            LectureListResponse: Paginated list of lectures

        Raises:
            HTTPException: If there's an error retrieving data.
        """
        try:
            # Get lectures using the core service list method (delegates to repository)
            core_lectures = self.core_service.list_lectures(
                page=page,
                size=size,
                course_id=course_id,
                professor_id=professor_id,
                topic_id=topic_id,
                search_query=search,
            )

            # Convert core models to API models
            lecture_items = [
                Lecture.model_validate(lecture)  # Use model_validate for core->API conversion
                for lecture in core_lectures
            ]

            # Get total count using the repository directly
            total_count = self.repository_factory.lecture.count(
                course_id=course_id,
                professor_id=professor_id,
                topic_id=topic_id,
                search_query=search,
            )

            # Calculate total pages
            pages = self._calculate_pages(total_count, size)

            return LectureListResponse(
                items=lecture_items,
                total=total_count,
                page=page,
                size=size,
                pages=pages,
            )
        except DatabaseError as e:
            self._handle_database_error("list lectures", e)
        except Exception as e:
            self._handle_general_error("list lectures", e)

    def get_lecture(self, lecture_id: int) -> Lecture:
        """
        Get detailed information about a specific lecture using the core service.

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Lecture: Lecture API model information

        Raises:
            HTTPException: 404 if not found, 500 for other errors.
        """
        try:
            core_lecture = self.core_service.get_lecture(lecture_id)
            return Lecture.model_validate(core_lecture)
        except LectureNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecture with ID {lecture_id} not found",
            )
        except DatabaseError as e:
            self._handle_database_error("get lecture", e)
        except Exception as e:
            self._handle_general_error("get lecture", e)

    def create_lecture(self, lecture_data: LectureCreate) -> Lecture:
        """
        Create a new lecture using the core service.

        Args:
            lecture_data: The lecture data (API model) to create

        Returns:
            Lecture: The created lecture (API model)

        Raises:
            HTTPException: 400 for database errors (like constraint violations),
                           500 for unexpected errors.
        """
        try:
            # Create lecture using core service, passing individual args
            # Core service create_lecture expects: course_id, topic_id, content, summary, title,
            # audio_url, transcript_url, revision
            core_lecture = self.core_service.create_lecture(
                course_id=lecture_data.course_id,
                topic_id=lecture_data.topic_id,
                content=lecture_data.content,
                summary=lecture_data.summary,
                title=lecture_data.title,
                audio_url=lecture_data.audio_url,
                transcript_url=lecture_data.transcript_url,
                revision=lecture_data.revision,
            )
            return Lecture.model_validate(core_lecture)
        except DatabaseError as e:
            self._handle_database_error("create lecture", e)
        except Exception as e:
            self._handle_general_error("create lecture", e)

    def update_lecture(self, lecture_id: int, lecture_data: LectureUpdate) -> Lecture:
        """
        Update an existing lecture using the core service.

        Args:
            lecture_id: The unique identifier of the lecture to update
            lecture_data: An instance of LectureUpdate containing fields to update

        Returns:
            Lecture: The updated lecture information (API model)

        Raises:
            HTTPException: 404 if not found, 400 for database errors during update,
                           500 for unexpected errors.
        """
        try:
            # Update lecture using core service
            update_dict = lecture_data.model_dump(exclude_unset=True)
            core_lecture = self.core_service.update_lecture(
                lecture_id=lecture_id,
                update_data=update_dict,
            )
            return Lecture.model_validate(core_lecture)
        except LectureNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecture with ID {lecture_id} not found for update.",
            )
        except DatabaseError as e:
            self._handle_database_error("update lecture", e)
        except Exception as e:
            self._handle_general_error("update lecture", e)

    def delete_lecture(self, lecture_id: int) -> bool:
        """
        Delete a lecture using the core service.

        Args:
            lecture_id: The unique identifier of the lecture to delete

        Returns:
            bool: True if lecture was deleted.

        Raises:
            HTTPException: 404 if not found, 400 for database errors during delete,
                           500 for unexpected errors.
        """
        try:
            deleted = self.core_service.delete_lecture(lecture_id)
            return deleted  # Core service raises LectureNotFound if it doesn't exist initially
        except LectureNotFoundError:
            # This case should ideally be caught by the core service,
            # but handle here for robustness if core returns False (though it shouldn't)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecture with ID {lecture_id} not found for deletion.",
            )
        except DatabaseError as e:
            self._handle_database_error("delete lecture", e)
        except Exception as e:
            self._handle_general_error("delete lecture", e)

    def get_lecture_content(self, lecture_id: int) -> Optional[str]:
        """
        Get the content of a specific lecture using the repository.

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Optional[str]: The lecture content, or None if not found or has no content.

        Raises:
            HTTPException: 500 for unexpected errors.
        """
        try:
            # Use repository directly for simple field retrieval
            content = self.repository_factory.lecture.get_content(lecture_id)
            # Note: Repository returns None if lecture not found or content is NULL
            return content
        except Exception as e:
            self._handle_general_error("get lecture content", e)

    def get_lecture_audio_url(self, lecture_id: int) -> Optional[str]:
        """
        Get the audio URL of a specific lecture using the repository.

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Optional[str]: The lecture audio URL, or None if not found or has no audio URL.

        Raises:
            HTTPException: 500 for unexpected errors.
        """
        try:
            # Use repository directly for simple field retrieval
            audio_url = self.repository_factory.lecture.get_audio_url(lecture_id)
            # Note: Repository returns None if lecture not found or audio_url is NULL
            return audio_url
        except Exception as e:
            self._handle_general_error("get lecture audio URL", e)

    async def generate_lecture_audio(self, lecture_id: int) -> Lecture:
        """
        Trigger audio generation for a lecture, then return the updated lecture.

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Lecture: Updated lecture with audio_url populated if successful
        """
        try:
            # Ensure the lecture exists first
            self.core_service.get_lecture(lecture_id)

            # Delegate to core service for audio generation
            await self.core_service.generate_lecture_audio(lecture_id)

            # Fetch and return updated lecture
            updated_core = self.core_service.get_lecture(lecture_id)
            return Lecture.model_validate(updated_core)
        except LectureNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lecture with ID {lecture_id} not found",
            )
        except (ContentGenerationError, DatabaseError, ValueError) as e:
            self.logger.error(f"Audio generation failed for lecture {lecture_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate audio for lecture {lecture_id}: {e}",
            )
        except Exception as e:
            self._handle_general_error("generate lecture audio", e)

    async def generate_lecture(self, generation_data: LectureGenerate) -> Lecture:
        """
        Generate lecture content using AI based on partial data and save to database.
        This method generates the data and creates/saves the lecture.

        Args:
            generation_data: Input data containing optional partial attributes and prompt.

        Returns:
            Lecture: The generated and saved lecture data (API model).

        Raises:
            HTTPException: If generation fails or prerequisites are not found.
        """
        log_attrs = (
            list(generation_data.partial_attributes.keys())
            if generation_data.partial_attributes
            else "None"
        )
        self.logger.info(
            f"Received request to generate lecture with partial attributes: {log_attrs}"
        )
        try:
            # Prepare attributes for the core service
            partial_attrs = generation_data.partial_attributes or {}  # Start with partial attrs
            if generation_data.freeform_prompt:  # Add prompt if provided
                partial_attrs["freeform_prompt"] = generation_data.freeform_prompt

            # Call the core service to generate the lecture content dictionary
            # The core service generate_lecture returns a dict
            generated_dict = await self.core_service.generate_lecture(
                partial_attributes=partial_attrs
            )

            # Convert the dictionary to the API response model
            # The core LectureService.generate_lecture returns a dict like:
            # {"course_id": ..., "topic_id": ..., "content": ..., "summary": ..., "title": ...}
            # This dict is used to populate api_lecture_data for validation.

            # Revision should come from generated_dict if available.
            # Content, summary, and title must be in generated_dict.
            # course_id and topic_id are in partial_attributes and should be in generated_dict.

            # Create a core Lecture object with the generated data
            # Provide default revision if not present (similar to repository logic)
            revision = generated_dict.get("revision")
            if revision is None:
                # Calculate next revision for the topic (similar to repository.create logic)
                try:
                    # Get the maximum revision for this specific topic
                    topic_lectures = self.repository_factory.lecture.list_by_topic(
                        generated_dict.get("topic_id")
                    )
                    max_revision = (
                        max([lecture.revision for lecture in topic_lectures])
                        if topic_lectures
                        else 0
                    )
                    revision = max_revision + 1
                except Exception:
                    # Fallback to 1 if we can't calculate
                    revision = 1

            # Create the lecture using the core service
            core_lecture = self.core_service.create_lecture(
                course_id=generated_dict.get("course_id"),
                topic_id=generated_dict.get("topic_id"),
                title=generated_dict.get("title"),
                content=generated_dict.get("content"),
                summary=generated_dict.get("summary"),
                audio_url=generated_dict.get("audio_url"),
                transcript_url=generated_dict.get("transcript_url"),
                revision=revision,
            )

            # Convert to API model and return
            response = Lecture.model_validate(core_lecture)

            self.logger.info(
                f"Successfully generated and saved lecture {response.id} "
                f"for topic {response.topic_id}"
            )
            return response

        except (ContentGenerationError, DatabaseError, ValueError) as e:
            # Handle errors from core service (generation, DB lookups, parsing)
            self.logger.error(f"Lecture generation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate lecture data: {e}",
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during lecture generation: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=("An unexpected error occurred during lecture generation."),
            )
