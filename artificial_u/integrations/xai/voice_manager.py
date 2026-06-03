"""
xAI (Grok) voice catalog.

Non-enterprise xAI accounts cannot clone or create voices and there is no
public list-voices endpoint, so the catalog is a small, static, curated set of
the built-in voices. This module is the single source of truth shared by the
seed script (and any future catalog endpoint).
"""

import logging
from typing import Any, Dict, List, Optional

# Built-in xAI voices. Metadata (gender in particular) is curated/best-effort and
# safe to refine; the UI tolerates a null gender. All voices speak English and
# can be used for accented-English output regardless of intended language.
XAI_VOICES: List[Dict[str, Any]] = [
    {"id": "eve", "name": "Eve", "gender": "female", "language": "en"},
    {"id": "ara", "name": "Ara", "gender": "female", "language": "en"},
    {"id": "leo", "name": "Leo", "gender": "male", "language": "en"},
    {"id": "rex", "name": "Rex", "gender": "male", "language": "en"},
    {"id": "sal", "name": "Sal", "gender": "male", "language": "en"},
]


class XAIVoiceManager:
    """Provides the static xAI voice catalog (mirrors the Mistral voice manager API)."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def list_voices(self) -> List[Dict[str, Any]]:
        """Return the static list of built-in xAI voices."""
        return [dict(v) for v in XAI_VOICES]
