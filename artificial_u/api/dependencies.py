"""
Dependency injection module for ArtificialU API.

This module provides FastAPI dependency functions for all services and repositories.
Each dependency is cached using FastAPI's dependency injection system to ensure
services are properly initialized and reused across requests.
"""

import logging
from functools import lru_cache
from typing import Optional

from fastapi import Depends

from artificial_u.api.config import Settings, get_settings
from artificial_u.api.services.course_service import CourseApiService
from artificial_u.api.services.department_service import DepartmentApiService
from artificial_u.api.services.lecture_service import LectureApiService
from artificial_u.api.services.professor_service import ProfessorApiService
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services.content_service import ContentService
from artificial_u.services.course_service import CourseService
from artificial_u.services.department_service import DepartmentService
from artificial_u.services.image_service import ImageService
from artificial_u.services.lecture_service import LectureService
from artificial_u.services.professor_service import ProfessorService
from artificial_u.services.storage_service import StorageService
from artificial_u.services.voice_service import VoiceService


@lru_cache()
def get_repository(settings: Settings = Depends(get_settings)) -> RepositoryFactory:
    """
    Get a repository factory instance.

    Args:
        settings: Application settings

    Returns:
        RepositoryFactory instance
    """
    return RepositoryFactory(db_url=settings.DATABASE_URL)


@lru_cache()
def get_content_service(
    settings: Settings = Depends(get_settings),
    repository: RepositoryFactory = Depends(get_repository),
) -> ContentService:
    """
    Get a content service instance.

    Args:
        settings: Application settings
        repository: Repository factory

    Returns:
        ContentService instance
    """
    return ContentService(
        repository=repository,
        api_key=settings.OPENAI_API_KEY,
        logger=logging.getLogger("artificial_u.services.content_service"),
    )


@lru_cache()
def get_image_service(
    settings: Settings = Depends(get_settings),
    repository: RepositoryFactory = Depends(get_repository),
) -> ImageService:
    """
    Get an image service instance.

    Args:
        settings: Application settings
        repository: Repository factory

    Returns:
        ImageService instance
    """
    return ImageService(
        repository=repository,
        api_key=settings.OPENAI_API_KEY,
        logger=logging.getLogger("artificial_u.services.image_service"),
    )


@lru_cache()
def get_voice_service(
    settings: Settings = Depends(get_settings),
    repository: RepositoryFactory = Depends(get_repository),
) -> Optional[VoiceService]:
    """
    Get a voice service instance if configured.

    Args:
        settings: Application settings
        repository: Repository factory

    Returns:
        VoiceService instance if configured, None otherwise
    """
    if not settings.ELEVENLABS_API_KEY:
        return None

    return VoiceService(
        repository=repository,
        api_key=settings.ELEVENLABS_API_KEY,
        logger=logging.getLogger("artificial_u.services.voice_service"),
    )


@lru_cache()
def get_storage_service(
    settings: Settings = Depends(get_settings),
) -> StorageService:
    """
    Get a storage service instance.

    Args:
        settings: Application settings

    Returns:
        StorageService instance
    """
    return StorageService(
        storage_path=settings.STORAGE_PATH,
        logger=logging.getLogger("artificial_u.services.storage_service"),
    )


@lru_cache()
def get_professor_service(
    repository: RepositoryFactory = Depends(get_repository),
    content_service: ContentService = Depends(get_content_service),
    image_service: ImageService = Depends(get_image_service),
    voice_service: Optional[VoiceService] = Depends(get_voice_service),
) -> ProfessorService:
    """
    Get a professor service instance.

    Args:
        repository: Repository factory
        content_service: Content service
        image_service: Image service
        voice_service: Voice service (optional)

    Returns:
        ProfessorService instance
    """
    return ProfessorService(
        repository=repository,
        content_service=content_service,
        image_service=image_service,
        voice_service=voice_service,
        logger=logging.getLogger("artificial_u.services.professor_service"),
    )


@lru_cache()
def get_course_service(
    repository: RepositoryFactory = Depends(get_repository),
    professor_service: ProfessorService = Depends(get_professor_service),
) -> CourseService:
    """
    Get a course service instance.

    Args:
        repository: Repository factory
        professor_service: Professor service

    Returns:
        CourseService instance
    """
    return CourseService(
        repository=repository,
        professor_service=professor_service,
        logger=logging.getLogger("artificial_u.services.course_service"),
    )


@lru_cache()
def get_department_service(
    repository: RepositoryFactory = Depends(get_repository),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
) -> DepartmentService:
    """
    Get a department service instance.

    Args:
        repository: Repository factory
        professor_service: Professor service
        course_service: Course service

    Returns:
        DepartmentService instance
    """
    return DepartmentService(
        repository=repository,
        professor_service=professor_service,
        course_service=course_service,
        logger=logging.getLogger("artificial_u.services.department_service"),
    )


@lru_cache()
def get_lecture_service(
    repository: RepositoryFactory = Depends(get_repository),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
    content_service: ContentService = Depends(get_content_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> LectureService:
    """
    Get a lecture service instance.

    Args:
        repository: Repository factory
        professor_service: Professor service
        course_service: Course service
        content_service: Content service
        storage_service: Storage service

    Returns:
        LectureService instance
    """
    return LectureService(
        repository=repository,
        professor_service=professor_service,
        course_service=course_service,
        content_service=content_service,
        storage_service=storage_service,
        logger=logging.getLogger("artificial_u.services.lecture_service"),
    )


@lru_cache()
def get_professor_api_service(
    repository: RepositoryFactory = Depends(get_repository),
    content_service: ContentService = Depends(get_content_service),
    image_service: ImageService = Depends(get_image_service),
    voice_service: Optional[VoiceService] = Depends(get_voice_service),
) -> ProfessorApiService:
    """
    Get a professor API service instance.

    Args:
        repository: Repository factory
        content_service: Content service
        image_service: Image service
        voice_service: Voice service (optional)

    Returns:
        ProfessorApiService instance
    """
    return ProfessorApiService(
        repository=repository,
        content_service=content_service,
        image_service=image_service,
        voice_service=voice_service,
    )


@lru_cache()
def get_course_api_service(
    repository: RepositoryFactory = Depends(get_repository),
    professor_service: ProfessorService = Depends(get_professor_service),
) -> CourseApiService:
    """
    Get a course API service instance.

    Args:
        repository: Repository factory
        professor_service: Professor service

    Returns:
        CourseApiService instance
    """
    return CourseApiService(
        repository=repository,
        professor_service=professor_service,
    )


@lru_cache()
def get_department_api_service(
    repository: RepositoryFactory = Depends(get_repository),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
) -> DepartmentApiService:
    """
    Get a department API service instance.

    Args:
        repository: Repository factory
        professor_service: Professor service
        course_service: Course service

    Returns:
        DepartmentApiService instance
    """
    return DepartmentApiService(
        repository=repository,
        professor_service=professor_service,
        course_service=course_service,
    )


@lru_cache()
def get_lecture_api_service(
    repository: RepositoryFactory = Depends(get_repository),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
    content_service: ContentService = Depends(get_content_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> LectureApiService:
    """
    Get a lecture API service instance.

    Args:
        repository: Repository factory
        professor_service: Professor service
        course_service: Course service
        content_service: Content service
        storage_service: Storage service

    Returns:
        LectureApiService instance
    """
    return LectureApiService(
        repository=repository,
        professor_service=professor_service,
        course_service=course_service,
        content_service=content_service,
        storage_service=storage_service,
    )
