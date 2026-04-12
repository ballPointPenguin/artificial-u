"""
Mistral Voice Manager.

Provides voice CRUD operations via the Mistral SDK's audio.voices API.
Supports listing preset/custom voices and creating cloned voices.
"""

import base64
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mistralai.client import Mistral


class MistralVoiceManager:
    """Manages Mistral TTS voices via the SDK.

    Wraps the client.audio.voices.* methods for listing, creating,
    retrieving, and deleting voices.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        if not api_key:
            from artificial_u.config import get_settings

            api_key = getattr(get_settings(), "MISTRAL_API_KEY", None)
        if not api_key:
            raise ValueError("Mistral API key is required for voice management")

        self.logger = logger or logging.getLogger(__name__)
        self._client = Mistral(api_key=api_key)

    def list_voices(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List available voices.

        Note: The Mistral Voices list API accepts only limit/offset — there is
        no type filter. User-created voices may not yet appear (Mistral API
        limitation as of April 2026).

        Args:
            limit: Max results to return.
            offset: Pagination offset.

        Returns:
            List of voice dicts with id, name, languages, gender, etc.
        """
        response = self._client.audio.voices.list(
            limit=limit,
            offset=offset,
        )

        voices = []
        voice_list = getattr(response, "items", None) or getattr(response, "data", [])
        for voice in voice_list:
            voices.append(self._voice_to_dict(voice))

        self.logger.info("Listed %d Mistral voices", len(voices))
        return voices

    def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific voice.

        Args:
            voice_id: The Mistral voice ID.

        Returns:
            Voice dict or None if not found.
        """
        try:
            voice = self._client.audio.voices.get(voice_id=voice_id)
            return self._voice_to_dict(voice)
        except Exception as e:
            self.logger.error("Failed to get Mistral voice %s: %s", voice_id, e)
            return None

    def create_voice(
        self,
        name: str,
        sample_audio_path: Optional[str] = None,
        sample_audio_bytes: Optional[bytes] = None,
        sample_filename: str = "sample.mp3",
        languages: Optional[List[str]] = None,
        gender: Optional[str] = None,
        age: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a custom voice via voice cloning.

        Provide either a file path or raw bytes for the audio sample.
        Mistral requires as little as 2-3 seconds of reference audio.

        Args:
            name: Display name for the voice.
            sample_audio_path: Path to an audio file (mp3, wav, etc.)
            sample_audio_bytes: Raw audio bytes (alternative to path).
            sample_filename: Filename hint for the sample.
            languages: List of language codes (e.g., ["en", "fr"]).
            gender: Voice gender metadata.
            age: Voice age metadata.
            tags: Optional tags for categorization.

        Returns:
            Created voice dict with id, name, etc.

        Raises:
            ValueError: If neither audio path nor bytes are provided.
        """
        if sample_audio_path:
            audio_bytes = Path(sample_audio_path).read_bytes()
            if not sample_filename or sample_filename == "sample.mp3":
                sample_filename = Path(sample_audio_path).name
        elif sample_audio_bytes:
            audio_bytes = sample_audio_bytes
        else:
            raise ValueError("Either sample_audio_path or sample_audio_bytes is required")

        sample_b64 = base64.b64encode(audio_bytes).decode()

        kwargs: Dict[str, Any] = {
            "name": name,
            "sample_audio": sample_b64,
            "sample_filename": sample_filename,
        }
        if languages:
            kwargs["languages"] = languages
        if gender:
            kwargs["gender"] = gender
        if age:
            kwargs["age"] = age
        if tags:
            kwargs["tags"] = tags

        voice = self._client.audio.voices.create(**kwargs)
        result = self._voice_to_dict(voice)
        self.logger.info("Created Mistral voice: %s (id=%s)", name, result.get("id"))
        return result

    def delete_voice(self, voice_id: str) -> bool:
        """Delete a custom voice.

        Args:
            voice_id: The Mistral voice ID to delete.

        Returns:
            True if deleted successfully.
        """
        try:
            self._client.audio.voices.delete(voice_id=voice_id)
            self.logger.info("Deleted Mistral voice: %s", voice_id)
            return True
        except Exception as e:
            self.logger.error("Failed to delete Mistral voice %s: %s", voice_id, e)
            return False

    def _voice_to_dict(self, voice: Any) -> Dict[str, Any]:
        """Convert an SDK voice response object to a plain dict."""
        result: Dict[str, Any] = {}
        for field in ("id", "name", "slug", "languages", "gender", "age", "tags", "color"):
            if hasattr(voice, field):
                result[field] = getattr(voice, field)
        if hasattr(voice, "created_at"):
            result["created_at"] = str(voice.created_at) if voice.created_at else None
        return result
