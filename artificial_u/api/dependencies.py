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
from artificial_u.api.services import (
    CourseApiService,
    DepartmentApiService,
    LectureApiService,
    ProfessorApiService,
    TopicApiService,
)
from artificial_u.integrations import elevenlabs
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import (
    ContentService,
    CourseService,
    DepartmentSelectorService,
    DepartmentService,
    ImageService,
    LectureService,
    ProfessorSelectorService,
    ProfessorService,
    StorageService,
    TopicService,
    VoiceService,
)
from artificial_u.services.job_enqueue_service import JobEnqueueService


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


def get_elevenlabs_client() -> Optional[elevenlabs.ElevenLabsClient]:
    """
    Get an ElevenLabs client instance if configured.

    Returns:
        ElevenLabsClient instance if configured, None otherwise
    """
    settings = get_settings()
    if not settings.ELEVENLABS_API_KEY:
        return None

    return elevenlabs.ElevenLabsClient(
        api_key=settings.ELEVENLABS_API_KEY,
    )


def get_voice_mapper() -> elevenlabs.VoiceMapper:
    """
    Get a voice mapper instance

    Returns:
        VoiceMapper instance
    """
    return elevenlabs.VoiceMapper(
        logger=logging.getLogger("artificial_u.integrations.elevenlabs.voice_mapper"),
    )


def get_voice_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    elevenlabs_client: Optional[elevenlabs.ElevenLabsClient] = Depends(get_elevenlabs_client),
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


def get_job_enqueue_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
) -> JobEnqueueService:
    """
    Get a job enqueue service instance.

    Args:
        repository_factory: Repository factory instance

    Returns:
        JobEnqueueService instance
    """
    return JobEnqueueService(
        repository_factory=repository_factory,
        logger=logging.getLogger("artificial_u.services.job_enqueue_service"),
    )


def get_professor_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    voice_service: VoiceService = Depends(get_voice_service),
    job_enqueue_service: JobEnqueueService = Depends(get_job_enqueue_service),
) -> ProfessorService:
    """
    Get a professor service instance.

    Args:
        repository_factory: Repository factory
        voice_service: Voice service
        job_enqueue_service: Job enqueueing service

    Returns:
        ProfessorService instance
    """
    return ProfessorService(
        repository_factory=repository_factory,
        voice_service=voice_service,
        job_enqueue_service=job_enqueue_service,
        logger=logging.getLogger("artificial_u.services.professor_service"),
    )


def get_course_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    professor_service: ProfessorService = Depends(get_professor_service),
) -> CourseService:
    """
    Get a course service instance.

    Args:
        repository_factory: Repository factory
        professor_service: Professor service

    Returns:
        CourseService instance
    """
    # Create selector services inline to avoid circular dependencies
    content_service = get_content_service()

    # Get generator services
    department_generator_service = get_department_generator_service(
        repository_factory, content_service, get_job_enqueue_service(repository_factory)
    )
    professor_generator_service = get_professor_generator_service(
        repository_factory,
        content_service,
        get_image_service(get_storage_service()),
        get_job_enqueue_service(repository_factory),
    )

    # Create selector services
    department_selector_service = DepartmentSelectorService(
        content_service=content_service,
        repository_factory=repository_factory,
        department_generator_service=department_generator_service,
        logger=logging.getLogger("artificial_u.services.department_selector_service"),
    )

    professor_selector_service = ProfessorSelectorService(
        content_service=content_service,
        repository_factory=repository_factory,
        professor_generator_service=professor_generator_service,
        professor_service=professor_service,
        logger=logging.getLogger("artificial_u.services.professor_selector_service"),
    )

    return CourseService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        department_selector_service=department_selector_service,
        professor_selector_service=professor_selector_service,
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
) -> LectureService:
    """
    Get a lecture service instance.

    Args:
        repository_factory: Repository factory

    Returns:
        LectureService instance
    """
    return LectureService(
        repository_factory=repository_factory,
        logger=logging.getLogger("artificial_u.services.lecture_service"),
    )


def get_topic_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
) -> TopicService:
    """
    Get a core TopicService instance.

    Args:
        repository_factory: Repository factory

    Returns:
        TopicService instance
    """
    return TopicService(
        repository_factory=repository_factory,
        logger=logging.getLogger("artificial_u.services.topic_service"),
    )


def get_department_generator_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    content_service: ContentService = Depends(get_content_service),
    job_enqueue_service: JobEnqueueService = Depends(get_job_enqueue_service),
):
    """
    Get a department generator service instance.

    Args:
        repository_factory: Repository factory
        content_service: Content service
        job_enqueue_service: Job enqueue service

    Returns:
        DepartmentGeneratorService instance
    """
    from artificial_u.services.department_generator_service import DepartmentGeneratorService
    from artificial_u.services.department_service import DepartmentService

    department_service = DepartmentService(
        repository_factory=repository_factory,
        professor_service=None,  # Not needed for generation
        course_service=None,  # Not needed for generation
        logger=logging.getLogger("artificial_u.services.department_service"),
    )

    return DepartmentGeneratorService(
        department_service=department_service,
        content_service=content_service,
        repository_factory=repository_factory,
        job_enqueue_service=job_enqueue_service,
        logger=logging.getLogger("artificial_u.services.department_generator_service"),
    )


