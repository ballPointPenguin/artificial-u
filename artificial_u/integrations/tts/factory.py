"""
Factory for creating TTS backend instances.
"""

import logging
from typing import Optional

from artificial_u.config import get_settings
from artificial_u.integrations.tts.base import TTSBackend


def create_tts_backend(
    backend_name: Optional[str] = None,
    api_key: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> TTSBackend:
    """Create a TTS backend instance.

    Args:
        backend_name: Backend to use ("elevenlabs", "mistral", "xai").
            Defaults to settings.tts_backend.
        api_key: Optional API key override.
        logger: Optional logger.

    Returns:
        A TTSBackend implementation.

    Raises:
        ValueError: If the backend name is not recognized.
    """
    settings = get_settings()
    backend_name = backend_name or settings.tts_backend

    if backend_name == "elevenlabs":
        from artificial_u.integrations.tts.elevenlabs_backend import ElevenLabsTTSBackend

        return ElevenLabsTTSBackend(
            api_key=api_key or settings.ELEVENLABS_API_KEY,
            logger=logger,
        )
    elif backend_name == "mistral":
        from artificial_u.integrations.tts.mistral_backend import MistralTTSBackend

        return MistralTTSBackend(
            api_key=api_key or settings.MISTRAL_API_KEY,
            logger=logger,
        )
    elif backend_name == "xai":
        from artificial_u.integrations.tts.xai_backend import XAITTSBackend

        return XAITTSBackend(
            api_key=api_key or settings.XAI_API_KEY,
            logger=logger,
        )
    else:
        raise ValueError(
            f"Unknown TTS backend: '{backend_name}'. "
            "Supported backends: 'elevenlabs', 'mistral', 'xai'"
        )
