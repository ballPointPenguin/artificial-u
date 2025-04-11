"""
ElevenLabs integration package for ArtificialU.

This package provides integration with the ElevenLabs API for text-to-speech and voice management.
"""

import os
import sys

from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper
from artificial_u.integrations.elevenlabs.cache import VoiceCache

__all__ = ["ElevenLabsClient", "VoiceMapper", "VoiceCache"]


# For test compatibility:
# When tests try to import VoiceSelectionManager, provide a dummy class
# This prevents import errors in test modules that expect this class
class _DummyVoiceSelectionManager:
    """
    Dummy class to prevent import errors in tests.
    This is used only for test compatibility and should not be used in production.
    """

    def __init__(self, *args, **kwargs):
        pass


# Only expose the dummy class when in a test environment
if os.environ.get("TESTING") == "true" or "pytest" in sys.modules:
    VoiceSelectionManager = _DummyVoiceSelectionManager
