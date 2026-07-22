"""
Qwen (Alibaba) TTS backend adapter.

Wraps QwenTTSClient to conform to the TTSBackend protocol.
"""

import logging
from typing import Any, Dict, Optional

from artificial_u.config import get_settings
from artificial_u.integrations.qwen.tts_client import QwenTTSClient


class QwenTTSBackend:
    """TTS backend implementation for Alibaba Qwen."""

    DEFAULT_VOICE = QwenTTSClient.DEFAULT_VOICE

    def __init__(
        self,
        api_key: Optional[str] = None,
        client: Optional[QwenTTSClient] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        settings = get_settings()
        api_key = api_key or getattr(settings, "ALIBABA_API_KEY", None)
        self._client = client or QwenTTSClient(
            api_key=api_key,
            wss_url=getattr(settings, "ALIBABA_TTS_WSS_URL", None),
            logger=self.logger,
        )

    @property
    def backend_name(self) -> str:
        return "qwen"

    @property
    def default_voice_settings(self) -> Dict[str, Any]:
        return {}

    def text_to_speech(
        self,
        text: str,
        voice_id: str,
        **kwargs: Any,
    ) -> bytes:
        """Convert text to speech using Alibaba Qwen.

        Args:
            text: Text to convert.
            voice_id: Qwen preset voice id (e.g. loongeva_v3.6, loongjohn).
            **kwargs: Optional overrides:
                - model: qwen-audio TTS model id (defaults to the voice's model).

        Returns:
            Audio data as bytes.
        """
        effective_voice_id = voice_id or self.DEFAULT_VOICE

        return self._client.text_to_speech(
            text=text,
            voice_id=effective_voice_id,
            model=kwargs.get("model"),
        )
