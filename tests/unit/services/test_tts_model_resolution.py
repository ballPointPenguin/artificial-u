"""Tests for ElevenLabs model selection and v4 fallback in TTSService."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper
from artificial_u.services.tts_service import TTSService
from artificial_u.utils import AudioProcessingError

pytestmark = pytest.mark.unit


def make_service(configured_model="eleven_v4", verified=None):
    backend = MagicMock()
    backend.backend_name = "elevenlabs"
    repo = MagicMock()
    repo.voice.get.return_value = {"verified_languages": verified} if verified else None
    service = TTSService(backend=backend, repository_factory=repo)
    service.settings = SimpleNamespace(
        TTS_VOICE_MODEL=configured_model, TTS_MISTRAL_MODEL="voxtral-mini-tts-2603"
    )
    return service


PROFESSOR = SimpleNamespace(voice_id=1)
LECTURE = SimpleNamespace(content="Hello class")


def test_v4_used_even_when_voice_does_not_list_it():
    service = make_service(verified=[{"model_id": "eleven_flash_v2_5"}])
    assert service._resolve_model_for_voice(PROFESSOR, "abc") == "eleven_v4"


def test_non_v4_configured_model_keeps_verified_behavior():
    service = make_service(
        configured_model="eleven_flash_v2_5",
        verified=[{"model_id": "eleven_multilingual_v2"}],
    )
    assert service._resolve_model_for_voice(PROFESSOR, "abc") == "eleven_multilingual_v2"


def test_verified_fallback_never_returns_v4_without_info():
    service = make_service()
    assert service._resolve_verified_model_for_voice(PROFESSOR, "abc") == "eleven_flash_v2_5"


def test_generation_falls_back_when_v4_fails():
    service = make_service(verified=[{"model_id": "eleven_multilingual_v2"}])
    calls = []

    def fake_convert(text, voice_id, model_id=None, language=None, **kwargs):
        calls.append(model_id)
        if model_id == "eleven_v4":
            raise RuntimeError("voice not supported")
        return b"audio"

    service.convert_text_to_speech = fake_convert
    audio = service.generate_lecture_audio(LECTURE, PROFESSOR, voice_id="abc")

    assert audio == b"audio"
    assert calls == ["eleven_v4", "eleven_multilingual_v2"]


def test_synthesis_reports_model_actually_used():
    service = make_service(verified=[{"model_id": "eleven_multilingual_v2"}])
    service.convert_text_to_speech = MagicMock(return_value=b"audio")
    result = service.synthesize_lecture_audio(LECTURE, PROFESSOR, voice_id="abc")
    assert (result.audio, result.model_id) == (b"audio", "eleven_v4")


def test_synthesis_reports_fallback_model_when_v4_fails():
    service = make_service(verified=[{"model_id": "eleven_multilingual_v2"}])

    def fake_convert(text, voice_id, model_id=None, language=None, **kwargs):
        if model_id == "eleven_v4":
            raise RuntimeError("voice not supported")
        return b"audio"

    service.convert_text_to_speech = fake_convert
    result = service.synthesize_lecture_audio(LECTURE, PROFESSOR, voice_id="abc")
    assert result.model_id == "eleven_multilingual_v2"


def test_explicit_model_is_not_retried():
    service = make_service()
    service.convert_text_to_speech = MagicMock(side_effect=RuntimeError("boom"))
    with pytest.raises(AudioProcessingError):
        service.generate_lecture_audio(LECTURE, PROFESSOR, voice_id="abc", model_id="eleven_v4")
    assert service.convert_text_to_speech.call_count == 1


def test_non_elevenlabs_backend_is_untouched():
    service = make_service()
    service.backend.backend_name = "mistral"
    service.convert_text_to_speech = MagicMock(return_value=b"audio")
    service.generate_lecture_audio(LECTURE, PROFESSOR, voice_id="abc")
    assert service.convert_text_to_speech.call_args.kwargs["model_id"] is None


def test_voice_mapper_gently_prefers_v4_voices():
    mapper = VoiceMapper()
    base = {"category": "professional", "gender": "male"}
    v4 = {**base, "verified_languages": [{"model_id": "eleven_v4"}]}
    older = {**base, "verified_languages": [{"model_id": "eleven_flash_v2_5"}]}
    criteria = {"gender": "male"}
    diff = mapper._calculate_voice_match_score(v4, criteria) - mapper._calculate_voice_match_score(
        older, criteria
    )
    assert diff == pytest.approx(0.1)
