"""
ElevenLabs API client for ArtificialU.

Provides low-level access to the ElevenLabs API for text-to-speech and voice management.
"""

import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

from elevenlabs import play
from elevenlabs.client import ElevenLabs

from artificial_u.config import get_settings


class ElevenLabsClient:
    """
    Low-level client for interacting with ElevenLabs API.
    Provides direct access to API endpoints with minimal business logic.
    """

    # ElevenLabs API base URL
    BASE_URL = "https://api.elevenlabs.io/v1"

    # Shared voices API endpoint
    SHARED_VOICES_URL = f"{BASE_URL}/shared-voices"

    # Maximum retries for API calls
    MAX_RETRIES = 3

    # Wait time between retries (seconds)
    RETRY_WAIT = 2

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ElevenLabs client.

        Args:
            api_key: ElevenLabs API key. If not provided, will use
                ELEVENLABS_API_KEY environment variable.
        """
        self.logger = logging.getLogger(__name__)

        # Check if we're in a test environment
        in_test_env = os.environ.get("TESTING") == "true" or "pytest" in sys.modules

        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            if in_test_env:
                # Use a dummy key in test environment
                self.api_key = "test_elevenlabs_key"
                self.logger.info("Using test API key in test environment")
            else:
                # Only raise error in production
                raise ValueError("ElevenLabs API key is required")

        # Initialize standard ElevenLabs client
        try:
            self.client = ElevenLabs(api_key=self.api_key)
            self.logger.debug("Successfully initialized ElevenLabs client")
        except Exception as e:
            if in_test_env:
                self.logger.info(f"Test environment: Mocking ElevenLabs client due to error: {e}")
                # Create a dummy client for testing
                self.client = MagicMock()
            else:
                self.logger.error(f"Failed to initialize ElevenLabs client: {e}")
                raise

        # Headers for API requests
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    """
    Get details of a specific voice by ElevenLabs voice ID.

    Args:
        el_voice_id: ElevenLabs Voice ID of the voice to retrieve

    Returns:
        Voice details or None if not found
    """

    def get_el_voice(self, el_voice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific voice.

        Args:
            voice_id: ElevenLabs Voice ID of the voice to retrieve

        Returns:
            Voice details or None if not found
        """
        try:
            response = self.client.voices.get(voice_id=el_voice_id)

            voice_data = {
                "el_voice_id": response.voice_id,
                "name": response.name,
                "category": getattr(response, "category", "premade"),
                "gender": getattr(response, "labels", {}).get("gender", "neutral"),
                "accent": getattr(response, "labels", {}).get("accent", "american"),
                "age": getattr(response, "labels", {}).get("age", "middle_aged"),
                "description": getattr(response, "description", ""),
                "preview_url": getattr(response, "preview_url", ""),
            }

            return voice_data
        except Exception as e:
            self.logger.error(f"Error retrieving ElevenLabs voice {el_voice_id}: {e}")
            return None

    def get_shared_voices(
        self,
        page_size: int = 100,
        page: int = 0,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        language: str = "en",
        use_case: Optional[str] = None,
        category: Optional[str] = None,
        search: Optional[str] = None,
        min_notice_period_days: Optional[int] = None,
        featured: Optional[bool] = None,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Get shared voices from the ElevenLabs API.

        Args:
            page_size: Number of results per page (max 100)
            page: Page number
            gender: Optional filter by gender
            accent: Optional filter by accent
            age: Optional filter by age
            language: Language code
            use_case: Optional filter by use case
            category: Optional filter by category
            search: Optional search term
            min_notice_period_days: Optional minimum notice period in days
            featured: Optional filter for featured voices

        Returns:
            Tuple of (list of voice data, has_more flag)
        """
        try:
            # Call the client library method
            response = self.client.voices.get_shared(
                page_size=min(page_size, 100),
                page=page,
                gender=gender,
                accent=accent,
                age=age,
                language=language,
                use_cases=use_case,
                category=category,
                search=search,
                min_notice_period_days=min_notice_period_days,
                featured=featured,
            )

            # Extract data from response
            voices = response.voices
            has_more = getattr(response, "has_more", False)

            # Format the voice data to standardized format
            formatted_voices = []
            for voice in voices:
                # Filter out voices with non-null rate or fiat_rate
                rate = getattr(voice, "rate", None)
                fiat_rate = getattr(voice, "fiat_rate", None)

                # Skip voices that cost extra
                if rate is not None and rate != 1.0:
                    continue
                if fiat_rate is not None:
                    continue

                formatted_voices.append(
                    {
                        "el_voice_id": voice.voice_id,  # Fixed: use consistent field name
                        "name": voice.name,
                        "gender": getattr(voice, "gender", None),
                        "accent": getattr(voice, "accent", None),
                        "age": getattr(voice, "age", None),
                        "descriptive": getattr(voice, "descriptive", None),
                        "use_case": getattr(voice, "use_case", None),
                        "category": getattr(voice, "category", None),
                        "language": getattr(voice, "language", None),
                        "locale": getattr(voice, "locale", None),
                        "description": getattr(voice, "description", ""),
                        "preview_url": getattr(voice, "preview_url", ""),
                        "verified_languages": getattr(voice, "verified_languages", []),
                        "cloned_by_count": getattr(voice, "cloned_by_count", 0),
                        "usage_character_count_1y": getattr(voice, "usage_character_count_1y", 0),
                    }
                )

            return formatted_voices, has_more
        except Exception as e:
            self.logger.error(f"Error retrieving shared voices: {e}")
            return [], False

    def get_premade_voices(self) -> List[Dict[str, Any]]:
        """
        Get all available voices from the v2/voices endpoint.
        This includes premade official voices and voices in the user's library.

        Returns:
            List of voice data dictionaries
        """
        try:
            # Get all voices from the v2 endpoint
            response = self.client.voices.get_all()

            formatted_voices = []
            for voice in response.voices:
                # Check if we should filter out paid voices
                sharing = getattr(voice, "sharing", None)
                if sharing:
                    # Filter out voices with non-null rate or fiat_rate
                    if (
                        getattr(sharing, "rate", None) is not None
                        and getattr(sharing, "rate", 1.0) != 1.0
                    ):
                        continue
                    if getattr(sharing, "fiat_rate", None) is not None:
                        continue

                # Get labels - for premade voices, these contain the attributes
                labels = getattr(voice, "labels", {})

                # Format the voice data
                formatted_voices.append(
                    {
                        "el_voice_id": voice.voice_id,
                        "name": voice.name,
                        "category": getattr(voice, "category", "unknown"),
                        "gender": labels.get("gender", None),
                        "accent": labels.get("accent", None),
                        "age": labels.get("age", None),
                        "descriptive": labels.get("descriptive", None),
                        "use_case": labels.get("use_case", None),
                        "language": labels.get("language", "en"),
                        "locale": None,  # Not available in v2 endpoint
                        "description": getattr(voice, "description", ""),
                        "preview_url": getattr(voice, "preview_url", ""),
                        "verified_languages": getattr(voice, "verified_languages", []),
                        "cloned_by_count": 0,  # Not available for premade voices
                        "usage_character_count_1y": 0,  # Not available for premade voices
                    }
                )

            self.logger.info(f"Retrieved {len(formatted_voices)} voices from v2/voices endpoint")
            return formatted_voices

        except Exception as e:
            self.logger.error(f"Error retrieving premade voices: {e}")
            return []

    def test_connection(self) -> Dict[str, Any]:
        """
        Tests the connection to ElevenLabs API and verifies authentication.

        Returns:
            Dictionary with connection status and API information
        """
        try:
            # Try to get user info as a connectivity test
            user_info = self.client.user.get()

            # Try to get available voices
            voices = self.client.voices.get_all()
            voice_count = len(voices.voices) if hasattr(voices, "voices") else 0

            return {
                "status": "connected",
                "subscription_tier": (
                    getattr(user_info.subscription, "tier", "unknown")
                    if hasattr(user_info, "subscription")
                    else "unknown"
                ),
                "available_voices": voice_count,
                "api_version": getattr(self.client, "version", "unknown"),
            }
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    def text_to_speech(
        self,
        text: str,
        voice_id: str,
        model_id: Optional[str] = None,
        voice_settings: Optional[Dict[str, float]] = None,
    ) -> bytes:
        """
        Convert text to speech using ElevenLabs API.

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs Voice ID to use
            model_id: Model ID to use (defaults to eleven_flash_v2_5)
            voice_settings: Voice settings (stability, speed, etc.)

        Returns:
            Audio data as bytes
        """
        # Default to globally configured model
        model_id = model_id or get_settings().TTS_VOICE_MODEL

        # Retry logic for API calls
        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.debug(f"TTS attempt {attempt+1} for text of length {len(text)}")

                # Get audio stream from the API
                # Follow official SDK example to ensure full audio is returned
                # Ref: https://elevenlabs.io/docs/api-reference/text-to-speech/convert
                audio_stream = self.client.text_to_speech.convert(
                    voice_id=voice_id,
                    output_format="mp3_44100_128",
                    text=text,
                    model_id=model_id,
                    voice_settings=voice_settings,
                    # Keep default apply_text_normalization behavior (auto)
                )

                audio_data = self._consume_audio_stream(audio_stream)
                self._warn_if_suspicious_audio(audio_data, len(text))
                return audio_data

            except Exception as e:
                self.logger.error(f"Error in text-to-speech conversion: {str(e)}")
                if attempt < self.MAX_RETRIES - 1:
                    self.logger.info(f"Waiting {self.RETRY_WAIT}s before retry...")
                    time.sleep(self.RETRY_WAIT)
                else:
                    self.logger.error(f"Failed after {self.MAX_RETRIES} attempts")
                    raise

    def _consume_audio_stream(self, audio_stream: Any) -> bytes:
        """Consume audio stream or return bytes, compatible with SDK variations."""
        if hasattr(audio_stream, "__iter__") and not isinstance(audio_stream, (bytes, bytearray)):
            self.logger.debug("Audio stream is a generator, consuming it")
            audio_chunks: List[bytes] = []
            for chunk in audio_stream:
                if isinstance(chunk, (bytes, bytearray)):
                    audio_chunks.append(bytes(chunk))
            return b"".join(audio_chunks)
        self.logger.debug("Audio stream is bytes data")
        return bytes(audio_stream)

    def _warn_if_suspicious_audio(self, audio_data: bytes, text_len: int) -> None:
        """Warn if very long text produced unrealistically small audio output."""
        if len(audio_data) < 16000 and text_len > 500:
            self.logger.warning(
                "Unexpectedly small audio returned: %d bytes for %d chars. "
                "Text may contain unsupported markup or the request failed silently.",
                len(audio_data),
                text_len,
            )

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the current ElevenLabs user.

        Returns:
            Dictionary with user information
        """
        try:
            user = self.client.user.get()

            return {
                "tier": (user.subscription.tier if hasattr(user, "subscription") else "unknown"),
                "character_limit": getattr(user.subscription, "character_limit", 0),
                "character_count": getattr(user.subscription, "character_count", 0),
                "available_characters": getattr(user.subscription, "character_limit", 0)
                - getattr(user.subscription, "character_count", 0),
            }
        except Exception as e:
            self.logger.error(f"Error retrieving user info: {e}")
            return {}

    def play_audio(self, audio_data: bytes) -> None:
        """
        Play audio using the ElevenLabs play function.

        Args:
            audio_data: Audio data as bytes
        """
        try:
            play(audio_data)
        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
            raise
