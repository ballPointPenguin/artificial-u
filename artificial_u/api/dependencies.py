"""
Dependency injection module for ArtificialU API.

This module provides FastAPI dependency functions for all services and repositories.
Each dependency is cached using FastAPI's dependency injection system to ensure
services are properly initialized and reused across requests.
"""

import logging
from typing import Optional

from fastapi import Depends

from artificial_u.api.config import get_settings
from artificial_u.api.services.course_service import CourseApiService
from artificial_u.api.services.department_service import DepartmentApiService
from artificial_u.api.services.lecture_service import LectureApiService
from artificial_u.api.services.professor_service import ProfessorApiService
from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services.content_service import ContentService
from artificial_u.services.course_service import CourseService
from artificial_u.services.department_service import DepartmentService
from artificial_u.services.image_service import ImageService
from artificial_u.services.lecture_service import LectureService
from artificial_u.services.professor_service import ProfessorService
from artificial_u.services.storage_service import StorageService
from artificial_u.services.voice_service import VoiceService


def get_repository_factory() -> RepositoryFactory:
    """
    Get a repository factory instance.

    Returns:
        RepositoryFactory instance
    """
    settings = get_settings()
    return RepositoryFactory(db_url=settings.DATABASE_URL)


def get_content_service() -> ContentService:
    """
    Get a content service instance.

    Returns:
        ContentService instance
    """
    return ContentService(
        logger=logging.getLogger("artificial_u.services.content_service"),
    )


def get_storage_service() -> StorageService:
    """
    Get a storage service instance.

    Returns:
        StorageService instance
    """
    return StorageService(
        logger=logging.getLogger("artificial_u.services.storage_service"),
    )


def get_image_service(
    storage_service: StorageService = Depends(get_storage_service),
) -> ImageService:
    """
    Get an image service instance.

    Args:
        storage_service: Storage service

    Returns:
        ImageService instance
    """
    return ImageService(
        storage_service=storage_service,
    )


def get_elevenlabs_client() -> Optional[ElevenLabsClient]:
    """
    Get an ElevenLabs client instance if configured.

    Returns:
        ElevenLabsClient instance if configured, None otherwise
    """
    settings = get_settings()
    if not settings.ELEVENLABS_API_KEY:
        return None

    return ElevenLabsClient(
        api_key=settings.ELEVENLABS_API_KEY,
    )


def get_voice_mapper() -> VoiceMapper:
    """
    Get a voice mapper instance

    Returns:
        VoiceMapper instance
    """
    return VoiceMapper(
        logger=logging.getLogger("artificial_u.integrations.elevenlabs.voice_mapper"),
    )


def get_voice_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    elevenlabs_client: Optional[ElevenLabsClient] = Depends(get_elevenlabs_client),
) -> VoiceService:
    """
    Get a voice service instance.

    Args:
        repository_factory: Repository factory instance
        elevenlabs_client: ElevenLabs client (optional)

    Returns:
        VoiceService instance
    """
    return VoiceService(
        repository_factory=repository_factory,
        client=elevenlabs_client,
        logger=logging.getLogger("artificial_u.services.voice_service"),
    )


def get_professor_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    content_service: ContentService = Depends(get_content_service),
    image_service: ImageService = Depends(get_image_service),
    voice_service: VoiceService = Depends(get_voice_service),
) -> ProfessorService:
    """
    Get a professor service instance.

    Args:
        repository_factory: Repository factory
        content_service: Content service
        image_service: Image service
        voice_service: Voice service

    Returns:
        ProfessorService instance
    """
    return ProfessorService(
        repository_factory=repository_factory,
        content_service=content_service,
        image_service=image_service,
        voice_service=voice_service,
        logger=logging.getLogger("artificial_u.services.professor_service"),
    )


def get_course_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    content_service: ContentService = Depends(get_content_service),
    professor_service: ProfessorService = Depends(get_professor_service),
) -> CourseService:
    """
    Get a course service instance.

    Args:
        repository_factory: Repository factory
        content_service: Content service
        professor_service: Professor service

    Returns:
        CourseService instance
    """
    return CourseService(
        repository_factory=repository_factory,
        content_service=content_service,
        professor_service=professor_service,
        logger=logging.getLogger("artificial_u.services.course_service"),
    )


def get_department_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
) -> DepartmentService:
    """
    Get a department service instance.

    Args:
        repository_factory: Repository factory
        professor_service: Professor service
        course_service: Course service

    Returns:
        DepartmentService instance
    """
    return DepartmentService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        course_service=course_service,
        logger=logging.getLogger("artificial_u.services.department_service"),
    )


def get_lecture_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
    content_service: ContentService = Depends(get_content_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> LectureService:
    """
    Get a lecture service instance.

    Args:
        repository_factory: Repository factory
        professor_service: Professor service
        course_service: Course service
        content_service: Content service
        storage_service: Storage service

    Returns:
        LectureService instance
    """
    return LectureService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        course_service=course_service,
        content_service=content_service,
        storage_service=storage_service,
        logger=logging.getLogger("artificial_u.services.lecture_service"),
    )


def get_professor_api_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    content_service: ContentService = Depends(get_content_service),
    image_service: ImageService = Depends(get_image_service),
    voice_service: VoiceService = Depends(get_voice_service),
) -> ProfessorApiService:
    """
    Get a professor API service instance.

    Args:
        repository_factory: Repository factory
        content_service: Content service
        image_service: Image service
        voice_service: Voice service

    Returns:
        ProfessorApiService instance
    """
    return ProfessorApiService(
        repository_factory=repository_factory,
        content_service=content_service,
        image_service=image_service,
        voice_service=voice_service,
        logger=logging.getLogger("artificial_u.api.services.professor_service"),
    )


def get_course_api_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    content_service: ContentService = Depends(get_content_service),
    professor_service: ProfessorService = Depends(get_professor_service),
) -> CourseApiService:
    """
    Get a course API service instance.

    Args:
        repository_factory: Repository factory
        professor_service: Professor service

    Returns:
        CourseApiService instance
    """
    return CourseApiService(
        repository_factory=repository_factory,
        content_service=content_service,
        professor_service=professor_service,
        logger=logging.getLogger("artificial_u.api.services.course_service"),
    )


def get_department_api_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
) -> DepartmentApiService:
    """
    Get a department API service instance.

    Args:
        repository_factory: Repository factory
        professor_service: Professor service
        course_service: Course service

    Returns:
        DepartmentApiService instance
    """
    return DepartmentApiService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        course_service=course_service,
        logger=logging.getLogger("artificial_u.api.services.department_service"),
    )


def get_lecture_api_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
    content_service: ContentService = Depends(get_content_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> LectureApiService:
    """
    Get a lecture API service instance.

    Args:
        repository_factory: Repository factory
        professor_service: Professor service
        content_service: Content service
        course_service: Course service
        storage_service: Storage service

    Returns:
        LectureApiService instance
    """
    return LectureApiService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        course_service=course_service,
        content_service=content_service,
        storage_service=storage_service,
        logger=logging.getLogger("artificial_u.api.services.lecture_service"),
    )
