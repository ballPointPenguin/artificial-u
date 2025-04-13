"""
Unit tests for the ElevenLabsClient.

These tests use mocking to avoid actual API calls
while verifying the client behaves as expected.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from artificial_u.integrations.elevenlabs.client import ElevenLabsClient


@pytest.fixture
def mock_elevenlabs():
    """Mock the ElevenLabs class."""
    with patch("elevenlabs.client.ElevenLabs") as mock_elevenlabs:
        mock_client = MagicMock()
        mock_elevenlabs.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_requests():
    """Mock the requests library."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": [
                {
                    "voice_id": "test-voice-1",
                    "name": "Test Voice 1",
                    "gender": "female",
                    "accent": "american",
                }
            ],
            "has_more": False,
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.mark.unit
class TestElevenLabsClient:
    """Test suite for ElevenLabsClient."""

    @pytest.mark.unit
    def test_init_with_test_api_key(self):
        """Test that client initializes with test API key from environment."""
        # Save original env var if it exists
        original_key = os.environ.get("ELEVENLABS_API_KEY")

        try:
            # Set test key in environment
            os.environ["ELEVENLABS_API_KEY"] = "test_elevenlabs_key"

            # In our updated implementation, we need to ensure TESTING is true
            os.environ["TESTING"] = "true"

            # Create client with the test key from environment
            client = ElevenLabsClient()

            # Verify the key was correctly set
            assert client.api_key == "test_elevenlabs_key"

        finally:
            # Restore original env vars
            if original_key:
                os.environ["ELEVENLABS_API_KEY"] = original_key
            else:
                del os.environ["ELEVENLABS_API_KEY"]

    @pytest.mark.unit
    def test_get_shared_voices(self, mock_requests):
        """Test getting shared voices from the API."""
        # Create client and call method
        client = ElevenLabsClient(api_key="test_key")
        el_voices, has_more = client.get_shared_voices(
            gender="female", accent="american"
        )

        # Verify results
        assert len(el_voices) == 1
        assert el_voices[0]["el_voice_id"] == "test-voice-1"
        assert not has_more

        # Verify API was called with correct parameters
        mock_requests.assert_called_once()
        args, kwargs = mock_requests.call_args
        assert args[0] == "https://api.elevenlabs.io/v1/shared-voices"
        assert kwargs["params"]["gender"] == "female"
        assert kwargs["params"]["accent"] == "american"

    @pytest.mark.unit
    def test_text_to_speech_with_mocks(self, mock_elevenlabs):
        """Test text-to-speech conversion."""
        # Create a correctly structured mock for the client
        client_mock = MagicMock()
        tts_mock = MagicMock()

        # Mock the convert method to return our test data
        mock_audio_data = b"test audio data"
        tts_mock.convert.return_value = [
            mock_audio_data
        ]  # Return a list as if it's a generator
        client_mock.text_to_speech = tts_mock

        # Create the client and set the testing mode
        with patch("elevenlabs.client.ElevenLabs", return_value=client_mock):
            os.environ["TESTING"] = "true"
            client = ElevenLabsClient(api_key="test_key")

            # Replace the client's client with our mock
            client.client = client_mock

            # Set up our test data
            model_id = "test-model"
            el_voice_id = "test-voice-1"
            text = "Hello world"

            # Test method that now returns mocked data
            result = client.text_to_speech(
                text=text, el_voice_id=el_voice_id, model_id=model_id
            )

            # The result should be our mock audio data
            assert result == mock_audio_data
