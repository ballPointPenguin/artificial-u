"""
Services module for ArtificialU.

This module provides service-layer abstractions for core functionality.
"""

import logging
import os
import sys

from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper
from artificial_u.services.audio_service import AudioService
from artificial_u.services.content_service import ContentService
from artificial_u.services.course_service import CourseService
from artificial_u.services.image_service import ImageService
from artificial_u.services.lecture_service import LectureService
from artificial_u.services.professor_service import ProfessorService
from artificial_u.services.storage_service import StorageService
from artificial_u.services.tts_service import TTSService

__all__ = [
    "ProfessorService",
    "CourseService",
    "LectureService",
    "AudioService",
    "TTSService",
    "StorageService",
    "ImageService",
    "ContentService",
    "VoiceMapper",
    "ElevenLabsClient",
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

        # Initialize basic components
        db_repository = RepositoryFactory()

        # Initialize elevenlabs client and voice mapper
        elevenlabs_client = ElevenLabsClient()
        voice_mapper = VoiceMapper(client=elevenlabs_client)

        logger.info("Initialized production services")
    except Exception as e:
        logger.warning(f"Error initializing services: {e}")
        db_repository = None
        voice_mapper = None
else:
    # In test environment, don't initialize real services
    logger.info("In test environment - not initializing real services")
    db_repository = None
    voice_mapper = None
