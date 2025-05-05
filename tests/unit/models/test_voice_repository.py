"""
Unit tests for VoiceRepository.
"""

from unittest.mock import ANY, MagicMock, call, patch

import pytest

from artificial_u.models.core import Voice
from artificial_u.models.database import VoiceModel
from artificial_u.models.repositories.voice import VoiceRepository


@pytest.mark.unit
class TestVoiceRepository:
    """Test the VoiceRepository class."""

    @pytest.fixture
    def voice_repository(self, repository_with_session):
        """Create a VoiceRepository with a mock session."""
        return repository_with_session(VoiceRepository)

    @pytest.fixture
    def mock_voice_model(self):
        """Create a mock voice model for testing."""
        mock_voice = MagicMock(spec=VoiceModel)
        mock_voice.id = 1
        mock_voice.el_voice_id = "el_voice_1"
        mock_voice.name = "Test Voice"
        mock_voice.accent = "Standard"
        mock_voice.gender = "female"
        mock_voice.age = "adult"
        mock_voice.descriptive = "calm"
        mock_voice.use_case = "narration"
        mock_voice.category = "generated"
        mock_voice.language = "en"
        mock_voice.locale = "en-US"
        mock_voice.description = "A test voice"
        mock_voice.preview_url = "http://example.com/preview.mp3"
        mock_voice.verified_languages = {"en": True}
        mock_voice.popularity_score = 80
        mock_voice.last_updated = MagicMock()
        return mock_voice

    def test_create(self, voice_repository, mock_session):
        """Test creating a voice."""

        # Configure mock behaviors
        def mock_refresh(model):
            model.id = 1

        mock_session.refresh.side_effect = mock_refresh

        # Create voice to test
        voice = Voice(
            el_voice_id="el_voice_1",
            name="Test Voice",
            accent="Standard",
            gender="female",
            age="adult",
            descriptive="calm",
            use_case="narration",
            category="generated",
            language="en",
            locale="en-US",
            description="A test voice",
            preview_url="http://example.com/preview.mp3",
            verified_languages={"en": True},
            popularity_score=80,
        )

        # Exercise
        result = voice_repository.create(voice)

        # Verify
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        assert result.id == 1
        assert result.el_voice_id == "el_voice_1"
        assert result.name == "Test Voice"

    def test_get(self, voice_repository, mock_session, mock_voice_model):
        """Test getting a voice by ID."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_voice_model

        # Exercise
        result = voice_repository.get(1)

        # Verify
        mock_session.query.assert_called_once_with(VoiceModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        assert result.id == 1
        assert result.el_voice_id == "el_voice_1"

    def test_get_not_found(self, voice_repository, mock_session):
        """Test getting a non-existent voice returns None."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Exercise
        result = voice_repository.get(999)

        # Verify
        assert result is None

    def test_get_by_elevenlabs_id(self, voice_repository, mock_session, mock_voice_model):
        """Test getting a voice by ElevenLabs voice ID."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_voice_model

        # Exercise
        result = voice_repository.get_by_elevenlabs_id("el_voice_1")

        # Verify
        mock_session.query.assert_called_once_with(VoiceModel)
        query_mock.filter_by.assert_called_once_with(el_voice_id="el_voice_1")
        assert result.id == 1
        assert result.el_voice_id == "el_voice_1"

    def test_list(self, voice_repository, mock_session, mock_voice_model):
        """Test listing voices."""
        # Configure mock behavior
        mock_voice2 = MagicMock(spec=VoiceModel)
        mock_voice2.id = 2
        mock_voice2.el_voice_id = "el_voice_2"
        mock_voice2.name = "Another Voice"
        mock_voice2.accent = "British"
        mock_voice2.gender = "male"
        mock_voice2.age = "young"
        mock_voice2.descriptive = "energetic"
        mock_voice2.use_case = "podcast"
        mock_voice2.category = "premium"
        mock_voice2.language = "en"
        mock_voice2.locale = "en-GB"
        mock_voice2.description = "Another test voice"
        mock_voice2.preview_url = "http://example.com/preview2.mp3"
        mock_voice2.verified_languages = {"en": True}
        mock_voice2.popularity_score = 90
        mock_voice2.last_updated = MagicMock()

        query_mock = mock_session.query.return_value
        query_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            mock_voice_model,
            mock_voice2,
        ]

        # Exercise
        result = voice_repository.list()

        # Verify
        mock_session.query.assert_called_once_with(VoiceModel)
        query_mock.order_by.assert_called_once()
        query_mock.limit.assert_called_once_with(100)
        query_mock.offset.assert_called_once_with(0)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2

    def test_list_with_filters(self, voice_repository, mock_session, mock_voice_model):
        """Test listing voices with filters."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        # Chain filter_by calls
        query_mock.filter.return_value = query_mock  # Allow chaining filter calls
        query_mock.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [
            mock_voice_model
        ]

        # Exercise
        result = voice_repository.list(gender="female", language="en", use_case="narration")

        # Verify
        mock_session.query.assert_called_once_with(VoiceModel)
        # Check if filter calls were made correctly - Use ANY for the complex expression
        query_mock.filter.assert_has_calls(
            [
                call(ANY),  # Check for call with gender filter expression
                call(ANY),  # Check for call with language filter expression
                call(ANY),  # Check for call with use_case filter expression
            ],
            any_order=True,  # The order of filters doesn't matter
        )
        query_mock.order_by.assert_called_once()
        assert len(result) == 1
        assert result[0].gender == "female"

    def test_update(self, voice_repository, mock_session, mock_voice_model):
        """Test updating a voice."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_voice_model

        # Create voice to update
        voice = Voice(
            id=1,
            el_voice_id="el_voice_1_updated",
            name="Updated Voice",
            accent="British",
            gender="male",
            age="young",
            descriptive="energetic",
            use_case="podcast",
            category="premium",
            language="en",
            locale="en-GB",
            description="Updated description",
            preview_url="http://example.com/updated_preview.mp3",
            verified_languages={"en": False},
            popularity_score=90,
        )

        # Exercise
        result = voice_repository.update(voice)

        # Verify
        mock_session.query.assert_called_once_with(VoiceModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        mock_session.commit.assert_called_once()

        # Check that the model was updated with new values
        assert mock_voice_model.el_voice_id == "el_voice_1_updated"
        assert mock_voice_model.name == "Updated Voice"
        assert mock_voice_model.accent == "British"
        assert mock_voice_model.gender == "male"
        assert mock_voice_model.age == "young"
        assert mock_voice_model.descriptive == "energetic"
        assert mock_voice_model.use_case == "podcast"
        assert mock_voice_model.category == "premium"
        assert mock_voice_model.language == "en"
        assert mock_voice_model.locale == "en-GB"
        assert mock_voice_model.description == "Updated description"
        assert mock_voice_model.preview_url == "http://example.com/updated_preview.mp3"
        assert mock_voice_model.verified_languages == {"en": False}
        assert mock_voice_model.popularity_score == 90

        # Check that the returned voice has the updated values
        assert result.id == 1
        assert result.el_voice_id == "el_voice_1_updated"

    def test_update_not_found(self, voice_repository, mock_session):
        """Test updating a non-existent voice raises an error."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Create voice to update
        voice = Voice(
            id=999,
            el_voice_id="el_voice_999",
            name="Non Existent Voice",
            accent="Standard",
            gender="female",
            age="adult",
            descriptive="calm",
            use_case="narration",
            category="generated",
            language="en",
            locale="en-US",
            description="A voice that doesn't exist",
            preview_url="http://example.com/preview.mp3",
            verified_languages={"en": True},
            popularity_score=80,
        )

        # Exercise & Verify
        with pytest.raises(ValueError, match="Voice with ID 999 not found"):
            voice_repository.update(voice)

    def test_upsert_create(self, voice_repository, mock_session):
        """Test upsert creates a voice if ElevenLabs ID not found."""
        # Configure mock behaviors
        # Mock get_by_elevenlabs_id to return None (voice not found)

        # Mock create to return a voice with an ID
        created_voice = Voice(
            id=1,
            el_voice_id="el_voice_new",
            name="New Voice",
            accent="Standard",
            gender="female",
            age="adult",
            descriptive="calm",
            use_case="narration",
            category="generated",
            language="en",
            locale="en-US",
            description="A new voice",
            preview_url="http://example.com/new_preview.mp3",
            verified_languages={"en": True},
            popularity_score=80,
        )

        voice_to_upsert = Voice(
            el_voice_id="el_voice_new",
            name="New Voice",
            accent="Standard",
            gender="female",
            age="adult",
            descriptive="calm",
            use_case="narration",
            category="generated",
            language="en",
            locale="en-US",
            description="A new voice",
            preview_url="http://example.com/new_preview.mp3",
            verified_languages={"en": True},
            popularity_score=80,
        )

        # Exercise
        with (
            patch.object(voice_repository, "get_by_elevenlabs_id", return_value=None) as mock_get,
            patch.object(voice_repository, "create", return_value=created_voice) as mock_create,
            patch.object(voice_repository, "update") as mock_update,
        ):  # noqa E129
            result = voice_repository.upsert(voice_to_upsert)

        # Verify
        mock_get.assert_called_once_with("el_voice_new")
        mock_create.assert_called_once_with(voice_to_upsert)
        mock_update.assert_not_called()
        assert result.id == 1
        assert result.el_voice_id == "el_voice_new"

    def test_upsert_update(self, voice_repository, mock_session):
        """Test upsert updates a voice if ElevenLabs ID is found."""
        # Configure mock behaviors
        # Mock get_by_elevenlabs_id to return an existing voice
        existing_voice = Voice(
            id=1,
            el_voice_id="el_voice_existing",
            name="Existing Voice",
            accent="Standard",
            gender="female",
            age="adult",
            descriptive="calm",
            use_case="narration",
            category="generated",
            language="en",
            locale="en-US",
            description="An existing voice",
            preview_url="http://example.com/existing_preview.mp3",
            verified_languages={"en": True},
            popularity_score=80,
        )

        # Mock update to return the updated voice
        updated_voice = Voice(
            id=1,
            el_voice_id="el_voice_existing",
            name="Updated Existing Voice",
            accent="British",
            gender="male",
            age="young",
            descriptive="energetic",
            use_case="podcast",
            category="premium",
            language="en",
            locale="en-GB",
            description="Updated existing description",
            preview_url="http://example.com/updated_existing_preview.mp3",
            verified_languages={"en": False},
            popularity_score=90,
        )

        voice_to_upsert = Voice(
            el_voice_id="el_voice_existing",
            name="Updated Existing Voice",
            accent="British",
            gender="male",
            age="young",
            descriptive="energetic",
            use_case="podcast",
            category="premium",
            language="en",
            locale="en-GB",
            description="Updated existing description",
            preview_url="http://example.com/updated_existing_preview.mp3",
            verified_languages={"en": False},
            popularity_score=90,
        )

        # Exercise
        with (
            patch.object(
                voice_repository, "get_by_elevenlabs_id", return_value=existing_voice
            ) as mock_get,
            patch.object(voice_repository, "create") as mock_create,
            patch.object(voice_repository, "update", return_value=updated_voice) as mock_update,
        ):  # noqa E129
            result = voice_repository.upsert(voice_to_upsert)

        # Verify
        mock_get.assert_called_once_with("el_voice_existing")
        mock_create.assert_not_called()
        # Ensure the update call receives the voice with the ID from the existing voice
        voice_to_upsert.id = existing_voice.id  # Set the ID for the update call
        mock_update.assert_called_once_with(voice_to_upsert)

        assert result.id == 1
        assert result.name == "Updated Existing Voice"
