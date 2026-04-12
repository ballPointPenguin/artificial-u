"""
TTS backend abstraction layer.

Provides a protocol for TTS backends and a factory for creating them.
"""

from artificial_u.integrations.tts.base import TTSBackend
from artificial_u.integrations.tts.factory import create_tts_backend

__all__ = ["TTSBackend", "create_tts_backend"]
