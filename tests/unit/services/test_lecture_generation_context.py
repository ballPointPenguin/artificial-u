"""Lecture generation fails, rather than degrading, when its context cannot be loaded."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from artificial_u.services.lecture_generator_service import LectureGeneratorService
from artificial_u.utils import DatabaseError


def _service():
    service = LectureGeneratorService.__new__(LectureGeneratorService)
    service.logger = MagicMock()
    service.course_service = MagicMock()
    service.professor_service = MagicMock()
    service.topic_service = MagicMock()
    service.repository_factory = MagicMock()
    return service


@pytest.mark.unit
def test_professor_lookup_failure_raises():
    service = _service()
    service.course_service.get_course.return_value = SimpleNamespace(professor_id=3)
    service.professor_service.get_professor.side_effect = RuntimeError("connection reset")

    with pytest.raises(DatabaseError, match="professor"):
        service._get_professor_data_for_generation(1)


@pytest.mark.unit
def test_course_without_professor_is_still_allowed():
    service = _service()
    service.course_service.get_course.return_value = SimpleNamespace(professor_id=None)

    assert service._get_professor_data_for_generation(1) == {}


@pytest.mark.unit
def test_existing_lectures_lookup_failure_raises():
    service = _service()
    service.repository_factory.lecture.list_by_course.side_effect = RuntimeError("timeout")

    with pytest.raises(DatabaseError, match="existing lectures"):
        service._get_existing_lectures_data_for_generation(course_id=1)


@pytest.mark.unit
def test_course_topics_lookup_failure_raises():
    service = _service()
    service.topic_service.list_topics_by_course.side_effect = RuntimeError("timeout")

    with pytest.raises(DatabaseError, match="topics"):
        service._get_all_course_topics_data_for_generation(1)
