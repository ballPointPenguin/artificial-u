"""
xAI (Grok) voice manager.

Lists the available xAI voices from the live API (GET {base}/tts/voices).
xAI exposes a small, evolving catalog (a handful of multilingual voices plus
language-specific voices). We always read it fresh so new voices appear
automatically without code changes. Non-enterprise accounts cannot create
custom voices, so this is read-only.
"""

import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

import httpx

from artificial_u.config import get_settings


class XAIVoiceManager:
    """Reads the xAI voice catalog from the live API."""

    MAX_RETRIES = 3
    RETRY_WAIT = 2

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.logger = logger or logging.getLogger(__name__)
        settings = get_settings()

        in_test_env = os.environ.get("TESTING") == "true" or "pytest" in sys.modules

        self.api_key = api_key or os.environ.get("XAI_API_KEY") or settings.XAI_API_KEY
        if not self.api_key:
            if in_test_env:
                self.api_key = "test_xai_key"
            else:
                raise ValueError("xAI API key is required for voice management")

        self.base_url = (base_url or settings.XAI_TTS_BASE_URL).rstrip("/")

    def list_voices(self) -> List[Dict[str, Any]]:
        """List available xAI voices.

        Returns:
            List of voice dicts normalized to: id, name, language, gender.
        """
        url = f"{self.base_url}/tts/voices"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        last_exc: Optional[Exception] = None
        for attempt in range(self.MAX_RETRIES):
            try:
                with httpx.Client(timeout=30) as http:
                    response = http.get(url, headers=headers)
                    response.raise_for_status()
                    payload = response.json()
                break
            except Exception as e:
                last_exc = e
                self.logger.error("xAI list voices error (attempt %d): %s", attempt + 1, e)
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_WAIT * (attempt + 1))
                    continue
                raise
        else:  # pragma: no cover - defensive
            raise RuntimeError(f"xAI list voices failed: {last_exc}")

        raw_voices = payload.get("voices", payload if isinstance(payload, list) else [])
        voices = [self._voice_to_dict(v) for v in raw_voices]
        self.logger.info("Listed %d xAI voices", len(voices))
        return voices

    def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Return metadata for a single voice id, or None if not found."""
        for voice in self.list_voices():
            if voice.get("id") == voice_id:
                return voice
        return None

    @staticmethod
    def _voice_to_dict(voice: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize an xAI voice record (voice_id -> id)."""
        voice_id = voice.get("voice_id") or voice.get("id")
        return {
            "id": voice_id,
            "name": voice.get("name") or voice_id,
            "language": voice.get("language"),
            "gender": voice.get("gender"),
        }
