"""
Mistral TTS backend adapter.

Wraps MistralTTSClient to conform to the TTSBackend protocol.
"""

import logging
from typing import Any, Dict, Optional

from artificial_u.config import get_settings
from artificial_u.integrations.mistral.tts_client import MistralTTSClient


class MistralTTSBackend:
    """TTS backend implementation for Mistral Voxtral."""

    DEFAULT_VOICE = ""

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[MistralTTSClient] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        settings = get_settings()
        api_key = api_key or getattr(settings, "MISTRAL_API_KEY", None)
        self._client = client or MistralTTSClient(api_key=api_key, logger=self.logger)
        self._settings = settings

    @property
    def backend_name(self) -> str:
        return "mistral"

    @property
    def default_voice_settings(self) -> Dict[str, Any]:
        return {}

    def supports_ssml(self) -> bool:
        return False

    def text_to_speech(
        self,
        text: str,
        voice_id: str,
        **kwargs: Any,
    ) -> bytes:
        """Convert text to speech using Mistral Voxtral.

        Args:
            text: Text to convert.
            voice_id: Mistral voice UUID from the Voices API or a custom
                voice ID from audio.voices.create().
            **kwargs: Optional overrides:
                - model: Mistral model name.
                - response_format: Audio format (mp3, wav, etc.)

        Returns:
            Audio data as bytes.
        """
        effective_voice_id = voice_id or self.DEFAULT_VOICE
        model = kwargs.get("model") or getattr(
            self._settings, "TTS_MISTRAL_MODEL", MistralTTSClient.DEFAULT_MODEL
        )
        response_format = kwargs.get("response_format", "mp3")

        return self._client.text_to_speech(
            text=text,
            voice_id=effective_voice_id,
            model=model,
            response_format=response_format,
        )
