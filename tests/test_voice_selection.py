"""
Tests for the ElevenLabs voice selection integration.
"""

import os
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
import json

from artificial_u.models.core import Professor
from artificial_u.integrations.elevenlabs import (
    VoiceSelectionManager,
    get_voice_for_professor,
    sample_voices,
    get_voice_filters,
)


class TestVoiceSelectionManager(unittest.TestCase):
    """Test cases for the VoiceSelectionManager."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock for the ElevenLabs client
        self.patcher = patch("artificial_u.integrations.elevenlabs.ElevenLabs")
        self.MockClient = self.patcher.start()
        self.mock_client_instance = self.MockClient.return_value

        # Setup mock voices response
        self.mock_voices = MagicMock()
        self.mock_voices.voices = []
        self.mock_client_instance.voices.get_all.return_value = self.mock_voices

        # Mock the requests.get for shared voices API
        self.requests_patcher = patch(
            "artificial_u.integrations.elevenlabs.requests.get"
        )
        self.mock_requests_get = self.requests_patcher.start()

        # Setup default mock response for shared voices API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"voices": [], "has_more": False}
        self.mock_requests_get.return_value = mock_response

        # Create temp directory for cache files
        self.temp_cache_dir = Path("./.test_cache")
        self.temp_cache_dir.mkdir(exist_ok=True)

        # Patch the CACHE_DIR
        self.cache_patcher = patch(
            "artificial_u.integrations.elevenlabs.CACHE_DIR", self.temp_cache_dir
        )
        self.cache_patcher.start()

        # Patch the VOICE_CACHE_FILE
        self.voice_cache_patcher = patch(
            "artificial_u.integrations.elevenlabs.VOICE_CACHE_FILE",
            self.temp_cache_dir / "voice_data.json",
        )
        self.voice_cache_patcher.start()

        # Mock environment variable
        os.environ["ELEVENLABS_API_KEY"] = "test_api_key"

        # Create sample professor
        self.professor = Professor(
            id="prof123",
            name="Dr. Jane Smith",
            title="Professor of Physics",
            department="Physics",
            specialization="Quantum Mechanics",
            background="British physicist with 20 years of experience. She completed her PhD at Oxford.",
            personality="Passionate and enthusiastic",
            teaching_style="Engaging and interactive",
        )

    def tearDown(self):
        """Tear down test fixtures."""
        self.patcher.stop()
        self.cache_patcher.stop()
        self.voice_cache_patcher.stop()
        self.requests_patcher.stop()

        # Clean up test cache files
        for file in self.temp_cache_dir.glob("*"):
            file.unlink()
        self.temp_cache_dir.rmdir()

    def test_initialization(self):
        """Test manager initialization."""
        manager = VoiceSelectionManager()
        self.assertEqual(manager.api_key, "test_api_key")
        self.MockClient.assert_called_once_with(api_key="test_api_key")

    def test_get_available_voices(self):
        """Test retrieving available voices."""
        # Setup mock response for shared voices API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": [
                {
                    "voice_id": "voice1",
                    "name": "Voice One",
                    "description": "Female British voice",
                    "category": "premade",
                    "gender": "female",
                    "accent": "british",
                    "age": "middle_aged",
                    "use_case": "informative_educational",
                    "cloned_by_count": 2000,
                },
                {
                    "voice_id": "voice2",
                    "name": "Voice Two",
                    "description": "Male American voice",
                    "category": "cloned",
                    "gender": "male",
                    "accent": "american",
                    "age": "young",
                    "use_case": "conversational",
                    "cloned_by_count": 1000,
                },
            ],
            "has_more": False,
        }
        self.mock_requests_get.return_value = mock_response

        # Test getting voices
        manager = VoiceSelectionManager()
        voices = manager.get_available_voices(refresh=True)

        # Verify results
        self.assertEqual(len(voices), 2)
        self.assertEqual(voices[0]["voice_id"], "voice1")
        self.assertEqual(voices[0]["gender"], "female")
        self.assertEqual(voices[0]["accent"], "british")
        self.assertEqual(voices[1]["voice_id"], "voice2")
        self.assertEqual(voices[1]["gender"], "male")
        self.assertEqual(voices[1]["accent"], "american")

        # Verify API was called with correct parameters
        self.mock_requests_get.assert_called_once()
        call_args = self.mock_requests_get.call_args
        self.assertEqual(call_args[0][0], "https://api.elevenlabs.io/v1/shared-voices")

    def test_extract_gender_from_professor(self):
        """Test gender extraction from professor profile."""
        manager = VoiceSelectionManager()

        # Test male indicators
        prof_male = Professor(
            name="Dr. John Smith",
            title="Professor",
            department="Physics",
            specialization="Quantum Mechanics",
            background="He studied at MIT before joining the faculty.",
            personality="Enthusiastic",
            teaching_style="Interactive",
        )
        self.assertEqual(manager._extract_gender_from_professor(prof_male), "male")

        # Test female indicators
        prof_female = Professor(
            name="Dr. Mary Johnson",
            title="Professor",
            department="Biology",
            specialization="Genetics",
            background="She earned her PhD from Stanford University.",
            personality="Patient",
            teaching_style="Thorough",
        )
        self.assertEqual(manager._extract_gender_from_professor(prof_female), "female")

        # Test name-based detection
        prof_name_only = Professor(
            name="Elizabeth Taylor",
            title="Professor",
            department="Chemistry",
            specialization="Organic Chemistry",
            background="Graduated with honors.",
            personality="Detail-oriented",
            teaching_style="Structured",
        )
        self.assertEqual(
            manager._extract_gender_from_professor(prof_name_only), "female"
        )

    def test_extract_accent_from_professor(self):
        """Test accent extraction from professor profile."""
        manager = VoiceSelectionManager()

        # Test explicit nationality mention
        prof_british = Professor(
            name="Dr. Smith",
            title="Professor",
            department="English",
            specialization="Literature",
            background="British scholar who studied at Oxford University.",
            personality="Reserved",
            teaching_style="Traditional",
        )
        self.assertEqual(
            manager._extract_accent_from_professor(prof_british), "british"
        )

        # Test city-based detection
        prof_french = Professor(
            name="Dr. Dupont",
            title="Professor",
            department="Art History",
            specialization="Renaissance Art",
            background="Studied in Paris and taught at the Sorbonne.",
            personality="Passionate",
            teaching_style="Visual",
        )
        self.assertEqual(manager._extract_accent_from_professor(prof_french), "french")

        # Test no clear accent
        prof_no_accent = Professor(
            name="Dr. Lee",
            title="Professor",
            department="Mathematics",
            specialization="Topology",
            background="Award-winning researcher and educator.",
            personality="Methodical",
            teaching_style="Step-by-step",
        )
        self.assertIsNone(manager._extract_accent_from_professor(prof_no_accent))

    def test_extract_age_from_professor(self):
        """Test age extraction from professor profile."""
        manager = VoiceSelectionManager()

        # Test explicit age mention
        prof_young = Professor(
            name="Dr. Smith",
            title="Assistant Professor",
            department="Computer Science",
            specialization="Machine Learning",
            background="32-year-old researcher who recently joined the faculty.",
            personality="Energetic",
            teaching_style="Hands-on",
        )
        self.assertEqual(manager._extract_age_from_professor(prof_young), "young")

        # Test position-based detection
        prof_senior = Professor(
            name="Dr. Williams",
            title="Distinguished Professor",
            department="History",
            specialization="Medieval Europe",
            background="Emeritus faculty member with decades of experience.",
            personality="Wise",
            teaching_style="Storytelling",
        )
        self.assertEqual(manager._extract_age_from_professor(prof_senior), "old")

        # Test default middle-aged
        prof_default = Professor(
            name="Dr. Johnson",
            title="Associate Professor",
            department="Economics",
            specialization="Behavioral Economics",
            background="Award-winning economist.",
            personality="Analytical",
            teaching_style="Discussion-based",
        )
        self.assertEqual(
            manager._extract_age_from_professor(prof_default), "middle_aged"
        )

    def test_voice_for_professor(self):
        """Test getting a voice for a professor."""
        # Setup mock response for shared voices API with voices matching the professor
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": [
                {
                    "voice_id": "voice1",
                    "name": "Voice One",
                    "description": "Female British voice",
                    "category": "high_quality",
                    "gender": "female",
                    "accent": "british",
                    "age": "middle_aged",
                    "quality_score": 0.8,
                }
            ],
            "has_more": False,
        }
        self.mock_requests_get.return_value = mock_response

        # Create manager
        manager = VoiceSelectionManager()

        # Create a new professor that should match the mock voice
        professor = Professor(
            id="prof_test",
            name="Dr. Smith",
            title="Professor",
            department="Physics",
            specialization="Quantum Mechanics",
            background="British female physicist.",
            personality="Enthusiastic",
            teaching_style="Interactive",
        )

        # Get voice for professor
        voice = manager.get_voice_for_professor(professor)

        # Verify the correct voice was selected
        self.assertEqual(voice["voice_id"], "voice1")

        # Verify it was saved in the mapping
        self.assertIn("prof_test", manager.voice_mapping_db)
        self.assertEqual(manager.voice_mapping_db["prof_test"], "voice1")

        # Test with different professor where no voice matches all criteria
        professor2 = Professor(
            id="prof_test2",
            name="Dr. Zhang",
            title="Professor",
            department="Mathematics",
            specialization="Number Theory",
            background="Chinese mathematician with teaching experience in Beijing.",
            personality="Precise",
            teaching_style="Methodical",
        )

        # Mock filter_voices to simulate no exact matches
        with patch.object(VoiceSelectionManager, "filter_voices") as mock_filter:
            # First call (all criteria) returns empty list
            # Second call (gender+accent) returns our voice
            mock_filter.side_effect = [
                [],
                [{"voice_id": "voice1", "name": "Voice One"}],
            ]

            voice2 = manager.get_voice_for_professor(professor2)

            # Verify fallback worked
            self.assertEqual(voice2["voice_id"], "voice1")

    @patch("artificial_u.integrations.elevenlabs.VoiceSelectionManager")
    def test_convenience_functions(self, MockManager):
        """Test the convenience functions."""
        # Setup mock manager and responses
        mock_manager_instance = MockManager.return_value
        voices = [{"voice_id": "test1"}, {"voice_id": "test2"}, {"voice_id": "test3"}]
        mock_manager_instance.get_voice_for_professor.return_value = {
            "voice_id": "test1"
        }
        mock_manager_instance.sample_voices_by_criteria.return_value = voices
        mock_manager_instance.list_available_voice_filters.return_value = {
            "genders": ["male", "female"],
            "accents": ["american", "british"],
        }

        # Test get_voice_for_professor
        prof = Professor(
            name="Test Professor",
            title="Professor",
            department="Test",
            specialization="Test",
            background="Test background",
            personality="Test personality",
            teaching_style="Test style",
        )

        result = get_voice_for_professor(prof, api_key="test_key")
        self.assertEqual(result["voice_id"], "test1")
        MockManager.assert_called_with(api_key="test_key")
        mock_manager_instance.get_voice_for_professor.assert_called_with(prof)

        # Test sample_voices
        result = sample_voices(
            count=3, gender="male", accent="test", api_key="test_key"
        )
        self.assertEqual(result, voices)

        # Check that the manager was initialized with the correct API key
        MockManager.assert_called_with(api_key="test_key")

        # Check that the correct methods were called
        mock_manager_instance.sample_voices_by_criteria.assert_called_with(
            count=3,
            gender="male",
            accent="test",
        )

        # Test get_voice_filters
        result = get_voice_filters(api_key="test_key")
        self.assertEqual(
            result, {"genders": ["male", "female"], "accents": ["american", "british"]}
        )
        MockManager.assert_called_with(api_key="test_key")
        mock_manager_instance.list_available_voice_filters.assert_called_once()


if __name__ == "__main__":
    unittest.main()
