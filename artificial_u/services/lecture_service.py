"""
Lecture management service for ArtificialU.

This service handles CRUD operations for lectures. For AI generation and complex
processing workflows, see LectureGeneratorService.
"""

import logging
from typing import Any, Dict, List, Optional

from artificial_u.models.core import Lecture
from artificial_u.utils import DatabaseError, LectureNotFoundError


class LectureService:
    """Service for managing lecture entities (CRUD operations only)."""

    def __init__(
        self,
        repository_factory,
        logger=None,
    ):
        """
        Initialize the lecture service.

        Args:
            repository_factory: Repository factory instance
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)

    # --- CRUD Methods --- #

    def create_lecture(
        self,
        course_id: int,
        topic_id: int,
        title: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        audio_url: Optional[str] = None,
        transcript_url: Optional[str] = None,
        revision: Optional[int] = None,
    ) -> Lecture:
        """
        Create a new lecture.

        Args:
            course_id: ID of the course this lecture belongs to
            topic_id: ID of the topic this lecture belongs to
            title: Title of the lecture
            content: Optional lecture content
            summary: Optional lecture summary
            audio_url: Optional URL to audio content
            transcript_url: Optional URL to transcript content
            revision: Optional revision number for the lecture

        Returns:
            Lecture: The created lecture

        Raises:
            DatabaseError: If there's an error saving to the database
        """
        # Create lecture object
        lecture = Lecture(
            course_id=course_id,
            topic_id=topic_id,
            title=title,
            revision=revision,
            content=content,
            summary=summary,
            audio_url=audio_url,
            transcript_url=transcript_url,
        )

        try:
            # Save to database using repository
            created_lecture = self.repository_factory.lecture.create(lecture)
            self.logger.info(f"Created lecture for topic {topic_id}, course {course_id}")
            return created_lecture
        except Exception as e:
            error_msg = f"Failed to create lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_lecture(self, lecture_id: int) -> Lecture:
        """
        Get a lecture by ID.

        Args:
            lecture_id: ID of the lecture

        Returns:
            Lecture: The lecture object

        Raises:
            LectureNotFoundError: If lecture not found
        """
        lecture = self.repository_factory.lecture.get(lecture_id)
        if not lecture:
            error_msg = f"Lecture with ID {lecture_id} not found"
            self.logger.error(error_msg)
            raise LectureNotFoundError(error_msg)
        return lecture

    def get_lecture_by_course_week_order(
        self, course_id: int, week_number: int, order_in_week: int
    ) -> Lecture:
        """
        Get a specific lecture by its position in a course.

        Args:
            course_id: ID of the course
            week_number: Week number in the course
            order_in_week: Order of the lecture within the week

        Returns:
            Lecture: The lecture object

        Raises:
            LectureNotFoundError: If lecture not found
        """
        lecture = self.repository_factory.lecture.get_by_course_week_order(
            course_id=course_id,
            week_number=week_number,
            order_in_week=order_in_week,
        )
        if not lecture:
            error_msg = (
                f"Lecture not found for course {course_id}, "
                f"week {week_number}, order {order_in_week}"
            )
            self.logger.error(error_msg)
            raise LectureNotFoundError(error_msg)
        return lecture

    def list_lectures(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List[Lecture]:
        """
        List lectures with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            course_id: Optional filter by course ID
            professor_id: Optional filter by professor ID
            topic_id: Optional filter by topic ID
            search_query: Optional search in title/description

        Returns:
            List[Lecture]: List of lectures

        Raises:
            DatabaseError: If there's an error retrieving from the database
        """
        try:
            lectures = self.repository_factory.lecture.list(
                page=page,
                size=size,
                course_id=course_id,
                professor_id=professor_id,
                topic_id=topic_id,
                search_query=search_query,
            )
            self.logger.debug(f"Found {len(lectures)} lectures")
            return lectures
        except Exception as e:
            error_msg = f"Failed to list lectures: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def update_lecture(self, lecture_id: int, update_data: Dict[str, Any]) -> Lecture:
        """
        Update a lecture.

        Args:
            lecture_id: ID of the lecture to update
            update_data: Dictionary of fields to update

        Returns:
            Lecture: The updated lecture

        Raises:
            LectureNotFoundError: If lecture not found
            DatabaseError: If there's an error updating the database
        """
        # Get existing lecture
        lecture = self.get_lecture(lecture_id)

        # Update fields
        for key, value in update_data.items():
            if hasattr(lecture, key):
                setattr(lecture, key, value)
            else:
                self.logger.warning(f"Ignoring unknown field: {key}")

        try:
            # Save changes
            updated_lecture = self.repository_factory.lecture.update(lecture)
            self.logger.info(f"Updated lecture {lecture_id}")
            return updated_lecture
        except Exception as e:
            error_msg = f"Failed to update lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_lecture(self, lecture_id: int) -> bool:
        """
        Delete a lecture.

        Args:
            lecture_id: ID of the lecture to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            LectureNotFoundError: If lecture not found
            DatabaseError: If there's an error deleting from the database
        """
        # Check if lecture exists
        self.get_lecture(lecture_id)

        try:
            # Delete the lecture
            result = self.repository_factory.lecture.delete(lecture_id)
            if result:
                self.logger.info(f"Lecture {lecture_id} deleted successfully")
            return result
        except Exception as e:
            error_msg = f"Failed to delete lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e


# Note: For AI generation and complex processing workflows (lecture generation,
# audio generation, summary generation, etc.), see:
# artificial_u.services.lecture_generator_service.LectureGeneratorService
