"""
Job enqueueing service for ArtificialU.

This service provides a centralized way to enqueue background jobs,
avoiding duplication across different domain services.
"""

import logging
from typing import Optional

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
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)

    def enqueue_professor_image_generation(
        self,
        professor_id: int,
        aspect_ratio: str = "1:1",
        *,
        parent_job_id: Optional[int] = None,
    ) -> int:
        """Enqueue a background job to generate an image for the professor."""
        try:
            job = self.repository_factory.job.create(
                kind="generate_professor_image",
                payload={"professor_id": professor_id, "aspect_ratio": aspect_ratio},
                parent_job_id=parent_job_id,
            )
            self.logger.info(
                "Enqueued professor image generation job %d for professor %d",
                job.id,
                professor_id,
            )
            return job.id
        except Exception as e:
            error_msg = (
                f"Failed to enqueue professor image generation job "
                f"for professor {professor_id}: {e}"
            )
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def enqueue_course_image_generation(
        self,
        course_id: int,
        aspect_ratio: str = "1:1",
        *,
        parent_job_id: Optional[int] = None,
    ) -> int:
        """Enqueue a background job to generate album art for a course."""
        try:
            job = self.repository_factory.job.create(
                kind="generate_course_image",
                payload={"course_id": course_id, "aspect_ratio": aspect_ratio},
                parent_job_id=parent_job_id,
            )
            self.logger.info(
                "Enqueued course image generation job %d for course %d", job.id, course_id
            )
            return job.id
        except Exception as e:
            error_msg = f"Failed to enqueue course image generation job for course {course_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def enqueue_lecture_summary_generation(
        self,
        lecture_id: int,
        *,
        topic_id: Optional[int] = None,
        parent_job_id: Optional[int] = None,
    ) -> Optional[int]:
        """Enqueue a background job to generate a lecture summary."""
        if get_settings().testing:
            self.logger.debug("Skipping lecture summary job enqueue: running in test mode")
            return None

        try:
            payload: dict = {"lecture_id": lecture_id}
            if topic_id is not None:
                payload["topic_id"] = topic_id
            job = self.repository_factory.job.create(
                kind="generate_lecture_summary",
                payload=payload,
                parent_job_id=parent_job_id,
            )
            self.logger.info("Enqueued lecture summary job %d for lecture %d", job.id, lecture_id)
            return job.id
        except Exception as e:
            error_msg = f"Failed to enqueue lecture summary job for lecture {lecture_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def enqueue_lecture_audio_generation(
        self,
        lecture_id: int,
        *,
        topic_id: Optional[int] = None,
        parent_job_id: Optional[int] = None,
    ) -> Optional[int]:
        """Enqueue a background job to generate lecture audio."""
        if get_settings().testing:
            self.logger.debug("Skipping lecture audio job enqueue: running in test mode")
            return None

        try:
            payload: dict = {"lecture_id": lecture_id}
            if topic_id is not None:
                payload["topic_id"] = topic_id
            job = self.repository_factory.job.create(
                kind="generate_lecture_audio",
                payload=payload,
                parent_job_id=parent_job_id,
            )
            self.logger.info("Enqueued lecture audio job %d for lecture %d", job.id, lecture_id)
            return job.id
        except Exception as e:
            error_msg = f"Failed to enqueue lecture audio job for lecture {lecture_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def enqueue_lecture_timeline_generation(
        self,
        lecture_id: int,
        *,
        topic_id: Optional[int] = None,
        parent_job_id: Optional[int] = None,
    ) -> Optional[int]:
        """Enqueue a background job to generate a lecture timeline (forced alignment)."""
        if get_settings().testing:
            self.logger.debug("Skipping lecture timeline job enqueue: running in test mode")
            return None

        try:
            payload: dict = {"lecture_id": lecture_id}
            if topic_id is not None:
                payload["topic_id"] = topic_id
            job = self.repository_factory.job.create(
                kind="generate_lecture_timeline",
                payload=payload,
                parent_job_id=parent_job_id,
            )
            self.logger.info("Enqueued lecture timeline job %d for lecture %d", job.id, lecture_id)
            return job.id
        except Exception as e:
            error_msg = f"Failed to enqueue lecture timeline job for lecture {lecture_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def enqueue_lecture_images_generation(
        self,
        lecture_id: int,
        *,
        parent_job_id: Optional[int] = None,
    ) -> Optional[int]:
        """Enqueue a background job to generate a lecture images timeline + slide images."""
        if get_settings().testing:
            self.logger.debug("Skipping lecture images job enqueue: running in test mode")
            return None

        try:
            job = self.repository_factory.job.create(
                kind="generate_lecture_images",
                payload={"lecture_id": lecture_id},
                parent_job_id=parent_job_id,
            )
            self.logger.info("Enqueued lecture images job %d for lecture %d", job.id, lecture_id)
            return job.id
        except Exception as e:
            error_msg = f"Failed to enqueue lecture images job for lecture {lecture_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def enqueue_topics_generation(
        self,
        course_id: int,
        created_by: Optional[int] = None,
        *,
        parent_job_id: Optional[int] = None,
    ) -> Optional[int]:
        """Enqueue a background job to generate topics for a course."""
        if get_settings().testing:
            self.logger.debug("Skipping topics generation job enqueue: running in test mode")
            return None

        try:
            payload: dict = {"course_id": course_id}
            if created_by is not None:
                payload["created_by"] = created_by
            job = self.repository_factory.job.create(
                kind="generate_topics_for_course",
                payload=payload,
                parent_job_id=parent_job_id,
            )
            self.logger.info("Enqueued topics generation job %d for course %d", job.id, course_id)
            return job.id
        except Exception as e:
            error_msg = f"Failed to enqueue topics generation job for course {course_id}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e
