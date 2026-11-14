"""Tests for the one-off course generation model override."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.api.models.courses import CourseGenerate
from artificial_u.services.course_generator_service import CourseGeneratorService

pytestmark = pytest.mark.unit


@pytest.fixture
def generator(monkeypatch):
    monkeypatch.setattr(
        "artificial_u.services.course_generator_service.parse_course_xml",
        lambda _xml: {"code": "CS101", "title": "Intro"},
    )
    svc = CourseGeneratorService(
        course_service=MagicMock(),
        professor_service=MagicMock(),
        content_service=MagicMock(),
        image_service=MagicMock(),
        repository_factory=MagicMock(),
        logger=MagicMock(),
    )
    svc._process_models_for_generation = AsyncMock(return_value=(None, None, []))
    svc._get_connected_courses = AsyncMock(return_value=[])
    svc._generate_and_parse_content = AsyncMock(return_value="<course/>")
    svc.preference_service = MagicMock()
    svc.preference_service.get_course_generation_model.return_value = "configured-model"
    return svc


@pytest.mark.asyncio
async def test_requested_model_is_used_and_recorded(generator):
    result = await generator.generate_course({"title": "Intro"}, model="one-off-model")

    assert generator._generate_and_parse_content.call_args.kwargs["model"] == "one-off-model"
    assert result["created_with"] == "one-off-model"
    generator.preference_service.get_course_generation_model.assert_not_called()


@pytest.mark.asyncio
async def test_configured_model_is_used_without_override(generator):
    result = await generator.generate_course({"title": "Intro"})

    assert generator._generate_and_parse_content.call_args.kwargs["model"] == "configured-model"
    assert result["created_with"] == "configured-model"


def test_blank_requested_model_becomes_none():
    assert CourseGenerate(model="  ").model is None
    assert CourseGenerate(model=" gpt-x ").model == "gpt-x"
