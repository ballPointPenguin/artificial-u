"""
xAI (Grok) TTS backend adapter.

Wraps XAITTSClient to conform to the TTSBackend protocol.
"""

import logging
from typing import Any, Dict, Optional

from artificial_u.config import get_settings
from artificial_u.integrations.xai.tts_client import XAITTSClient


class XAITTSBackend:
    """TTS backend implementation for xAI Grok."""

    DEFAULT_VOICE = "eve"

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[XAITTSClient] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        settings = get_settings()
        api_key = api_key or getattr(settings, "XAI_API_KEY", None)
        self._client = client or XAITTSClient(
            api_key=api_key,
            base_url=getattr(settings, "XAI_TTS_BASE_URL", None),
            logger=self.logger,
        )
        self._settings = settings

    @property
    def backend_name(self) -> str:
        return "xai"

    @property
    def default_voice_settings(self) -> Dict[str, Any]:
        return {}

    def text_to_speech(
        self,
        text: str,
        voice_id: str,
        **kwargs: Any,
    ) -> bytes:
        """Convert text to speech using xAI Grok.

        Args:
            text: Text to convert.
            voice_id: Built-in xAI voice name (ara, eve, leo, rex, sal).
            **kwargs: Optional overrides:
                - language: BCP-47 language code (defaults to settings.XAI_TTS_LANGUAGE).
                - output_format: Codec/sample-rate/bit-rate dict.

        Returns:
            Audio data as bytes.
        """
        effective_voice_id = voice_id or self.DEFAULT_VOICE
        language = kwargs.get("language") or getattr(self._settings, "XAI_TTS_LANGUAGE", "en")
        output_format = kwargs.get("output_format")

        return self._client.text_to_speech(
            text=text,
            voice_id=effective_voice_id,
            language=language,
            output_format=output_format,
        )
