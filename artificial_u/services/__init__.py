"""
Services module for ArtificialU.

This module provides service-layer abstractions for core functionality.
Each service is responsible for managing its own dependencies and external
service connections. Services should be instantiated through the dependency
injection system rather than using global state.
"""

from artificial_u.services.audio_service import AudioService
from artificial_u.services.content_service import ContentService
from artificial_u.services.course_service import CourseService
from artificial_u.services.department_service import DepartmentService
from artificial_u.services.image_service import ImageService
from artificial_u.services.lecture_service import LectureService
from artificial_u.services.professor_service import ProfessorService
from artificial_u.services.storage_service import StorageService
from artificial_u.services.topic_service import TopicService
from artificial_u.services.tts_service import TTSService
from artificial_u.services.voice_service import VoiceService

__all__ = [
    # Content generation services
    "ContentService",
    "ImageService",
    "TTSService",
    "VoiceService",
    # Domain services
    "CourseService",
    "DepartmentService",
    "LectureService",
    "ProfessorService",
    "TopicService",
    # Infrastructure services
    "AudioService",
    "StorageService",
]
