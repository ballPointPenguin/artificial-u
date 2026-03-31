"""
Mistral TTS (Voxtral) client using the official mistralai SDK.

Wraps the SDK's audio.speech endpoint for text-to-speech generation.
"""

import base64
import logging
import time
from typing import Any, Dict, List, Optional

from mistralai import Mistral


class MistralTTSClient:
    """Client for Mistral TTS using the official SDK."""

    DEFAULT_MODEL = "voxtral-mini-tts-2603"
    DEFAULT_FORMAT = "mp3"
    MAX_RETRIES = 3
    RETRY_WAIT = 2

    # Preset voices available in Voxtral TTS
    PRESET_VOICES: List[str] = [
        "alloy",
        "ash",
        "breeze",
        "cove",
        "echo",
        "ember",
        "fable",
        "haze",
        "lark",
        "maple",
        "nova",
        "onyx",
        "orbit",
        "reed",
        "sage",
        "shimmer",
        "vale",
        "vortex",
        "whisper",
        "zen",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        if not api_key:
            raise ValueError("Mistral API key is required for TTS")

        self.logger = logger or logging.getLogger(__name__)
        self.api_key = api_key
        self._client = Mistral(api_key=api_key)

    def text_to_speech(
        self,
        text: str,
        voice_id: str = "alloy",
        model: Optional[str] = None,
        response_format: Optional[str] = None,
    ) -> bytes:
        """Convert text to speech via Mistral SDK.

        Args:
            text: Text to convert.
            voice_id: Voice identifier - a preset name (e.g., "alloy") or
                a saved custom voice ID from audio.voices.create().
            model: Model name (default: voxtral-mini-tts-2603).
            response_format: Audio format (default: mp3).

        Returns:
            Audio data as bytes.
        """
        model = model or self.DEFAULT_MODEL
        response_format = response_format or self.DEFAULT_FORMAT

        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.debug(
                    "Mistral TTS attempt %d: voice_id=%s, text_len=%d",
                    attempt + 1,
                    voice_id,
                    len(text),
                )
                response = self._client.audio.speech.complete(
                    model=model,
                    input=text,
                    voice_id=voice_id,
                    response_format=response_format,
                )

                # SDK returns base64-encoded audio in response.audio_data
                audio_data = base64.b64decode(response.audio_data)

                if len(audio_data) < 1000 and len(text) > 100:
                    self.logger.warning(
                        "Unexpectedly small audio from Mistral: %d bytes for %d chars",
                        len(audio_data),
                        len(text),
                    )
                return audio_data

            except Exception as e:
                self.logger.error("Mistral TTS error (attempt %d): %s", attempt + 1, e)
                if attempt < self.MAX_RETRIES - 1:
                    wait = self.RETRY_WAIT * (attempt + 1)
                    self.logger.info("Waiting %ds before retry...", wait)
                    time.sleep(wait)
                    continue
                raise

        # Should not reach here, but satisfy type checker
        raise RuntimeError("Mistral TTS failed after all retries")

    def close(self) -> None:
        """Close the SDK client."""
        # The mistralai SDK client doesn't require explicit cleanup,
        # but we keep this method for interface consistency.
        pass
