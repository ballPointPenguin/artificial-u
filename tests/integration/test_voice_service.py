"""
Integration tests for VoiceService.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Professor, Voice
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.voice_service import VoiceService


@pytest.fixture
def repository_factory():
    """Create a repository factory that uses the test database."""
    # The DATABASE_URL will be picked up from .env.test
    return RepositoryFactory()


@pytest.fixture
def mock_elevenlabs_client():
    """Create a mock ElevenLabs client."""
    client = MagicMock()

    # Mock the get_shared_voices method to return some test voices
    client.get_shared_voices.return_value = (
        [
            {
                "el_voice_id": "test-voice-1",
                "name": "Male Professor Voice",
                "gender": "male",
                "accent": "American",
                "age": "middle_aged",
                "description": "Professional teaching voice",
                "preview_url": "https://example.com/preview1",
                "category": "professional",
                "use_case": "education",
                "language": "en",
            },
            {
                "el_voice_id": "test-voice-2",
                "name": "Female Professor Voice",
                "gender": "female",
                "accent": "British",
                "age": "young",
                "description": "Engaging lecturer voice",
                "preview_url": "https://example.com/preview2",
                "category": "professional",
                "use_case": "education",
                "language": "en",
            },
        ],
        False,  # has_more
    )

    # Mock the get_el_voice method to return data for test-voice-1 and None for others
    def get_el_voice_side_effect(voice_id):
        if voice_id == "test-voice-1":
            return {
                "el_voice_id": "test-voice-1",
                "name": "Male Professor Voice",
                "gender": "male",
                "accent": "American",
                "age": "middle_aged",
                "description": "Professional teaching voice",
                "preview_url": "https://example.com/preview1",
                "category": "professional",
                "use_case": "education",
                "language": "en",
            }
        if voice_id == "test-voice-2":
            return {
                "el_voice_id": "test-voice-2",
                "name": "Female Professor Voice",
                "gender": "female",
                "accent": "British",
                "age": "young",
                "description": "Engaging lecturer voice",
                "preview_url": "https://example.com/preview2",
                "category": "professional",
                "use_case": "education",
                "language": "en",
            }
        return None

    client.get_el_voice.side_effect = get_el_voice_side_effect
    return client


@pytest.fixture
def voice_service(repository_factory, mock_elevenlabs_client):
    """Create a VoiceService with mocked ElevenLabs client."""
    return VoiceService(
        repository_factory=repository_factory,
        client=mock_elevenlabs_client,
    )


@pytest.mark.integration
class TestVoiceService:
    """Integration tests for VoiceService."""

    def test_select_voice_for_professor(self, voice_service, repository_factory):
        """Test selecting a voice for a professor."""
        # Prepopulate database with test voices
        test_voices = [
            Voice(
                el_voice_id="test-voice-1",
                name="Male Professor Voice",
                gender="male",
                accent="American",
                age="middle_aged",
                description="Professional teaching voice",
                preview_url="https://example.com/preview1",
                category="professional",
                use_case="education",
                language="en",
                last_updated=datetime.now(),
            ),
            Voice(
                el_voice_id="test-voice-2",
                name="Female Professor Voice",
                gender="female",
                accent="British",
                age="young",
                description="Engaging lecturer voice",
                preview_url="https://example.com/preview2",
                category="professional",
                use_case="education",
                language="en",
                last_updated=datetime.now(),
            ),
            Voice(
                el_voice_id="test-voice-3",
                name="Male German Voice",
                gender="male",
                accent="German",
                age="middle_aged",
                description="Science lecturer voice",
                preview_url="https://example.com/preview3",
                category="professional",
                use_case="education",
                language="de",
                last_updated=datetime.now(),
            ),
        ]

        for voice in test_voices:
            repository_factory.voice.upsert(voice)

        # Create a professor with specific attributes that should match test-voice-1
        professor = Professor(
            name="Dr. John Smith",
            title="Professor",
            gender="male",
            accent="American",
            age=45,  # middle_aged
            description="Expert in Computer Science",
        )

        # Select a voice
        selected_voice = voice_service.select_voice_for_professor(professor)

        # Verify the selection matches the expected voice
        assert selected_voice is not None
        assert (
            selected_voice["el_voice_id"] == "test-voice-1"
        )  # Should match the male American voice
        assert selected_voice["gender"] == "male"
        assert selected_voice["accent"] == "American"
        assert selected_voice["age"] == "middle_aged"

        # Create another professor with different attributes that should match test-voice-2
        professor2 = Professor(
            name="Dr. Jane Doe",
            title="Professor",
            gender="female",
            accent="British",
            age=30,  # young
            description="Expert in Literature",
        )

        # Select a voice for the second professor
        selected_voice2 = voice_service.select_voice_for_professor(professor2)

        # Verify the selection matches the expected voice
        assert selected_voice2 is not None
        assert (
            selected_voice2["el_voice_id"] == "test-voice-2"
        )  # Should match the female British voice
        assert selected_voice2["gender"] == "female"
        assert selected_voice2["accent"] == "British"
        assert selected_voice2["age"] == "young"

    def test_voice_persistence(self, voice_service, repository_factory):
        """Test that voices are properly saved to and retrieved from the database."""
        # Create a test voice
        voice = Voice(
            el_voice_id="test-voice-3",
            name="Test Voice",
            gender="female",
            accent="British",
            age="young",
            description="Test description",
            preview_url="https://example.com/preview3",
            category="professional",
            use_case="education",
            language="en",
            last_updated=datetime.now(),
        )

        # Save to database
        saved_voice = repository_factory.voice.upsert(voice)
        assert saved_voice.id is not None
        assert saved_voice.el_voice_id == "test-voice-3"

        # Retrieve and verify
        retrieved = repository_factory.voice.get_by_elevenlabs_id("test-voice-3")
        assert retrieved is not None
        assert retrieved.name == "Test Voice"
        assert retrieved.gender == "female"
        assert retrieved.accent == "British"

    def test_list_available_voices(self, voice_service, repository_factory):
        """Test listing available voices with filters."""
        # Prepopulate database with test voices
        test_voices = [
            Voice(
                el_voice_id="test-voice-1",
                name="Male Professor Voice",
                gender="male",
                accent="American",
                age="middle_aged",
                description="Professional teaching voice",
                preview_url="https://example.com/preview1",
                category="professional",
                use_case="education",
                language="en",
                last_updated=datetime.now(),
            ),
            Voice(
                el_voice_id="test-voice-2",
                name="Female Professor Voice",
                gender="female",
                accent="British",
                age="young",
                description="Engaging lecturer voice",
                preview_url="https://example.com/preview2",
                category="professional",
                use_case="education",
                language="en",
                last_updated=datetime.now(),
            ),
            Voice(
                el_voice_id="test-voice-3",
                name="German Professor Voice",
                gender="male",
                accent="German",
                age="middle_aged",
                description="Science lecturer voice",
                preview_url="https://example.com/preview3",
                category="professional",
                use_case="education",
                language="de",  # Different language
                last_updated=datetime.now(),
            ),
        ]

        for voice in test_voices:
            repository_factory.voice.upsert(voice)

        # Test filtering by gender and accent
        voices = voice_service.list_available_voices(
            gender="male",
            accent="American",
            language="en",
        )
        assert len(voices) == 1
        assert voices[0]["gender"] == "male"
        assert voices[0]["accent"] == "American"
        assert voices[0]["language"] == "en"

        # Test filtering by gender only
        voices = voice_service.list_available_voices(gender="female")
        assert len(voices) == 1
        assert voices[0]["gender"] == "female"
        assert voices[0]["name"] == "Female Professor Voice"

        # Test filtering by language
        voices = voice_service.list_available_voices(language="de")
        assert len(voices) == 1
        assert voices[0]["language"] == "de"
        assert voices[0]["name"] == "German Professor Voice"

        # Test no filters (should return all voices)
        voices = voice_service.list_available_voices()
        assert len(voices) == 3

    def test_manual_voice_assignment(self, voice_service, repository_factory):
        """Test manually assigning a voice to a professor."""
        # Create a professor
        professor = Professor(
            name="Dr. Jane Doe",
            title="Associate Professor",
            gender="female",
            accent="British",
            description="Expert in Physics",
        )
        professor = repository_factory.professor.create(professor)

        # Manually assign a voice
        voice_service.manual_voice_assignment(professor.id, "test-voice-2")

        # Verify the assignment
        updated_professor = repository_factory.professor.get(professor.id)
        assert updated_professor.voice_id is not None

        # Verify the voice details
        voice = repository_factory.voice.get_by_elevenlabs_id("test-voice-2")
        assert voice is not None
        assert voice.name == "Female Professor Voice"
        assert voice.gender == "female"
        assert voice.accent == "British"

    def test_voice_selection_with_relaxed_criteria(self, voice_service):
        """Test voice selection when strict criteria yields no results."""
        # Create a professor with criteria that won't match exactly
        professor = Professor(
            name="Dr. Alex Johnson",
            title="Professor",
            gender="non-binary",  # This won't match our test voices
            accent="Australian",  # This won't match our test voices
            age=35,
            description="Expert in Biology",
        )

        # Select a voice - should still work with relaxed criteria
        selected_voice = voice_service.select_voice_for_professor(professor)

        # Verify we got a voice despite non-matching criteria
        assert selected_voice is not None
        assert "el_voice_id" in selected_voice

    def test_get_voice_by_el_id(self, voice_service, repository_factory):
        """Test retrieving voice data by ElevenLabs ID."""
        # First create a voice in the database
        voice = Voice(
            el_voice_id="test-voice-1",
            name="Male Professor Voice",
            gender="male",
            accent="American",
            age="middle_aged",
            description="Professional teaching voice",
            preview_url="https://example.com/preview1",
            category="professional",
            use_case="education",
            language="en",
            last_updated=datetime.now(),
        )
        repository_factory.voice.upsert(voice)

        # Get the voice from the service
        voice_data = voice_service.get_voice_by_el_id("test-voice-1")

        # Verify the data
        assert voice_data is not None
        assert voice_data["el_voice_id"] == "test-voice-1"
        assert voice_data["name"] == "Male Professor Voice"
        assert voice_data["gender"] == "male"
        assert voice_data["accent"] == "American"

        # Try getting a non-existent voice
        voice_data = voice_service.get_voice_by_el_id("non-existent-voice")
        assert voice_data is None
