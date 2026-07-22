"""
Qwen (Alibaba) TTS client.

Wraps the dashscope SDK's synchronous SpeechSynthesizer, which drives the
qwen-audio-3.0-tts WebSocket protocol and returns complete audio bytes.
The endpoint is region-locked to the API key (see ALIBABA_TTS_WSS_URL).
"""

import logging
import os
import sys
import time
from typing import Optional

from artificial_u.config import get_settings
from artificial_u.integrations.qwen.voice_manager import model_for_voice


class QwenTTSClient:
    """Low-level client for Alibaba Model Studio Qwen text-to-speech."""

    DEFAULT_VOICE = "loongeva_v3.6"

    MAX_RETRIES = 3
    RETRY_WAIT = 2

    def __init__(
        self,
        api_key: Optional[str] = None,
        wss_url: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the Qwen TTS client.

        Args:
            api_key: Alibaba Cloud API key. Falls back to ALIBABA_API_KEY env/settings.
            wss_url: Override the Model Studio WebSocket endpoint.
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

        self.wss_url = wss_url or settings.ALIBABA_TTS_WSS_URL
        self.default_model = settings.TTS_QWEN_MODEL

    def text_to_speech(
        self,
        text: str,
        voice_id: str = DEFAULT_VOICE,
        model: Optional[str] = None,
    ) -> bytes:
        """Convert text to speech via the Qwen TTS WebSocket API.

        Args:
            text: Text to convert.
            voice_id: Qwen preset voice id (e.g. loongeva_v3.6, loongjohn).
            model: Model override. Defaults to the model the voice belongs to
                (plus-tier voices need qwen-audio-3.0-tts-plus), falling back
                to settings.TTS_QWEN_MODEL.

        Returns:
            Audio data as mp3 bytes.
        """
        # Imported lazily so the module (and test mocks) load without the SDK
        # opening network resources at import time.
        import dashscope
        from dashscope.audio.tts_v2 import AudioFormat, SpeechSynthesizer

        effective_voice_id = voice_id or self.DEFAULT_VOICE
        effective_model = model or model_for_voice(effective_voice_id) or self.default_model

        # The SDK reads the key from module state; there is no per-call param.
        dashscope.api_key = self.api_key

        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.debug(
                    "Qwen TTS attempt %d: model=%s, voice=%s, text_len=%d",
                    attempt + 1,
                    effective_model,
                    effective_voice_id,
                    len(text),
                )
                # SpeechSynthesizer instances are single-use: one per call.
                synthesizer = SpeechSynthesizer(
                    model=effective_model,
                    voice=effective_voice_id,
                    format=AudioFormat.MP3_24000HZ_MONO_256KBPS,
                    url=self.wss_url,
                )
                audio_data = synthesizer.call(text)

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
                if attempt < self.MAX_RETRIES - 1:
                    wait = self.RETRY_WAIT * (attempt + 1)
                    self.logger.info("Waiting %ds before retry...", wait)
                    time.sleep(wait)
                    continue
                raise

        # Should not reach here, but satisfy type checker
        raise RuntimeError("Qwen TTS failed after all retries")
