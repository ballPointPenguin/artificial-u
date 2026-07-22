"""
Qwen (Alibaba) voice manager.

Alibaba Model Studio exposes no voice-list API for the qwen-audio-3.0-tts
models, so the preset catalog is maintained here as a static list, taken from
https://www.alibabacloud.com/help/en/model-studio/qwen-audio-tts-voice-list
Every preset voice supports English; most are bilingual Mandarin+English.
Each voice works only with the model it is listed under.
"""

import logging
from typing import Any, Dict, List, Optional

FLASH_MODEL = "qwen-audio-3.0-tts-flash"
PLUS_MODEL = "qwen-audio-3.0-tts-plus"

QWEN_VOICES: List[Dict[str, Any]] = [
    # qwen-audio-3.0-tts-plus (flagship tier)
    {
        "id": "longanlingxin",
        "name": "Longan Lingxin",
        "gender": "female",
        "description": "Warm and empathetic",
        "languages": ["zh", "en"],
        "model": PLUS_MODEL,
    },
    {
        "id": "longanlufeng",
        "name": "Longan Lufeng",
        "gender": "female",
        "description": "Bright and cheerful",
        "languages": ["zh", "en"],
        "model": PLUS_MODEL,
    },
    # qwen-audio-3.0-tts-flash — native-English voices
    {
        "id": "loongmary",
        "name": "Mary",
        "gender": "female",
        "description": "Warm British accent",
        "languages": ["en"],
        "model": FLASH_MODEL,
    },
    {
        "id": "loongeva_v3.6",
        "name": "Eva",
        "gender": "female",
        "description": "Intelligent and elegant",
        "languages": ["en"],
        "model": FLASH_MODEL,
    },
    {
        "id": "loongjohn",
        "name": "John",
        "gender": "male",
        "description": "Calm and friendly American accent",
        "languages": ["en"],
        "model": FLASH_MODEL,
    },
    # qwen-audio-3.0-tts-flash — bilingual Mandarin+English voices
    {
        "id": "longanfengyue",
        "name": "Longan Fengyue",
        "gender": "female",
        "description": "Natural and friendly",
        "languages": ["zh", "en"],
        "model": FLASH_MODEL,
    },
    {
        "id": "longanyuanfei",
        "name": "Longan Yuanfei",
        "gender": "female",
        "description": "Proud and regal",
        "languages": ["zh", "en"],
        "model": FLASH_MODEL,
    },
    {
        "id": "longanlingxi",
        "name": "Longan Lingxi",
        "gender": "female",
        "description": "Cute and sweet",
        "languages": ["zh", "en"],
        "model": FLASH_MODEL,
    },
    {
        "id": "longanxiaoxin",
        "name": "Longan Xiaoxin",
        "gender": "female",
        "description": "Friendly and lively",
        "languages": ["zh", "en"],
        "model": FLASH_MODEL,
    },
    {
        "id": "longanhuan_v3.6",
        "name": "Longan Huan",
        "gender": "female",
        "description": "Gentle and soothing",
        "languages": ["zh", "en"],
        "model": FLASH_MODEL,
    },
    {
        "id": "longjielidou_v3.6",
        "name": "Longjie Lidou",
        "gender": "male",
        "description": "Innocent boy",
        "languages": ["zh", "en"],
        "model": FLASH_MODEL,
    },
    {
        "id": "longpaopao_v3.6",
        "name": "Long Paopao",
        "gender": "female",
        "description": "Soft and adorable",
        "languages": ["zh", "en"],
        "model": FLASH_MODEL,
    },
    {
        "id": "longhuohuo_v3.6",
        "name": "Long Huohuo",
        "gender": "male",
        "description": "Mischievous boy",
        "languages": ["zh", "en"],
        "model": FLASH_MODEL,
    },
    {
        "id": "longchuanshu_v3.6",
        "name": "Long Chuanshu",
        "gender": "male",
        "description": "Sichuan-dialect storyteller",
        "languages": ["zh", "en"],
        "model": FLASH_MODEL,
    },
]


def model_for_voice(voice_id: str) -> Optional[str]:
    """Return the qwen-audio model a preset voice belongs to, or None if unknown."""
    for voice in QWEN_VOICES:
        if voice["id"] == voice_id:
            return voice["model"]
    return None


class QwenVoiceManager:
    """Reads the static Qwen preset voice catalog."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def list_voices(self) -> List[Dict[str, Any]]:
        """List available Qwen preset voices.

        Returns:
            List of voice dicts: id, name, gender, description, languages, model.
        """
        return [dict(voice) for voice in QWEN_VOICES]

    def get_voice(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """Return metadata for a single voice id, or None if not found."""
        for voice in QWEN_VOICES:
            if voice["id"] == voice_id:
                return dict(voice)
        return None
