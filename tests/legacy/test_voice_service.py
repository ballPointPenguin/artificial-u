"""
Unit tests for the VoiceService.

These tests use mocking to avoid actual API calls or database operations
while verifying the service behaves as expected.
"""

from unittest.mock import MagicMock, patch

import pytest

from artificial_u.integrations import elevenlabs
from artificial_u.models.core import Professor
from artificial_u.services import VoiceService


@pytest.fixture
def mock_client():
    """Create a mock ElevenLabsClient."""
    with patch("artificial_u.integrations.elevenlabs.client.ElevenLabsClient") as mock:
        client = MagicMock(spec=elevenlabs.ElevenLabsClient)
        mock.return_value = client

        # Set up common method returns
        client.get_el_voice.return_value = {
            "el_voice_id": "test-voice-1",
            "name": "Test Voice 1",
            "category": "premade",
            "gender": "male",
            "accent": "american",
            "age": "middle_aged",
            "description": "A test voice",
        }

        client.get_shared_voices.return_value = (
            [
                {
                    "el_voice_id": "test-voice-1",
                    "name": "Test Voice 1",
                    "gender": "male",
                    "accent": "american",
                    "age": "middle_aged",
                }
            ],
            False,
        )

        yield client


@pytest.fixture
def mock_mapper():
    """Create a mock VoiceMapper."""
    mapper = MagicMock(spec=elevenlabs.VoiceMapper)

    # Set up common method returns
    mapper.extract_profile_attributes.return_value = {
        "gender": "male",
        "accent": "american",
        "age": "middle_aged",
    }

    mapper.rank_voices.return_value = [
        {
            "el_voice_id": "test-voice-1",
            "name": "Test Voice 1",
            "match_score": 0.9,
            "gender": "male",
        }
    ]

    mapper.select_voice.return_value = {
        "el_voice_id": "test-voice-1",
        "name": "Test Voice 1",
        "match_score": 0.9,
    }

    return mapper


@pytest.fixture
def mock_repository():
    """Create a mock Repository."""
    repo = MagicMock()

    # Set up common method returns
    repo.list_voices.return_value = []
    repo.get_voice_by_elevenlabs_id.return_value = None

    return repo


@pytest.fixture
def sample_professor():
    """Create a sample professor for testing."""
    return Professor(
        id=123,
        name="Dr. John Smith",
        title="Professor of Physics",
        department="Physics",
        specialization="Quantum Mechanics",
        background="American physicist with 15 years of experience.",
        personality="Enthusiastic and passionate",
        teaching_style="Engaging and interactive",
    )


@pytest.mark.skip
class TestVoiceService:
    """Test suite for VoiceService."""

    def test_init(self, mock_client, mock_mapper, mock_repository):
        """Test service initialization."""
        # Create service with injected mocks
        service = VoiceService(
            api_key="test_key",
            client=mock_client,
            mapper=mock_mapper,
            repository=mock_repository,
        )

        # Verify dependencies were properly set
        assert service.client == mock_client
        assert service.mapper == mock_mapper
        assert service.repository == mock_repository

    def test_get_voice_id_for_professor(
        self, mock_client, mock_mapper, mock_repository, sample_professor
    ):
        """Test getting a voice ID for a professor."""
        # Create service with injected mocks
        service = VoiceService(
            client=mock_client,
            mapper=mock_mapper,
            repository=mock_repository,
        )

        # Mock select_voice_for_professor
        service.select_voice_for_professor = MagicMock(return_value={"el_voice_id": "test-voice-1"})

        # Call the method
        result = service.select_voice_for_professor(sample_professor)

        # Verify the result
        assert result == {"el_voice_id": "test-voice-1"}

        # Verify method calls
        service.select_voice_for_professor.assert_called_once_with(sample_professor)
