"""Tests for VoiceService.refresh_voices_missing_verified_languages."""

from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Voice
from artificial_u.services.voice_service import VoiceService

pytestmark = pytest.mark.unit


def make_service(voices, fetched_by_id):
    repository_factory = MagicMock()
    repository_factory.voice.list_missing_verified_languages.return_value = voices
    client = MagicMock()
    client.get_el_voice.side_effect = lambda el_id, **kwargs: fetched_by_id.get(el_id)
    return VoiceService(repository_factory=repository_factory, client=client), repository_factory


def test_fills_verified_languages_and_empty_fields_only():
    voice = Voice(
        id=1,
        el_voice_id="a",
        name="Jarnathan",
        preview_url="http://existing-preview",
        popularity_score=500,
    )
    fetched = {
        "el_voice_id": "a",
        "preview_url": "http://new-preview",
        "language": "en",
        "use_case": "conversational",
        "verified_languages": [{"model_id": "eleven_v4"}],
    }
    service, factory = make_service([voice], {"a": fetched})

    stats = service.refresh_voices_missing_verified_languages()

    assert stats == {"checked": 1, "updated": 1, "unresolved": 0}
    saved = factory.voice.update.call_args[0][0]
    assert saved.verified_languages == [{"model_id": "eleven_v4"}]
    assert (saved.language, saved.use_case) == ("en", "conversational")
    # Existing values are never overwritten
    assert saved.preview_url == "http://existing-preview"
    assert saved.popularity_score == 500


def test_unknown_voice_is_counted_unresolved_and_not_saved():
    voice = Voice(id=2, el_voice_id="gone", name="Gone")
    service, factory = make_service([voice], {})

    stats = service.refresh_voices_missing_verified_languages()

    assert stats == {"checked": 1, "updated": 0, "unresolved": 1}
    factory.voice.update.assert_not_called()


def test_voice_still_without_verified_languages_upstream_is_unresolved():
    voice = Voice(id=3, el_voice_id="b", name="Plain")
    fetched = {"el_voice_id": "b", "verified_languages": []}
    service, factory = make_service([voice], {"b": fetched})

    stats = service.refresh_voices_missing_verified_languages()

    assert stats == {"checked": 1, "updated": 0, "unresolved": 1}
    factory.voice.update.assert_not_called()


def test_refresh_skips_slow_shared_voice_search():
    voice = Voice(id=4, el_voice_id="c", name="C")
    service, _ = make_service([voice], {})

    service.refresh_voices_missing_verified_languages()

    service.client.get_el_voice.assert_called_once_with("c", search_shared=False)
