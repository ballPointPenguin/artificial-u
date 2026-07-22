"""
Qwen (Alibaba) voice manager.

Alibaba Model Studio exposes no voice-list API for the qwen-audio-3.0-tts
models, so the preset catalog is maintained here as a static list, taken from
https://www.alibabacloud.com/help/en/model-studio/qwen-audio-tts-voice-list

The catalog has two kinds of entries:
  * System voices — first-class voices whose ``voice`` parameter is a plain id
    (e.g. ``longanlingxin``) tied to one model (plus or flash).
  * Base voices — pre-generated cloned voices whose ``voice`` parameter is the
    full model-prefixed name (e.g. ``qwen-audio-3.0-tts-plus-longyinghaikai``).
    Alibaba publishes 1000+ of these; only a representative subset is listed
    here. The same suffix works in both plus and flash; we standardize on plus.

Child voices (age < 18) are intentionally omitted (Longjie Lidou, Long Paopao,
Long Huohuo, and the young base voices). Base voices are Chinese (Mandarin)
only, which is useful for Chinese-language content.
"""

import logging
from typing import Any, Dict, List, Optional

FLASH_MODEL = "qwen-audio-3.0-tts-flash"
PLUS_MODEL = "qwen-audio-3.0-tts-plus"

QWEN_VOICES: List[Dict[str, Any]] = [
    # ---- System voices: qwen-audio-3.0-tts-plus (flagship) ----
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
        "gender": "male",
        "description": "Bright and cheerful",
        "languages": ["zh", "en"],
        "model": PLUS_MODEL,
    },
    # ---- System voices: qwen-audio-3.0-tts-flash ----
    # Native-English voices
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
    # Bilingual Mandarin+English voices
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
        "id": "longchuanshu_v3.6",
        "name": "Long Chuanshu",
        "gender": "male",
        "description": "Sichuan-dialect storyteller",
        "languages": ["zh", "en"],
        "model": FLASH_MODEL,
    },
    # ---- Base (cloned) voices: Mandarin only, plus-tier ----
    {
        "id": "qwen-audio-3.0-tts-plus-longyinghaikai",
        "name": "Long Ying Hai Kai",
        "gender": "female",
        "description": "Positive and upbeat",
        "languages": ["zh"],
        "model": PLUS_MODEL,
    },
    {
        "id": "qwen-audio-3.0-tts-plus-longyinghaixuan",
        "name": "Long Ying Hai Xuan",
        "gender": "female",
        "description": "Capable and composed",
        "languages": ["zh"],
        "model": PLUS_MODEL,
    },
    {
        "id": "qwen-audio-3.0-tts-plus-longyingjingdong",
        "name": "Long Ying Jing Dong",
        "gender": "female",
        "description": "Composed and professional",
        "languages": ["zh"],
        "model": PLUS_MODEL,
    },
    {
        "id": "qwen-audio-3.0-tts-plus-longyinghaizhe",
        "name": "Long Ying Hai Zhe",
        "gender": "male",
        "description": "Firm and persuasive",
        "languages": ["zh"],
        "model": PLUS_MODEL,
    },
    {
        "id": "qwen-audio-3.0-tts-plus-longyingjinhao",
        "name": "Long Ying Jin Hao",
        "gender": "female",
        "description": "Approachable and reliable",
        "languages": ["zh"],
        "model": PLUS_MODEL,
    },
    {
        "id": "qwen-audio-3.0-tts-plus-longluanxuanling",
        "name": "Long Luan Xuan Ling",
        "gender": "female",
        "description": "Gentle older-sister voice",
        "languages": ["zh"],
        "model": PLUS_MODEL,
    },
    {
        "id": "qwen-audio-3.0-tts-plus-longhexiaoxuan",
        "name": "Long He Xiao Xuan",
        "gender": "male",
        "description": "Refined and scholarly",
        "languages": ["zh"],
        "model": PLUS_MODEL,
    },
    {
        "id": "qwen-audio-3.0-tts-plus-longsonglinwang",
        "name": "Long Song Lin Wang",
        "gender": "male",
        "description": "Warm and magnetic",
        "languages": ["zh"],
        "model": PLUS_MODEL,
    },
    {
        "id": "qwen-audio-3.0-tts-plus-longhuiluling",
        "name": "Long Hui Lu Ling",
        "gender": "female",
        "description": "Gentle and caring",
        "languages": ["zh"],
        "model": PLUS_MODEL,
    },
    {
        "id": "qwen-audio-3.0-tts-plus-longshuojizhu",
        "name": "Long Shuo Ji Zhu",
        "gender": "male",
        "description": "Standard broadcasting voice",
        "languages": ["zh"],
        "model": PLUS_MODEL,
    },
    {
        "id": "qwen-audio-3.0-tts-plus-longyufengmo",
        "name": "Long Yu Feng Mo",
        "gender": "female",
        "description": "Gentle and resilient",
        "languages": ["zh"],
        "model": PLUS_MODEL,
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
