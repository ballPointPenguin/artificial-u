"""Tests for the TTS backend/model label shown on lecture audio jobs."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from artificial_u.api.routers.jobs import _job_model_name

pytestmark = pytest.mark.unit

SETTINGS = SimpleNamespace(
    tts_backend="elevenlabs",
    TTS_VOICE_MODEL="eleven_v4",
    TTS_MISTRAL_MODEL="voxtral-mini-tts-2603",
)


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    monkeypatch.setattr("artificial_u.api.routers.jobs.get_settings", lambda: SETTINGS)


def make_factory(professor_backend=None, voice_backend=None):
    factory = MagicMock()
    factory.lecture.get.return_value = SimpleNamespace(course_id=5)
    factory.course.get.return_value = SimpleNamespace(professor_id=9)
    factory.professor.get.return_value = SimpleNamespace(
        tts_backend=professor_backend, voice_id=3 if voice_backend else None
    )
    factory.voice.get.return_value = SimpleNamespace(tts_backend=voice_backend)
    return factory


def test_recorded_result_includes_model():
    result = {"tts_backend": "elevenlabs", "tts_model": "eleven_flash_v2_5"}
    label = _job_model_name("generate_lecture_audio", {"lecture_id": 1}, result)
    assert label == "elevenlabs/eleven_flash_v2_5"


def test_recorded_result_without_model_shows_backend_only():
    result = {"tts_backend": "elevenlabs"}
    assert _job_model_name("generate_lecture_audio", {"lecture_id": 1}, result) == "elevenlabs"


def test_pending_job_uses_professor_voice_backend_not_global_default():
    factory = make_factory(voice_backend="mistral")
    label = _job_model_name("generate_lecture_audio", {"lecture_id": 1}, None, factory)
    assert label == "mistral/voxtral-mini-tts-2603"


def test_pending_job_professor_override_wins():
    factory = make_factory(professor_backend="xai", voice_backend="elevenlabs")
    label = _job_model_name("generate_lecture_audio", {"lecture_id": 1}, None, factory)
    assert label == "xai"


def test_pending_elevenlabs_job_shows_configured_model():
    factory = make_factory(voice_backend="elevenlabs")
    label = _job_model_name("generate_lecture_audio", {"lecture_id": 1}, None, factory)
    assert label == "elevenlabs/eleven_v4"


def test_pending_job_lookup_is_cached_per_lecture():
    factory = make_factory(voice_backend="mistral")
    cache: dict = {}
    for _ in range(3):
        _job_model_name("generate_lecture_audio", {"lecture_id": 1}, None, factory, cache)
    assert factory.lecture.get.call_count == 1


def test_unresolvable_lecture_falls_back_to_global_backend():
    factory = make_factory()
    factory.lecture.get.return_value = None
    label = _job_model_name("generate_lecture_audio", {"lecture_id": 1}, None, factory)
    assert label == "elevenlabs/eleven_v4"
