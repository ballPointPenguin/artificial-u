"""
Lecture API service for handling lecture operations in the API layer.
"""

import logging
from typing import Optional

from fastapi import HTTPException, status

from artificial_u.api.models.lectures import Lecture, LectureCreate, LectureList, LectureUpdate
from artificial_u.generators.content import ContentGenerator
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import LectureService

# from artificial_u.services.content_service import ContentService
from artificial_u.services.course_service import CourseService
from artificial_u.services.professor_service import ProfessorService
from artificial_u.services.storage_service import StorageService


class LectureApiService:
    """Service for handling lecture API operations."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        professor_service: ProfessorService,
        course_service: CourseService,
        content_generator: ContentGenerator,
        # content_service: ContentService,
        storage_service: StorageService,
        logger=None,
    ):
        """
        Initialize with required services.

        Args:
            repository_factory: Repository factory instance
            professor_service: Professor service for professor-related operations
            course_service: Course service for course-related operations
            content_generator: Content generator service
            storage_service: Storage service for file operations
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Initialize core service with dependencies
        self.core_service = LectureService(
            repository_factory=repository_factory,
            professor_service=professor_service,
            course_service=course_service,
            content_generator=content_generator,
            # content_service=content_service,
            storage_service=storage_service,
            logger=self.logger,
        )

    def list_lectures(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> LectureList:
        """
        List lectures with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            search_query: Search query for title/description

        Returns:
            LectureList: Paginated list of lectures
        """
        try:
            # Get lectures from core service
            lectures = self.core_service.list_lectures(
                page=page,
                size=size,
                course_id=course_id,
                professor_id=professor_id,
                search_query=search_query,
            )

            # Convert core models to API models
            lecture_items = [
                Lecture(
                    id=lecture.id,
                    title=lecture.title,
                    description=lecture.description,
                    content=lecture.content,
                    course_id=lecture.course_id,
                    week_number=lecture.week_number,
                    order_in_week=lecture.order_in_week,
                    audio_url=lecture.audio_url,
                )
                for lecture in lectures
            ]

            # Get total count from core service
            total_count = self.core_service.count_lectures(
                course_id=course_id,
                professor_id=professor_id,
                search_query=search_query,
            )

            return LectureList(
                items=lecture_items,
                total=total_count,
                page=page,
                page_size=size,
            )
        except Exception as e:
            self.logger.error(f"Error listing lectures: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve lectures",
            )

    def get_lecture(self, lecture_id: int) -> Optional[Lecture]:
        """
        Get detailed information about a specific lecture.

        Args:
            lecture_id: The unique identifier of the lecture

        Returns:
            Lecture: Lecture information or None if not found
        """
        try:
            lecture = self.core_service.get_lecture(lecture_id)
            if not lecture:
                return None

            return Lecture(
                id=lecture.id,
                title=lecture.title,
                description=lecture.description,
                content=lecture.content,
                course_id=lecture.course_id,
                week_number=lecture.week_number,
                order_in_week=lecture.order_in_week,
                audio_url=lecture.audio_url,
            )
        except Exception as e:
            self.logger.error(f"Error getting lecture {lecture_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve lecture",
            )

    def create_lecture(self, lecture_data: LectureCreate) -> Lecture:
        """
        Create a new lecture.

        Args:
            lecture_data: The lecture data to create

        Returns:
            Lecture: The created lecture

        Raises:
            HTTPException: If course doesn't exist or other validation errors
        """
        try:
            # Create lecture using core service
            lecture = self.core_service.create_lecture(
                title=lecture_data.title,
                description=lecture_data.description,
                content=lecture_data.content,
                course_id=lecture_data.course_id,
                week_number=lecture_data.week_number,
                order_in_week=lecture_data.order_in_week,
                audio_url=lecture_data.audio_url,
            )

            return Lecture(
                id=lecture.id,
                title=lecture.title,
                description=lecture.description,
                content=lecture.content,
                course_id=lecture.course_id,
                week_number=lecture.week_number,
                order_in_week=lecture.order_in_week,
                audio_url=lecture.audio_url,
            )
        except Exception as e:
            self.logger.error(f"Error creating lecture: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    def update_lecture(self, lecture_id: int, lecture_data: LectureUpdate) -> Optional[Lecture]:
        """
        Update an existing lecture with new information.

        Args:
            lecture_id: The unique identifier of the lecture to update
            lecture_data: An instance of LectureUpdate containing fields to update

        Returns:
            Optional[Lecture]: The updated lecture information or None if not found
        """
        try:
            # Update lecture using core service
            lecture = self.core_service.update_lecture(
                lecture_id=lecture_id,
                update_data=lecture_data.model_dump(exclude_unset=True),
            )

            if not lecture:
                return None

            return Lecture(
                id=lecture.id,
                title=lecture.title,
                description=lecture.description,
                content=lecture.content,
                course_id=lecture.course_id,
                week_number=lecture.week_number,
                order_in_week=lecture.order_in_week,
                audio_url=lecture.audio_url,
            )
        except Exception as e:
            self.logger.error(f"Error updating lecture: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    def delete_lecture(self, lecture_id: int) -> bool:
        """
        Delete a lecture.

        Args:
            lecture_id: The unique identifier of the lecture to delete

        Returns:
            bool: True if lecture was deleted, False if not found
        """
        try:
            return self.core_service.delete_lecture(lecture_id)
        except Exception as e:
            self.logger.error(f"Error deleting lecture: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
