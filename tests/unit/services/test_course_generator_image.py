"""Unit tests for course album art generation orchestration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.models.core import Course
from artificial_u.services.course_generator_service import CourseGeneratorService
from artificial_u.services.image_service import ImageGenerationResult
from artificial_u.utils import GenerationError


@pytest.mark.asyncio
async def test_generate_and_set_course_image_updates_course(monkeypatch):
    course = Course(
        id=7,
        code="TST100",
        title="Test",
        description="Desc",
        department_id=1,
        professor_id=None,
        level="Ugrad",
    )

    course_service = MagicMock()
    course_service.get_course.return_value = course
    course_service.update_course = MagicMock(
        return_value=Course(
            id=7,
            code="TST100",
            title="Test",
            description="Desc",
            department_id=1,
            professor_id=None,
            level="Ugrad",
            image_url="https://storage.example/img.png",
            image_created_with="gemini-test",
        )
    )

    professor_service = MagicMock()

    image_service = MagicMock()
    image_service.generate_course_image = AsyncMock(
        return_value=ImageGenerationResult(success=True, image_keys=["abc.png"])
    )
    image_service.storage_service.images_bucket = "images"
    image_service.storage_service.get_file_url = MagicMock(
        return_value="https://storage.example/img.png"
    )

    job_enqueue = MagicMock()
    repo = MagicMock()

    monkeypatch.setattr(
        "artificial_u.services.course_generator_service.get_settings",
        lambda: MagicMock(IMAGE_GENERATION_MODEL="gemini-test"),
    )

    svc = CourseGeneratorService(
        course_service=course_service,
        professor_service=professor_service,
        content_service=MagicMock(),
        image_service=image_service,
        repository_factory=repo,
        job_enqueue_service=job_enqueue,
        logger=MagicMock(),
    )

    out = await svc.generate_and_set_course_image(7)
    assert out.image_url == "https://storage.example/img.png"
    course_service.update_course.assert_called_once()
    call_kw = course_service.update_course.call_args[0][1]
    assert call_kw["image_url"] == "https://storage.example/img.png"
    assert call_kw["image_created_with"] == "gemini-test"


@pytest.mark.asyncio
async def test_generate_and_set_course_image_raises_on_failed_generation(monkeypatch):
    course = Course(
        id=8,
        code="TST200",
        title="Test",
        description="Desc",
        department_id=1,
        professor_id=None,
        level="Ugrad",
    )
    course_service = MagicMock()
    course_service.get_course.return_value = course

    image_service = MagicMock()
    image_service.generate_course_image = AsyncMock(
        return_value=ImageGenerationResult(success=False, image_keys=[])
    )

    monkeypatch.setattr(
        "artificial_u.services.course_generator_service.get_settings",
        lambda: MagicMock(IMAGE_GENERATION_MODEL="gemini-test"),
    )

    svc = CourseGeneratorService(
        course_service=course_service,
        professor_service=MagicMock(),
        content_service=MagicMock(),
        image_service=image_service,
        repository_factory=MagicMock(),
        job_enqueue_service=MagicMock(),
        logger=MagicMock(),
    )

    with pytest.raises(GenerationError):
        await svc.generate_and_set_course_image(8)
