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
            workspace_id=getattr(settings, "ALIBABA_WORKSPACE_ID", None),
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
            voice_id: Qwen system voice id (e.g. Brian_v3.1, Emily_v3.1).
            **kwargs: Optional overrides:
                - model: qwen-audio TTS model id (defaults to settings.TTS_QWEN_MODEL).

        Returns:
            Audio data as bytes.
        """
        return self._client.text_to_speech(
            text=text,
            voice_id=voice_id or self.DEFAULT_VOICE,
            model=kwargs.get("model"),
        )
