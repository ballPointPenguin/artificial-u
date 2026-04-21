"""
Job enqueueing service for ArtificialU.

This service provides a centralized way to enqueue background jobs,
avoiding duplication across different domain services.
"""

import logging

from artificial_u.config import get_settings
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.utils import DatabaseError


class JobEnqueueService:
    """Service for enqueueing background processing jobs."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        logger=None,
    ):
        """
        Initialize the job enqueue service.

        Args:
            repository_factory: Repository factory instance
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)

    def enqueue_professor_image_generation(
        self, professor_id: int, aspect_ratio: str = "1:1"
    ) -> None:
        """
        Enqueue a background job to generate an image for the professor.

        Args:
            professor_id: The ID of the professor
            aspect_ratio: The desired aspect ratio for the image

        Raises:
            DatabaseError: If job enqueueing fails
        """
        try:
            job_repo = self.repository_factory.job
            job = job_repo.create(
                kind="generate_professor_image",
                payload={
                    "professor_id": professor_id,
                    "aspect_ratio": aspect_ratio,
                },
            )
            job_id = job.id
            self.logger.info(
                f"Enqueued professor image generation job {job_id} for professor {professor_id}"
            )
        except Exception as e:
            error_msg = (
                f"Failed to enqueue professor image generation job "
                f"for professor {professor_id}: {e}"
            )
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def enqueue_lecture_summary_generation(
        self, lecture_id: int, *, topic_id: int | None = None
    ) -> None:
        """
        Enqueue a background job to generate a lecture summary.

        Args:
            lecture_id: The ID of the lecture

        Raises:
            DatabaseError: If job enqueueing fails
        """
        if get_settings().testing:
            self.logger.debug("Skipping lecture summary job enqueue: running in test mode")
            return

        try:
            job_repo = self.repository_factory.job
            payload = {"lecture_id": lecture_id}
            if topic_id is not None:
                payload["topic_id"] = topic_id
            job = job_repo.create(kind="generate_lecture_summary", payload=payload)
            job_id = job.id
            self.logger.info(f"Enqueued lecture summary job {job_id} for lecture {lecture_id}")
        except Exception as e:
            error_msg = f"Failed to enqueue lecture summary job for lecture {lecture_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def enqueue_lecture_audio_generation(
        self, lecture_id: int, *, topic_id: int | None = None
    ) -> None:
        """
        Enqueue a background job to generate lecture audio.

        Args:
            lecture_id: The ID of the lecture

        Raises:
            DatabaseError: If job enqueueing fails
        """
        if get_settings().testing:
            self.logger.debug("Skipping lecture audio job enqueue: running in test mode")
            return

        try:
            job_repo = self.repository_factory.job
            payload = {"lecture_id": lecture_id}
            if topic_id is not None:
                payload["topic_id"] = topic_id
            job = job_repo.create(kind="generate_lecture_audio", payload=payload)
            job_id = job.id
            self.logger.info(f"Enqueued lecture audio job {job_id} for lecture {lecture_id}")
        except Exception as e:
            error_msg = f"Failed to enqueue lecture audio job for lecture {lecture_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def enqueue_lecture_timeline_generation(
        self, lecture_id: int, *, topic_id: int | None = None
    ) -> None:
        """
        Enqueue a background job to generate a lecture timeline (forced alignment).

        Args:
            lecture_id: The ID of the lecture

        Raises:
            DatabaseError: If job enqueueing fails
        """
        if get_settings().testing:
            self.logger.debug("Skipping lecture timeline job enqueue: running in test mode")
            return

        try:
            job_repo = self.repository_factory.job
            payload = {"lecture_id": lecture_id}
            if topic_id is not None:
                payload["topic_id"] = topic_id
            job = job_repo.create(kind="generate_lecture_timeline", payload=payload)
            job_id = job.id
            self.logger.info(f"Enqueued lecture timeline job {job_id} for lecture {lecture_id}")
        except Exception as e:
            error_msg = f"Failed to enqueue lecture timeline job for lecture {lecture_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def enqueue_topics_generation(self, course_id: int, created_by: int = None) -> None:
        """
        Enqueue a background job to generate topics for a course.

        Args:
            course_id: The ID of the course
            created_by: Optional student ID who triggered the generation

        Raises:
            DatabaseError: If job enqueueing fails
        """
        if get_settings().testing:
            self.logger.debug("Skipping topics generation job enqueue: running in test mode")
            return

        try:
            job_repo = self.repository_factory.job
            payload = {"course_id": course_id}
            if created_by is not None:
                payload["created_by"] = created_by
            job = job_repo.create(
                kind="generate_topics_for_course",
                payload=payload,
            )
            job_id = job.id
            self.logger.info(f"Enqueued topics generation job {job_id} for course {course_id}")
        except Exception as e:
            error_msg = f"Failed to enqueue topics generation job for course {course_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e
