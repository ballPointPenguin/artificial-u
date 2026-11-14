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

    def _enqueue(
        self,
        kind: str,
        payload: dict,
        *,
        label: str,
        subject: str,
        parent_job_id: Optional[int] = None,
    ) -> int:
        """Create a job row and return its ID. ``None`` payload values are dropped."""
        try:
            job = self.repository_factory.job.create(
                kind=kind,
                payload={key: value for key, value in payload.items() if value is not None},
                parent_job_id=parent_job_id,
            )
        except Exception as e:
            error_msg = f"Failed to enqueue {label} job for {subject}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

        self.logger.info("Enqueued %s job %d for %s", label, job.id, subject)
        return job.id

    def enqueue_professor_image_generation(
        self,
        professor_id: int,
        aspect_ratio: str = "1:1",
        *,
        parent_job_id: Optional[int] = None,
    ) -> int:
        """Enqueue a background job to generate an image for the professor."""
        return self._enqueue(
            "generate_professor_image",
            {"professor_id": professor_id, "aspect_ratio": aspect_ratio},
            label="professor image generation",
            subject=f"professor {professor_id}",
            parent_job_id=parent_job_id,
        )

    def enqueue_course_image_generation(
        self,
        course_id: int,
        aspect_ratio: str = "1:1",
        *,
        parent_job_id: Optional[int] = None,
    ) -> int:
        """Enqueue a background job to generate album art for a course."""
        return self._enqueue(
            "generate_course_image",
            {"course_id": course_id, "aspect_ratio": aspect_ratio},
            label="course image generation",
            subject=f"course {course_id}",
            parent_job_id=parent_job_id,
        )

    def enqueue_lecture_summary_generation(
        self,
        lecture_id: int,
        *,
        topic_id: Optional[int] = None,
        parent_job_id: Optional[int] = None,
    ) -> Optional[int]:
        """Enqueue a background job to generate a lecture summary."""
        return self._enqueue_for_lecture(
            "generate_lecture_summary", "lecture summary", lecture_id, topic_id, parent_job_id
        )

    def enqueue_lecture_audio_generation(
        self,
        lecture_id: int,
        *,
        topic_id: Optional[int] = None,
        parent_job_id: Optional[int] = None,
    ) -> Optional[int]:
        """Enqueue a background job to generate lecture audio."""
        return self._enqueue_for_lecture(
            "generate_lecture_audio", "lecture audio", lecture_id, topic_id, parent_job_id
        )

    def enqueue_lecture_timeline_generation(
        self,
        lecture_id: int,
        *,
        topic_id: Optional[int] = None,
        parent_job_id: Optional[int] = None,
    ) -> Optional[int]:
        """Enqueue a background job to generate a lecture timeline (forced alignment)."""
        return self._enqueue_for_lecture(
            "generate_lecture_timeline", "lecture timeline", lecture_id, topic_id, parent_job_id
        )

    def enqueue_tags_generation(
        self,
        course_id: int,
        created_by: Optional[int] = None,
        *,
        parent_job_id: Optional[int] = None,
    ) -> Optional[int]:
        """Enqueue a background job to generate tags for a course."""
        return self._enqueue_for_course(
            "generate_tags_for_course", "tags generation", course_id, created_by, parent_job_id
        )

    def enqueue_topics_generation(
        self,
        course_id: int,
        created_by: Optional[int] = None,
        *,
        parent_job_id: Optional[int] = None,
    ) -> Optional[int]:
        """Enqueue a background job to generate topics for a course."""
        return self._enqueue_for_course(
            "generate_topics_for_course", "topics generation", course_id, created_by, parent_job_id
        )

    def _enqueue_for_lecture(
        self,
        kind: str,
        label: str,
        lecture_id: int,
        topic_id: Optional[int],
        parent_job_id: Optional[int],
    ) -> Optional[int]:
        if self._skip_in_tests(label):
            return None
        return self._enqueue(
            kind,
            {"lecture_id": lecture_id, "topic_id": topic_id},
            label=label,
            subject=f"lecture {lecture_id}",
            parent_job_id=parent_job_id,
        )

    def _enqueue_for_course(
        self,
        kind: str,
        label: str,
        course_id: int,
        created_by: Optional[int],
        parent_job_id: Optional[int],
    ) -> Optional[int]:
        if self._skip_in_tests(label):
            return None
        return self._enqueue(
            kind,
            {"course_id": course_id, "created_by": created_by},
            label=label,
            subject=f"course {course_id}",
            parent_job_id=parent_job_id,
        )

    def _skip_in_tests(self, label: str) -> bool:
        """Follow-up jobs for lectures and courses are not enqueued in test mode."""
        if get_settings().testing:
            self.logger.debug("Skipping %s job enqueue: running in test mode", label)
            return True
        return False
