"""Connected-course topic context uses TopicRepository.list_by_course."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from artificial_u.services.course_generator_service import CourseGeneratorService

pytestmark = pytest.mark.unit


def test_related_courses_topics_uses_list_by_course(monkeypatch):
    monkeypatch.setattr(
        "artificial_u.services.course_generator_service.topics_to_xml",
        lambda topics: f"<topics count='{len(topics)}'/>",
    )

    topic = SimpleNamespace(id=1, title="Intro", week=1, order=1, content="cells")
    repository_factory = MagicMock()
    repository_factory.topic.list_by_course.return_value = [topic]

    svc = CourseGeneratorService(
        course_service=MagicMock(),
        professor_service=MagicMock(),
        content_service=MagicMock(),
        image_service=MagicMock(),
        repository_factory=repository_factory,
        logger=MagicMock(),
    )

    context = svc._build_related_courses_topics_context([{"id": 79, "title": "Prior Course"}])

    repository_factory.topic.list_by_course.assert_called_once_with(79)
    repository_factory.topic.list.assert_not_called()
    assert "Prior Course" in context
    assert "<topics count='1'/>" in context
    svc.logger.warning.assert_not_called()
