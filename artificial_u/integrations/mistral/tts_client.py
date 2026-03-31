"""
Mistral TTS (Voxtral) API client.

Low-level client for the Mistral text-to-speech endpoint.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import httpx


class MistralTTSClient:
    """Low-level client for the Mistral TTS API."""

    BASE_URL = "https://api.mistral.ai/v1"
    DEFAULT_MODEL = "mistral-tts-latest"
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
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "audio/mpeg",
            },
            timeout=120.0,
        )

    def text_to_speech(
        self,
        text: str,
        voice: str = "alloy",
        model: Optional[str] = None,
        response_format: Optional[str] = None,
    ) -> bytes:
        """Convert text to speech via Mistral API.

        Args:
            text: Text to convert.
            voice: Preset voice name (e.g., "alloy", "nova").
            model: Model name (default: mistral-tts-latest).
            response_format: Audio format (default: mp3).

        Returns:
            Audio data as bytes.
        """
        model = model or self.DEFAULT_MODEL
        response_format = response_format or self.DEFAULT_FORMAT

        payload: Dict[str, Any] = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": response_format,
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.debug(
                    "Mistral TTS attempt %d: voice=%s, text_len=%d",
                    attempt + 1,
                    voice,
                    len(text),
                )
                response = self._client.post("/audio/speech", json=payload)
                response.raise_for_status()

                audio_data = response.content
                if len(audio_data) < 1000 and len(text) > 100:
                    self.logger.warning(
                        "Unexpectedly small audio from Mistral: %d bytes for %d chars",
                        len(audio_data),
                        len(text),
                    )
                return audio_data

            except httpx.HTTPStatusError as e:
                self.logger.error("Mistral TTS HTTP error: %s", e)
                if e.response.status_code == 429 and attempt < self.MAX_RETRIES - 1:
                    wait = self.RETRY_WAIT * (attempt + 1)
                    self.logger.info("Rate limited, waiting %ds before retry...", wait)
                    time.sleep(wait)
                    continue
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_WAIT)
                    continue
                raise
            except Exception as e:
                self.logger.error("Mistral TTS error: %s", e)
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_WAIT)
                    continue
                raise

        # Should not reach here, but satisfy type checker
        raise RuntimeError("Mistral TTS failed after all retries")

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
