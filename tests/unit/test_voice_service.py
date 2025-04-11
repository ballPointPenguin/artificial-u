"""
Unit tests for the VoiceService.

These tests use mocking to avoid actual API calls or database operations
while verifying the service behaves as expected.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from artificial_u.models.core import Professor, Voice
from artificial_u.services.voice_service import VoiceService
from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper
from artificial_u.integrations.elevenlabs.cache import VoiceCache


@pytest.fixture
def mock_client():
    """Create a mock ElevenLabsClient."""
    with patch("artificial_u.integrations.elevenlabs.client.ElevenLabsClient") as mock:
        client = MagicMock(spec=ElevenLabsClient)
        mock.return_value = client

        # Set up common method returns
        client.get_voice.return_value = {
            "voice_id": "test-voice-1",
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
                    "voice_id": "test-voice-1",
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
    mapper = MagicMock(spec=VoiceMapper)

    # Set up common method returns
    mapper.extract_profile_attributes.return_value = {
        "gender": "male",
        "accent": "american",
        "age": "middle_aged",
    }

    mapper.rank_voices.return_value = [
        {
            "voice_id": "test-voice-1",
            "name": "Test Voice 1",
            "match_score": 0.9,
            "gender": "male",
        }
    ]

    mapper.select_voice.return_value = {
        "voice_id": "test-voice-1",
        "name": "Test Voice 1",
        "match_score": 0.9,
    }

    return mapper


@pytest.fixture
def mock_cache():
    """Create a mock VoiceCache."""
    cache = MagicMock(spec=VoiceCache)

    # Set up common method returns
    cache.get_professor_voice_mapping.return_value = None
    cache.build_criteria_key.return_value = "male_american_middle_aged"
    cache.get_voices_by_criteria.return_value = []

    return cache


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
        id="prof123",
        name="Dr. John Smith",
        title="Professor of Physics",
        department="Physics",
        specialization="Quantum Mechanics",
        background="American physicist with 15 years of experience.",
        personality="Enthusiastic and passionate",
        teaching_style="Engaging and interactive",
    )


@pytest.mark.unit
class TestVoiceService:
    """Test suite for VoiceService."""

    @pytest.mark.unit
    def test_init(self, mock_client, mock_mapper, mock_cache, mock_repository):
        """Test service initialization."""
        # Create service with injected mocks
        service = VoiceService(
            api_key="test_key",
            client=mock_client,
            mapper=mock_mapper,
            cache=mock_cache,
            repository=mock_repository,
        )

        # Verify dependencies were properly set
        assert service.client == mock_client
        assert service.mapper == mock_mapper
        assert service.cache == mock_cache
        assert service.repository == mock_repository

    @pytest.mark.unit
    def test_select_voice_for_professor_new(
        self, mock_client, mock_mapper, mock_cache, mock_repository, sample_professor
    ):
        """Test selecting a voice for a professor with no existing mapping."""
        # Create service with injected mocks
        service = VoiceService(
            client=mock_client,
            mapper=mock_mapper,
            cache=mock_cache,
            repository=mock_repository,
        )

        # Call the method
        result = service.select_voice_for_professor(sample_professor)

        # Verify the result
        assert result["voice_id"] == "test-voice-1"

        # Verify method calls
        mock_cache.get_professor_voice_mapping.assert_called_once_with(
            sample_professor.id
        )
        mock_mapper.extract_profile_attributes.assert_called_once()
        mock_repository.list_voices.assert_called_once()
        mock_client.get_shared_voices.assert_called_once()
        mock_mapper.rank_voices.assert_called_once()
        mock_mapper.select_voice.assert_called_once()
        mock_cache.set_professor_voice_mapping.assert_called_once_with(
            sample_professor.id, "test-voice-1"
        )

    @pytest.mark.unit
    def test_select_voice_for_professor_cached(
        self, mock_client, mock_mapper, mock_cache, mock_repository, sample_professor
    ):
        """Test selecting a voice for a professor with existing cache mapping."""
        # Set up cached mapping
        mock_cache.get_professor_voice_mapping.return_value = "cached-voice-id"
        mock_cache.get_voice.return_value = None  # Cache miss to force API call

        # Create the return value for get_voice as a real dict, not a mock
        voice_data = {
            "voice_id": "cached-voice-id",
            "name": "Cached Voice",
            "gender": "male",
            "accent": "american",
        }

        # Configure the mock to return the dict directly
        # Set the return value directly rather than relying on __getitem__
        mock_client.get_voice.return_value = voice_data

        # Create service with injected mocks
        service = VoiceService(
            client=mock_client,
            mapper=mock_mapper,
            cache=mock_cache,
            repository=mock_repository,
        )

        # Call the method
        result = service.select_voice_for_professor(sample_professor)

        # For debugging
        print(f"Result type: {type(result)}")
        print(f"Result content: {result}")

        # Compare the entire dictionary instead of accessing by key
        assert result == voice_data

        # Verify method calls
        mock_cache.get_professor_voice_mapping.assert_called_once_with(
            sample_professor.id
        )
        mock_client.get_voice.assert_called_once_with("cached-voice-id")

        # Verify that no other methods were called
        mock_mapper.extract_profile_attributes.assert_not_called()
        mock_repository.list_voices.assert_not_called()
        mock_client.get_shared_voices.assert_not_called()

    @pytest.mark.unit
    def test_get_voice_id_for_professor(
        self, mock_client, mock_mapper, mock_cache, mock_repository, sample_professor
    ):
        """Test getting a voice ID for a professor."""
        # Create service with injected mocks
        service = VoiceService(
            client=mock_client,
            mapper=mock_mapper,
            cache=mock_cache,
            repository=mock_repository,
        )

        # Mock select_voice_for_professor
        service.select_voice_for_professor = MagicMock(
            return_value={"voice_id": "test-voice-1"}
        )

        # Call the method
        result = service.get_voice_id_for_professor(sample_professor)

        # Verify the result
        assert result == "test-voice-1"

        # Verify method calls
        service.select_voice_for_professor.assert_called_once_with(
            sample_professor, additional_context=None
        )
