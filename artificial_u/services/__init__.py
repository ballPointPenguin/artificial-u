"""
Services module for ArtificialU.

This module provides service-layer abstractions for core functionality.
"""

import logging
import os
import sys

from artificial_u.services.audio_service import AudioService
from artificial_u.services.content_service import ContentService
from artificial_u.services.course_service import CourseService
from artificial_u.services.image_service import ImageService
from artificial_u.services.lecture_service import LectureService
from artificial_u.services.professor_service import ProfessorService
from artificial_u.services.storage_service import StorageService
from artificial_u.services.tts_service import TTSService
from artificial_u.services.voice_service import VoiceService

__all__ = [
    "ProfessorService",
    "CourseService",
    "LectureService",
    "AudioService",
    "VoiceService",
    "TTSService",
    "StorageService",
    "ImageService",
    "ContentService",
]

logger = logging.getLogger(__name__)


# Check if we're running in a test environment
def is_test_environment() -> bool:
    """Check if we're running in a test environment."""
    return os.environ.get("TESTING") == "true" or "pytest" in sys.modules


# Only import actual implementations if we're not in a unit test
# This avoids database connection issues during unit tests
if not is_test_environment():
    try:
        from artificial_u.models.repositories import RepositoryFactory

        # Initialize services
        db_repository = RepositoryFactory()
        voice_service = VoiceService(repository=db_repository)

        logger.info("Initialized production services")
    except Exception as e:
        logger.warning(f"Error initializing services: {e}")
        db_repository = None
        voice_service = None
else:
    # In test environment, don't initialize real services
    logger.info("In test environment - not initializing real services")
    db_repository = None
    voice_service = None