def get_professor_generator_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    content_service: ContentService = Depends(get_content_service),
    image_service: ImageService = Depends(get_image_service),
    job_enqueue_service: JobEnqueueService = Depends(get_job_enqueue_service),
):
    """
    Get a professor generator service instance.

    Args:
        repository_factory: Repository factory
        content_service: Content service
        image_service: Image service
        job_enqueue_service: Job enqueue service

    Returns:
        ProfessorGeneratorService instance
    """
    from artificial_u.services.professor_generator_service import ProfessorGeneratorService

    # We need the core professor service for generation, but it depends on voice_service
    # We'll get it via dependency injection
    professor_service = get_professor_service(
        repository_factory=repository_factory,
        voice_service=get_voice_service(repository_factory, get_elevenlabs_client()),
        job_enqueue_service=job_enqueue_service,
    )

    return ProfessorGeneratorService(
        professor_service=professor_service,
        content_service=content_service,
        image_service=image_service,
        repository_factory=repository_factory,
        job_enqueue_service=job_enqueue_service,
        logger=logging.getLogger("artificial_u.services.professor_generator_service"),
    )


def get_department_selector_service(
    content_service: ContentService = Depends(get_content_service),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    department_generator_service=Depends(get_department_generator_service),
) -> DepartmentSelectorService:
    """
    Get a department selector service instance.

    Args:
        content_service: Content service
        repository_factory: Repository factory
        department_generator_service: Department generator service

    Returns:
        DepartmentSelectorService instance
    """
    return DepartmentSelectorService(
        content_service=content_service,
        repository_factory=repository_factory,
        department_generator_service=department_generator_service,
        logger=logging.getLogger("artificial_u.services.department_selector_service"),
    )


def get_professor_selector_service(
    content_service: ContentService = Depends(get_content_service),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    professor_generator_service=Depends(get_professor_generator_service),
    professor_service: ProfessorService = Depends(get_professor_service),
) -> ProfessorSelectorService:
    """
    Get a professor selector service instance.

    Args:
        content_service: Content service
        repository_factory: Repository factory
        professor_generator_service: Professor generator service
        professor_service: Professor service (for creating generated professors)

    Returns:
        ProfessorSelectorService instance
    """
    return ProfessorSelectorService(
        content_service=content_service,
        repository_factory=repository_factory,
        professor_generator_service=professor_generator_service,
        professor_service=professor_service,
        logger=logging.getLogger("artificial_u.services.professor_selector_service"),
    )


def get_professor_api_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    content_service: ContentService = Depends(get_content_service),
    image_service: ImageService = Depends(get_image_service),
    voice_service: VoiceService = Depends(get_voice_service),
    logger=logging.getLogger("artificial_u.api.services.lecture_service"),
) -> ProfessorApiService:
    """
    Get a professor API service instance.

    Args:
        repository_factory: Repository factory
        content_service: Content service
        image_service: Image service
        voice_service: Voice service
        logger: Logger for the service

    Returns:
        ProfessorApiService instance
    """
    return ProfessorApiService(
        repository_factory=repository_factory,
        content_service=content_service,
        image_service=image_service,
        voice_service=voice_service,
        logger=logger,
    )


def get_course_api_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    content_service: ContentService = Depends(get_content_service),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
) -> CourseApiService:
    """
    Get a course API service instance.

    Args:
        repository_factory: Repository factory
        content_service: Content service
        professor_service: Professor service
        course_service: Core course service with smart selection

    Returns:
        CourseApiService instance
    """
    return CourseApiService(
        repository_factory=repository_factory,
        content_service=content_service,
        professor_service=professor_service,
        course_service=course_service,
        logger=logging.getLogger("artificial_u.api.services.course_service"),
    )


def get_department_api_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
    content_service: ContentService = Depends(get_content_service),
) -> DepartmentApiService:
    """
    Get a department API service instance.

    Args:
        repository_factory: Repository factory
        professor_service: Professor service
        course_service: Course service
        content_service: Content service

    Returns:
        DepartmentApiService instance
    """
    return DepartmentApiService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        course_service=course_service,
        content_service=content_service,
        logger=logging.getLogger("artificial_u.api.services.department_service"),
    )


def get_lecture_api_service(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    professor_service: ProfessorService = Depends(get_professor_service),
    course_service: CourseService = Depends(get_course_service),
    content_service: ContentService = Depends(get_content_service),
    storage_service: StorageService = Depends(get_storage_service),
    topic_service: TopicService = Depends(get_topic_service),
) -> LectureApiService:
    """
    Get a lecture API service instance.

    Args:
        repository_factory: Repository factory
        professor_service: Professor service
        course_service: Course service
        content_service: Content service
        storage_service: Storage service
        topic_service: Topic service

    Returns:
        LectureApiService instance
    """
    return LectureApiService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        course_service=course_service,
        content_service=content_service,
        storage_service=storage_service,
        topic_service=topic_service,
        logger=logging.getLogger("artificial_u.api.services.lecture_service"),
    )


def get_topic_api_service(
    core_topic_service: TopicService = Depends(get_topic_service),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    course_service: CourseService = Depends(get_course_service),
) -> TopicApiService:
    """
    Get a Topic API service instance.

    Args:
        core_topic_service: Core TopicService instance
        repository_factory: Repository factory
        course_service: Course service with smart selection

    Returns:
        TopicApiService instance
    """
    return TopicApiService(
        core_topic_service=core_topic_service,
        repository_factory=repository_factory,
        course_service=course_service,
        logger=logging.getLogger("artificial_u.api.services.topic_service"),
    )
