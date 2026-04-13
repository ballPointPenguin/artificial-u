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

import httpx
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

        First tries to fetch from the user's voice library (v1/voices endpoint).
        If not found, falls back to searching shared voices (v1/shared-voices endpoint).

        Args:
            el_voice_id: ElevenLabs Voice ID of the voice to retrieve

        Returns:
            Voice details or None if not found
        """
        # Step 1: Try to get from user's library (works for library + premade voices)
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

            self.logger.debug(f"Found voice {el_voice_id} in user's library")
            return voice_data
        except Exception as e:
            # Check if it's a "voice_not_found" error before falling back
            error_str = str(e).lower()
            if "voice_not_found" not in error_str and "not found" not in error_str:
                # Some other error, log and return None
                self.logger.error(f"Error retrieving ElevenLabs voice {el_voice_id}: {e}")
                return None

            self.logger.debug(
                f"Voice {el_voice_id} not in user's library, searching shared voices..."
            )

        # Step 2: Fall back to searching shared voices
        return self._search_shared_voice_by_id(el_voice_id)

    def _search_shared_voice_by_id(
        self, el_voice_id: str, max_pages: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        Search shared voices to find a specific voice by ID.

        The shared-voices endpoint doesn't support direct ID lookup, so we
        paginate through results looking for a match. Searches popular voices
        first (sorted by usage) since those are most likely to appear in the UI.

        Args:
            el_voice_id: ElevenLabs Voice ID to search for
            max_pages: Maximum number of pages to search (default 20 = ~2000 voices)

        Returns:
            Voice details or None if not found
        """
        page = 0
        page_size = 100  # Max allowed by API

        while page < max_pages:
            try:
                # Sort by usage count - popular voices are more likely to be
                # the ones users find and copy from the ElevenLabs UI
                response = self.client.voices.get_shared(
                    page_size=page_size,
                    page=page,
                    language="en",  # Start with English to narrow search
                    sort="usage_character_count_1y",  # Most used voices first
                )

                voices = response.voices
                has_more = getattr(response, "has_more", False)

                # Search for matching voice_id
                for voice in voices:
                    if voice.voice_id == el_voice_id:
                        self.logger.info(
                            f"Found voice {el_voice_id} in shared voices (page {page})"
                        )
                        return {
                            "el_voice_id": voice.voice_id,
                            "name": voice.name,
                            "category": getattr(voice, "category", "shared"),
                            "gender": getattr(voice, "gender", "neutral"),
                            "accent": getattr(voice, "accent", "american"),
                            "age": getattr(voice, "age", "middle_aged"),
                            "description": getattr(voice, "description", ""),
                            "preview_url": getattr(voice, "preview_url", ""),
                        }

                if not has_more:
                    break

                page += 1

            except Exception as e:
                self.logger.error(f"Error searching shared voices (page {page}): {e}")
                break

        # If not found in English voices, try without language filter
        self.logger.debug(
            f"Voice {el_voice_id} not found in English shared voices "
            f"(searched {page + 1} pages), trying all languages..."
        )
        return self._search_shared_voice_all_languages(el_voice_id, max_pages=10)

    def _search_shared_voice_all_languages(
        self, el_voice_id: str, max_pages: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Search shared voices without language filter.

        Args:
            el_voice_id: ElevenLabs Voice ID to search for
            max_pages: Maximum number of pages to search

        Returns:
            Voice details or None if not found
        """
        page = 0
        page_size = 100

        while page < max_pages:
            try:
                # Search without language filter, sorted by popularity
                response = self.client.voices.get_shared(
                    page_size=page_size,
                    page=page,
                    sort="usage_character_count_1y",
                )

                voices = response.voices
                has_more = getattr(response, "has_more", False)

                for voice in voices:
                    if voice.voice_id == el_voice_id:
                        self.logger.info(
                            f"Found voice {el_voice_id} in shared voices "
                            f"(all languages, page {page})"
                        )
                        return {
                            "el_voice_id": voice.voice_id,
                            "name": voice.name,
                            "category": getattr(voice, "category", "shared"),
                            "gender": getattr(voice, "gender", "neutral"),
                            "accent": getattr(voice, "accent", "american"),
                            "age": getattr(voice, "age", "middle_aged"),
                            "description": getattr(voice, "description", ""),
                            "preview_url": getattr(voice, "preview_url", ""),
                        }

                if not has_more:
                    break

                page += 1

            except Exception as e:
                self.logger.error(f"Error searching shared voices all languages (page {page}): {e}")
                break

        self.logger.warning(
            f"Voice {el_voice_id} not found. Searched user library and "
            f"~{(page + 1) * page_size} shared voices. The voice may be private, "
            "removed, or in a less popular category."
        )
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

    # ---------------------------------------------------------------------------
    # Voice Design (text-to-voice) API
    # ---------------------------------------------------------------------------

    # Default sample text used when generating voice previews
    VOICE_DESIGN_PREVIEW_TEXT = (
        "Welcome to Artificial University. "
        "Today we will explore ideas that challenge our assumptions "
        "and deepen our understanding of the world around us."
    )

    def generate_voice_previews(
        self,
        voice_description: str,
        text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate voice previews using the ElevenLabs Voice Design API.

        Calls POST /v1/text-to-voice/create-previews.

        Args:
            voice_description: Prose description of the desired voice.
            text: Optional text to synthesise in the preview.
                  Defaults to a short academic sentence.

        Returns:
            List of preview dicts, each containing:
            ``generated_voice_id`` (str), ``audio_sample`` (base64 str),
            ``media_type`` (str), ``duration_secs`` (float).
        """
        url = f"{self.BASE_URL}/text-to-voice/create-previews"
        payload: Dict[str, Any] = {
            "voice_description": voice_description,
            "text": text or self.VOICE_DESIGN_PREVIEW_TEXT,
            # Recommended model for voice design
            "model_id": "eleven_multilingual_ttv_v2",
        }

        try:
            with httpx.Client(timeout=90) as http:
                resp = http.post(url, json=payload, headers=self.headers)
                resp.raise_for_status()
                data = resp.json()
            raw_previews = data.get("previews", [])
            self.logger.info("Voice Design: received %d preview(s)", len(raw_previews))
            # Normalise field name: ElevenLabs returns audio_base_64; we expose audio_sample
            previews = []
            for p in raw_previews:
                preview = dict(p)
                if "audio_base_64" in preview and "audio_sample" not in preview:
                    preview["audio_sample"] = preview.pop("audio_base_64")
                previews.append(preview)
            return previews
        except httpx.HTTPStatusError as e:
            self.logger.error(
                "Voice Design preview request failed (%s): %s",
                e.response.status_code,
                e.response.text,
            )
            raise
        except Exception as e:
            self.logger.error("Voice Design preview generation failed: %s", e)
            raise

    def save_voice_to_library(
        self,
        generated_voice_id: str,
        voice_name: str,
        voice_description: str,
    ) -> str:
        """Save a Voice Design preview to the ElevenLabs voice library.

        Calls POST /v1/text-to-voice/create-voice-from-preview.

        Args:
            generated_voice_id: Temporary ID returned by ``generate_voice_previews``.
            voice_name: Name to give the saved voice in the library.
            voice_description: Description of the voice (stored in the library).

        Returns:
            Permanent ElevenLabs ``voice_id`` string that can be used with TTS.
        """
        url = f"{self.BASE_URL}/text-to-voice/create-voice-from-preview"
        payload: Dict[str, Any] = {
            "voice_name": voice_name,
            "voice_description": voice_description,
            "generated_voice_id": generated_voice_id,
        }

        try:
            with httpx.Client(timeout=30) as http:
                resp = http.post(url, json=payload, headers=self.headers)
                resp.raise_for_status()
                data = resp.json()
            el_voice_id = data.get("voice_id")
            if not el_voice_id:
                raise ValueError(f"No voice_id in ElevenLabs response: {data}")
            self.logger.info(
                "Voice Design: saved voice '%s' → el_voice_id=%s", voice_name, el_voice_id
            )
            return el_voice_id
        except httpx.HTTPStatusError as e:
            self.logger.error(
                "Failed to save voice to library (%s): %s",
                e.response.status_code,
                e.response.text,
            )
            raise
        except Exception as e:
            self.logger.error("Failed to save voice to library: %s", e)
            raise

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
