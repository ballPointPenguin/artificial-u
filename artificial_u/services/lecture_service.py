"""
Lecture management service for ArtificialU.

This service handles CRUD operations for lectures. For AI generation and complex
processing workflows, see LectureGeneratorService.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from artificial_u.models.core import Lecture
from artificial_u.services.storage_service import StorageService
from artificial_u.utils import DatabaseError, LectureNotFoundError


class LectureService:
    """Service for managing lecture entities (CRUD operations only)."""

    def __init__(
        self,
        repository_factory,
        storage_service: Optional[StorageService] = None,
        logger=None,
    ):
        """
        Initialize the lecture service.

        Args:
            repository_factory: Repository factory instance
            storage_service: Optional storage service for lecture asset cleanup
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.storage_service = storage_service
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
        created_by: Optional[int] = None,
        created_with: Optional[str] = None,
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
            created_by: Optional ID of the student who created this lecture
            created_with: Optional AI model used to generate this lecture

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
            created_by=created_by,
            created_with=created_with,
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
        try:
            # Perform partial update to avoid overwriting concurrent changes
            updated_lecture = self.repository_factory.lecture.update_fields(lecture_id, update_data)
            self.logger.info(f"Updated lecture {lecture_id}")
            return updated_lecture
        except Exception as e:
            error_msg = f"Failed to update lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _get_storage_service(self) -> StorageService:
        if self.storage_service is None:
            self.storage_service = StorageService(logger=self.logger)
        return self.storage_service

    def _has_storage_assets(self, lecture: Lecture) -> bool:
        return any(
            getattr(lecture, field, None)
            for field in (
                "audio_url",
                "transcript_url",
                "timeline_url",
                "images_timeline_url",
            )
        )

    def _delete_storage_url(
        self,
        storage_service: StorageService,
        url: Optional[str],
        *,
        label: str,
        expected_bucket: Optional[str],
        deleted_objects: Set[Tuple[str, str]],
    ) -> bool:
        if not url:
            return False

        bucket, object_key = storage_service.parse_storage_url(url)
        if not bucket or not object_key:
            self.logger.warning(
                "Skipping unparseable %s URL during lecture cleanup: %s",
                label,
                url,
            )
            return False

        if expected_bucket and bucket != expected_bucket:
            self.logger.warning(
                "Skipping %s cleanup outside expected bucket %s: %s/%s",
                label,
                expected_bucket,
                bucket,
                object_key,
            )
            return False

        object_ref = (bucket, object_key)
        if object_ref in deleted_objects:
            return True

        deleted_objects.add(object_ref)
        deleted = storage_service.delete_file_sync(bucket, object_key)
        if not deleted:
            self.logger.warning(
                "Failed to delete %s object during lecture cleanup: %s/%s",
                label,
                bucket,
                object_key,
            )
        return deleted

    def _extract_images_timeline_urls(self, images_timeline: Dict[str, Any]) -> List[str]:
        urls: List[str] = []
        seen: Set[str] = set()
        for slot in images_timeline.get("slots") or []:
            url = slot.get("url") if isinstance(slot, dict) else None
            if not url or url in seen:
                continue
            seen.add(url)
            urls.append(str(url))
        return urls

    def _delete_lecture_image_assets(
        self,
        storage_service: StorageService,
        images_timeline_url: Optional[str],
        *,
        deleted_objects: Set[Tuple[str, str]],
    ) -> None:
        if not images_timeline_url:
            return

        bucket, object_key = storage_service.parse_storage_url(images_timeline_url)
        if not bucket or not object_key:
            self.logger.warning(
                "Skipping unparseable lecture images timeline URL: %s",
                images_timeline_url,
            )
            return

        if bucket != storage_service.lectures_bucket:
            self.logger.warning(
                "Skipping lecture images timeline lookup outside lectures bucket: %s/%s",
                bucket,
                object_key,
            )
            return

        file_data, _ = storage_service.download_file_sync(bucket, object_key)
        if not file_data:
            self.logger.warning(
                "Unable to load lecture images timeline during cleanup: %s/%s",
                bucket,
                object_key,
            )
            return

        try:
            images_timeline = json.loads(file_data.decode("utf-8"))
        except Exception as e:
            self.logger.warning(
                "Unable to parse lecture images timeline during cleanup: %s/%s: %s",
                bucket,
                object_key,
                e,
            )
            return

        for url in self._extract_images_timeline_urls(images_timeline):
            self._delete_storage_url(
                storage_service,
                url,
                label="lecture image",
                expected_bucket=storage_service.images_bucket,
                deleted_objects=deleted_objects,
            )

    def _delete_lecture_storage_assets(self, lecture: Lecture) -> None:
        if not self._has_storage_assets(lecture):
            return

        storage_service = self._get_storage_service()
        deleted_objects: Set[Tuple[str, str]] = set()

        # Read image URLs before deleting the images timeline JSON object.
        self._delete_lecture_image_assets(
            storage_service,
            lecture.images_timeline_url,
            deleted_objects=deleted_objects,
        )

        for label, url, expected_bucket in (
            ("lecture audio", lecture.audio_url, storage_service.audio_bucket),
            ("lecture transcript", lecture.transcript_url, storage_service.lectures_bucket),
            ("lecture timeline", lecture.timeline_url, storage_service.lectures_bucket),
            (
                "lecture images timeline",
                lecture.images_timeline_url,
                storage_service.lectures_bucket,
            ),
        ):
            self._delete_storage_url(
                storage_service,
                url,
                label=label,
                expected_bucket=expected_bucket,
                deleted_objects=deleted_objects,
            )

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
        # Check if lecture exists and keep its asset URLs for cleanup.
        lecture = self.get_lecture(lecture_id)

        try:
            try:
                self._delete_lecture_storage_assets(lecture)
            except Exception as e:
                self.logger.warning(
                    "Best-effort asset cleanup failed for lecture %s: %s",
                    lecture_id,
                    e,
                    exc_info=True,
                )

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
