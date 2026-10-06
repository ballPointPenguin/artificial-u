"""Tests for ElevenLabsClient.get_el_voice (library lookup path)."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from artificial_u.integrations.elevenlabs.client import ElevenLabsClient

pytestmark = pytest.mark.unit


def make_client(response):
    client = ElevenLabsClient(api_key="test_key")
    client.client = MagicMock()
    client.client.voices.get.return_value = response
    return client


def test_library_voice_keeps_verified_languages_and_labels():
    response = SimpleNamespace(
        voice_id="abc",
        name="Jarnathan",
        category="high_quality",
        labels={
            "gender": "male",
            "accent": "american",
            "age": "middle_aged",
            "descriptive": "confident",
            "use_case": "conversational",
            "language": "en",
        },
        description="desc",
        preview_url="http://preview",
        verified_languages=[SimpleNamespace(model_id="eleven_v4")],
    )

    voice = make_client(response).get_el_voice("abc")

    assert [v.model_id for v in voice["verified_languages"]] == ["eleven_v4"]
    assert voice["descriptive"] == "confident"
    assert voice["use_case"] == "conversational"
    assert voice["language"] == "en"


def test_library_voice_without_labels_or_verified_languages():
    response = SimpleNamespace(
        voice_id="abc", name="Plain", category="premade", labels=None, verified_languages=None
    )

    voice = make_client(response).get_el_voice("abc")

    assert voice["verified_languages"] == []
    assert voice["gender"] == "neutral"
    assert voice["language"] is None


def test_not_in_library_skips_shared_search_when_disabled():
    client = ElevenLabsClient(api_key="test_key")
    client.client = MagicMock()
    client.client.voices.get.side_effect = Exception("voice_not_found")
    client._search_shared_voice_by_id = MagicMock(return_value={"el_voice_id": "x"})

    assert client.get_el_voice("x", search_shared=False) is None
    client._search_shared_voice_by_id.assert_not_called()
    assert client.get_el_voice("x") == {"el_voice_id": "x"}
