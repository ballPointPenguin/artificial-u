"""
xAI (Grok) TTS client.

Wraps the xAI text-to-speech REST endpoint (POST {base_url}/tts), which returns
raw audio bytes (mp3 by default). Uses httpx directly rather than an SDK.
"""

import logging
import os
import sys
import time
from typing import Any, Dict, Optional

import httpx

from artificial_u.config import get_settings


class XAITTSClient:
    """Low-level client for the xAI Grok text-to-speech API."""

    # Default built-in voice (one of: ara, eve, leo, rex, sal)
    DEFAULT_VOICE = "eve"
    DEFAULT_LANGUAGE = "en"
    DEFAULT_OUTPUT_FORMAT: Dict[str, Any] = {
        "codec": "mp3",
        "sample_rate": 24000,
        "bit_rate": 128000,
    }

    MAX_RETRIES = 3
    RETRY_WAIT = 2

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the xAI TTS client.

        Args:
            api_key: xAI API key. Falls back to XAI_API_KEY env/settings.
            base_url: Override the xAI API base URL.
            logger: Optional logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        settings = get_settings()

        in_test_env = os.environ.get("TESTING") == "true" or "pytest" in sys.modules

        self.api_key = api_key or os.environ.get("XAI_API_KEY") or settings.XAI_API_KEY
        if not self.api_key:
            if in_test_env:
                self.api_key = "test_xai_key"
                self.logger.info("Using test API key in test environment")
            else:
                raise ValueError("xAI API key is required for TTS")

        self.base_url = (base_url or settings.XAI_TTS_BASE_URL).rstrip("/")

    def text_to_speech(
        self,
        text: str,
        voice_id: str = DEFAULT_VOICE,
        language: Optional[str] = None,
        output_format: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Convert text to speech via the xAI TTS endpoint.

        Args:
            text: Text to convert.
            voice_id: Built-in xAI voice name (ara, eve, leo, rex, sal).
            language: BCP-47 language code (default: "en").
            output_format: Codec/sample-rate/bit-rate dict. Defaults to mp3.

        Returns:
            Audio data as bytes (mp3 by default).
        """
        effective_voice_id = voice_id or self.DEFAULT_VOICE
        body: Dict[str, Any] = {
            "text": text,
            "voice_id": effective_voice_id,
            "language": language or self.DEFAULT_LANGUAGE,
            "output_format": output_format or dict(self.DEFAULT_OUTPUT_FORMAT),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/tts"

        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.debug(
                    "xAI TTS attempt %d: voice_id=%s, text_len=%d",
                    attempt + 1,
                    effective_voice_id,
                    len(text),
                )
                with httpx.Client(timeout=120) as http:
                    response = http.post(url, json=body, headers=headers)
                    response.raise_for_status()
                    audio_data = response.content

                if len(audio_data) < 1000 and len(text) > 100:
                    self.logger.warning(
                        "Unexpectedly small audio from xAI: %d bytes for %d chars",
                        len(audio_data),
                        len(text),
                    )
                return audio_data

            except httpx.HTTPStatusError as e:
                # Error responses are JSON even though success is raw bytes.
                self.logger.error(
                    "xAI TTS HTTP error (attempt %d): %s - %s",
                    attempt + 1,
                    e,
                    e.response.text if e.response is not None else "",
                )
                if attempt < self.MAX_RETRIES - 1:
                    wait = self.RETRY_WAIT * (attempt + 1)
                    self.logger.info("Waiting %ds before retry...", wait)
                    time.sleep(wait)
                    continue
                raise
            except Exception as e:
                self.logger.error("xAI TTS error (attempt %d): %s", attempt + 1, e)
                if attempt < self.MAX_RETRIES - 1:
                    wait = self.RETRY_WAIT * (attempt + 1)
                    self.logger.info("Waiting %ds before retry...", wait)
                    time.sleep(wait)
                    continue
                raise

        # Should not reach here, but satisfy type checker
        raise RuntimeError("xAI TTS failed after all retries")
