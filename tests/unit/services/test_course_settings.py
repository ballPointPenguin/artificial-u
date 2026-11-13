"""Tests for per-course settings (lecture generation model override)."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from artificial_u.api.models.courses import CourseUpdate
from artificial_u.api.routers.jobs import _job_model_name
from artificial_u.api.services.course_service import CourseApiService
from artificial_u.models.core import Course, CourseSettings
from artificial_u.services.course_service import CourseService
from artificial_u.services.preference_service import PreferenceService

pytestmark = pytest.mark.unit


def make_course(**settings) -> Course:
    return Course(id=7, code="CS101", title="Intro", settings=CourseSettings(**settings))


# --- CourseSettings schema ---------------------------------------------------


def test_course_settings_blank_model_becomes_none():
    assert CourseSettings(lecture_generation_model="  ").lecture_generation_model is None
    assert CourseSettings(lecture_generation_model=" gpt-x ").lecture_generation_model == "gpt-x"


def test_course_settings_rejects_unknown_keys():
    with pytest.raises(ValidationError):
        CourseSettings.model_validate({"unknown": 1})


# --- Core service update merge ----------------------------------------------


@pytest.fixture
def core_service():
    factory = MagicMock()
    factory.course.update.side_effect = lambda course: course
    return CourseService(
        repository_factory=factory,
        professor_service=MagicMock(),
        department_selector_service=MagicMock(),
        professor_selector_service=MagicMock(),
    )


def _apply(core_service, existing: Course, payload: dict) -> Course:
    core_service.repository_factory.course.get.return_value = existing
    update = CourseUpdate.model_validate(payload).model_dump(exclude_unset=True)
    return core_service.update_course(existing.id, update)


def test_update_sets_lecture_model(core_service):
    updated = _apply(
        core_service, make_course(), {"settings": {"lecture_generation_model": "gpt-x"}}
    )
    assert updated.settings.lecture_generation_model == "gpt-x"


def test_update_with_null_model_clears_override(core_service):
    existing = make_course(lecture_generation_model="gpt-x")
    updated = _apply(core_service, existing, {"settings": {"lecture_generation_model": None}})
    assert updated.settings == CourseSettings()


def test_update_without_settings_keeps_override(core_service):
    existing = make_course(lecture_generation_model="gpt-x")
    updated = _apply(core_service, existing, {"title": "New"})
    assert updated.settings.lecture_generation_model == "gpt-x"


def test_update_with_empty_settings_object_is_noop(core_service):
    existing = make_course(lecture_generation_model="gpt-x")
    updated = _apply(core_service, existing, {"settings": {}})
    assert updated.settings.lecture_generation_model == "gpt-x"


# --- API service permissions -------------------------------------------------


def test_course_owner_can_change_settings():
    service = CourseApiService(
        content_service=MagicMock(),
        professor_service=MagicMock(),
        repository_factory=MagicMock(),
        course_service=MagicMock(),
        storage_service=MagicMock(),
        image_service=MagicMock(),
    )
    service.core_service.get_course.return_value = SimpleNamespace(created_by=1)
    service._build_course_response = MagicMock()
    update = CourseUpdate(settings=CourseSettings(lecture_generation_model="gpt-x"))

    service.update_course(7, update, student_id=1, role="creator")

    service.core_service.update_course.assert_called_once_with(
        7, {"settings": {"lecture_generation_model": "gpt-x"}}
    )


# --- Model resolution order ---------------------------------------------------


@pytest.fixture
def preference_service():
    factory = MagicMock()
    factory.preference.get.return_value = SimpleNamespace(value="pref-model")
    return PreferenceService(factory)


def test_course_override_beats_user_and_global_preference(preference_service):
    preference_service.repository_factory.course.get.return_value = make_course(
        lecture_generation_model="course-model"
    )
    model = preference_service.get_lecture_generation_model(student_id=1, course_id=7)
    assert model == "course-model"


def test_course_without_override_falls_back_to_preference(preference_service):
    preference_service.repository_factory.course.get.return_value = make_course()
    model = preference_service.get_lecture_generation_model(student_id=1, course_id=7)
    assert model == "pref-model"


def test_no_course_id_skips_course_lookup(preference_service):
    assert preference_service.get_lecture_generation_model(student_id=1) == "pref-model"
    preference_service.repository_factory.course.get.assert_not_called()


# --- Jobs list planned model --------------------------------------------------


@pytest.mark.parametrize("kind", ["generate_lecture", "generate_lecture_text_only"])
def test_pending_lecture_job_shows_course_override(kind):
    factory = MagicMock()
    factory.course.get.return_value = make_course(lecture_generation_model="course-model")
    payload = {"partial_attributes": {"course_id": 7, "topic_id": 1}}
    assert _job_model_name(kind, payload, None, factory) == "course-model"


def test_pending_lecture_job_without_override_uses_global_preference():
    factory = MagicMock()
    factory.course.get.return_value = make_course()
    factory.preference.get_global.return_value = SimpleNamespace(value="global-model")
    payload = {"partial_attributes": {"course_id": 7}}
    assert _job_model_name("generate_lecture", payload, None, factory) == "global-model"
