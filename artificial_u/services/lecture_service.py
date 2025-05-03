"""
Lecture management service for ArtificialU.
"""

import logging


class LectureService:
    """Service for managing lecture entities."""

    def __init__(
        self,
        content_service,
        course_service,
        professor_service,
        repository_factory,
        logger=None,
    ):
        """
        Initialize the lecture service.

        Args:
            content_service: Content generation service
            course_service: Course management service
            professor_service: Professor management service
            repository_factory: Repository factory instance
            logger: Optional logger instance
        """
        self.content_service = content_service
        self.course_service = course_service
        self.professor_service = professor_service
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)
