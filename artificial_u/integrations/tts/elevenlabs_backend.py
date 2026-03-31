"""
ElevenLabs TTS backend adapter.

Wraps the existing ElevenLabsClient to conform to the TTSBackend protocol.
"""

import logging
from typing import Any, Dict, Optional

from artificial_u.config import get_settings
from artificial_u.integrations.elevenlabs.client import ElevenLabsClient


class ElevenLabsTTSBackend:
    """TTS backend implementation for ElevenLabs."""

    DEFAULT_VOICE_SETTINGS: Dict[str, Any] = {
        "similarity_boost": 0.0,
        "speed": 1.0,
        "stability": 0.5,
        "style": 0.0,
        "use_speaker_boost": True,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[ElevenLabsClient] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        self._client = client or ElevenLabsClient(api_key=api_key)
        self._settings = get_settings()

    @property
    def backend_name(self) -> str:
        return "elevenlabs"

    @property
    def default_voice_settings(self) -> Dict[str, Any]:
        return self.DEFAULT_VOICE_SETTINGS.copy()

    def supports_ssml(self) -> bool:
        return True

    def text_to_speech(
        self,
        text: str,
        voice_id: str,
        **kwargs: Any,
    ) -> bytes:
        """Convert text to speech using ElevenLabs.

        Args:
            text: Text to convert.
            voice_id: ElevenLabs voice ID.
            **kwargs: Optional overrides:
                - model_id: ElevenLabs model (default from settings.TTS_VOICE_MODEL)
                - voice_settings: Dict of stability, speed, etc.

        Returns:
            Audio data as MP3 bytes.
        """
        model_id = kwargs.get("model_id") or self._settings.TTS_VOICE_MODEL
        voice_settings = kwargs.get("voice_settings") or self.DEFAULT_VOICE_SETTINGS.copy()

        return self._client.text_to_speech(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            voice_settings=voice_settings,
        )

    @property
    def client(self) -> ElevenLabsClient:
        """Expose the underlying client for ElevenLabs-specific operations."""
        return self._client
