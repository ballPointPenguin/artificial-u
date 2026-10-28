"""
Qwen (Alibaba) voice manager.

Alibaba Model Studio exposes no voice-list API for qwen-audio-3.1-tts-flash, so
the system-voice catalog is maintained here as a static list, taken from
https://www.alibabacloud.com/help/en/model-studio/qwen-audio-tts-voice-list

Only voices that work in the Singapore region are listed; each was verified
against the live API. The docs also list ~45 Mandarin-only and extra voices
(e.g. ``yuxiaoyun_v3.1``, ``longanyang_v3.1``) that are China (Beijing) only and
fail in Singapore ("Engine error [411]"). Child voices are intentionally omitted.
"""

import logging
from typing import Any, Dict, List, Optional

from artificial_u.config.defaults import DEFAULT_QWEN_TTS_MODEL

DEFAULT_VOICE_ID = "Brian_v3.1"

QWEN_VOICES: List[Dict[str, Any]] = [
    {
        "id": "longanhuan_v3.1",
        "name": "Long An Huan",
        "gender": "female",
        "description": "Multilingual with Chinese dialects",
        "languages": ["zh", "en", "ja", "ko", "fr", "de", "pt", "it", "vi", "id"],
        "accent": None,
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "longanlingxin_v3.1",
        "name": "Long An Lingxin",
        "gender": "female",
        "description": "Multilingual with Chinese dialects",
        "languages": ["zh", "en", "ja", "ko", "fr", "de", "pt", "it", "vi", "id"],
        "accent": None,
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "longanfengyue_v3.1",
        "name": "Long An Fengyue",
        "gender": "female",
        "description": "Multilingual with Chinese dialects",
        "languages": ["zh", "en", "ja", "ko", "fr", "de", "pt", "it", "vi", "id"],
        "accent": None,
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "xunanchuan_v3.1",
        "name": "Xu Nanchuan",
        "gender": "male",
        "description": "Multilingual with Chinese dialects",
        "languages": ["zh", "en", "ja", "ko", "fr", "de", "pt", "it", "vi", "id"],
        "accent": None,
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Emily_v3.1",
        "name": "Emily",
        "gender": "female",
        "description": "British English",
        "languages": ["en"],
        "accent": "British",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Luna_v3.1",
        "name": "Luna",
        "gender": "female",
        "description": "British English",
        "languages": ["en"],
        "accent": "British",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Eric_v3.1",
        "name": "Eric",
        "gender": "male",
        "description": "British English",
        "languages": ["en"],
        "accent": "British",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Luca_v3.1",
        "name": "Luca",
        "gender": "male",
        "description": "British English",
        "languages": ["en"],
        "accent": "British",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Abby_v3.1",
        "name": "Abby",
        "gender": "female",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Annie_v3.1",
        "name": "Annie",
        "gender": "female",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Ava_v3.1",
        "name": "Ava",
        "gender": "female",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Beth_v3.1",
        "name": "Beth",
        "gender": "female",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Betty_v3.1",
        "name": "Betty",
        "gender": "female",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Cally_v3.1",
        "name": "Cally",
        "gender": "female",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Cindy_v3.1",
        "name": "Cindy",
        "gender": "female",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Donna_v3.1",
        "name": "Donna",
        "gender": "female",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Andy_v3.1",
        "name": "Andy",
        "gender": "male",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "Brian_v3.1",
        "name": "Brian",
        "gender": "male",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
    {
        "id": "David_v3.1",
        "name": "David",
        "gender": "male",
        "description": "American English",
        "languages": ["en"],
        "accent": "American",
        "model": DEFAULT_QWEN_TTS_MODEL,
    },
]


class QwenVoiceManager:
    """Reads the static Qwen voice catalog."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def list_voices(self) -> List[Dict[str, Any]]:
        """List available Qwen voices.

        Returns:
            List of voice dicts: id, name, gender, description, languages, accent, model.
        """
        return [dict(voice) for voice in QWEN_VOICES]

    def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Return metadata for a single voice id, or None if not found."""
        for voice in QWEN_VOICES:
            if voice["id"] == voice_id:
                return dict(voice)
        return None
