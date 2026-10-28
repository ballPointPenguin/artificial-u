"""
Qwen (Alibaba) TTS client.

Calls the qwen-audio-3.1-tts-flash HTTPS audio generation API with a system
voice. The call is non-streaming: it returns JSON with a short-lived (24h)
audio URL, which is then downloaded. The endpoint is workspace- and region-specific, and the
ALIBABA_API_KEY must belong to the same region (e.g. Singapore, ap-southeast-1).
"""

import logging
import os
import sys
import time
from typing import Any, Optional

import httpx

from artificial_u.config import get_settings
from artificial_u.integrations.qwen.voice_manager import DEFAULT_VOICE_ID


class QwenTTSClient:
    """Low-level client for Alibaba Model Studio Qwen audio generation."""

    DEFAULT_VOICE = DEFAULT_VOICE_ID

    OUTPUT_FORMAT = "mp3"
    SAMPLE_RATE = 24000
    CHANNELS = 1

    MAX_RETRIES = 3
    RETRY_WAIT = 2
    REQUEST_TIMEOUT = 180

    def __init__(
        self,
        api_key: Optional[str] = None,
        workspace_id: Optional[str] = None,
        region: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the Qwen TTS client.

        Args:
            api_key: Alibaba Cloud API key. Falls back to ALIBABA_API_KEY env/settings.
            workspace_id: Model Studio workspace ID. Falls back to ALIBABA_WORKSPACE_ID.
            region: Region of the workspace. Falls back to ALIBABA_TTS_REGION.
            logger: Optional logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        settings = get_settings()

        in_test_env = os.environ.get("TESTING") == "true" or "pytest" in sys.modules

        self.api_key = api_key or os.environ.get("ALIBABA_API_KEY") or settings.ALIBABA_API_KEY
        if not self.api_key:
            if in_test_env:
                self.api_key = "test_alibaba_key"
                self.logger.info("Using test API key in test environment")
            else:
                raise ValueError("Alibaba API key is required for Qwen TTS")

        self.workspace_id = (
            workspace_id or os.environ.get("ALIBABA_WORKSPACE_ID") or settings.ALIBABA_WORKSPACE_ID
        )
        if not self.workspace_id:
            if in_test_env:
                self.workspace_id = "test-workspace"
            else:
                raise ValueError("ALIBABA_WORKSPACE_ID is required for Qwen TTS")

        self.region = region or settings.ALIBABA_TTS_REGION
        self.default_model = settings.TTS_QWEN_MODEL

    @property
    def url(self) -> str:
        return (
            f"https://{self.workspace_id}.{self.region}.maas.aliyuncs.com"
            "/api/v1/services/audio/tts/SpeechSynthesizer"
        )

    def text_to_speech(
        self,
        text: str,
        voice_id: str = DEFAULT_VOICE,
        model: Optional[str] = None,
    ) -> bytes:
        """Convert text to speech via the Qwen audio generation API.

        Args:
            text: Text to convert.
            voice_id: Qwen system voice id (e.g. Brian_v3.1, Emily_v3.1).
            model: Model override. Defaults to settings.TTS_QWEN_MODEL.

        Returns:
            Audio data as mp3 bytes.
        """
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "input": {
                "text": text,
                "voice": voice_id or self.DEFAULT_VOICE,
                "format": self.OUTPUT_FORMAT,
                "sample_rate": self.SAMPLE_RATE,
                "channels": self.CHANNELS,
            },
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.debug(
                    "Qwen TTS attempt %d: model=%s, voice=%s, text_len=%d",
                    attempt + 1,
                    payload["model"],
                    payload["input"]["voice"],
                    len(text),
                )
                with httpx.Client(timeout=self.REQUEST_TIMEOUT) as http:
                    resp = http.post(self.url, json=payload, headers=headers)
                    self._raise_for_status(resp)
                    audio_url = (resp.json().get("output") or {}).get("audio", {}).get("url")
                    if not audio_url:
                        raise RuntimeError(f"Qwen TTS response had no audio URL: {resp.text[:300]}")
                    audio_resp = http.get(audio_url)
                    audio_resp.raise_for_status()
                    audio_data = audio_resp.content

                if not audio_data:
                    raise RuntimeError("Qwen TTS returned no audio data")
                if len(audio_data) < 1000 and len(text) > 100:
                    self.logger.warning(
                        "Unexpectedly small audio from Qwen: %d bytes for %d chars",
                        len(audio_data),
                        len(text),
                    )
                return audio_data

            except Exception as e:
                self.logger.error("Qwen TTS error (attempt %d): %s", attempt + 1, e)
                if not self._is_retryable(e) or attempt == self.MAX_RETRIES - 1:
                    raise
                wait = self.RETRY_WAIT * (attempt + 1)
                self.logger.info("Waiting %ds before retry...", wait)
                time.sleep(wait)

        # Should not reach here, but satisfy type checker
        raise RuntimeError("Qwen TTS failed after all retries")

    @staticmethod
    def _raise_for_status(resp: httpx.Response) -> None:
        """Raise with the API's error code/message, which httpx's default hides."""
        if resp.status_code < 400:
            return
        try:
            body = resp.json()
            detail = f"{body.get('code')}: {body.get('message')}"
        except ValueError:
            detail = resp.text[:300]
        raise httpx.HTTPStatusError(
            f"Qwen TTS HTTP {resp.status_code} ({detail})",
            request=resp.request,
            response=resp,
        )

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        """Retry transport errors, throttling, and 5xx; not auth/validation errors."""
        if isinstance(error, httpx.HTTPStatusError):
            status = error.response.status_code
            return status == 429 or status >= 500
        return isinstance(error, (httpx.TransportError, RuntimeError))
