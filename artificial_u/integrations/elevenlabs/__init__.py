"""
ElevenLabs integration package for ArtificialU.

This package provides integration with the ElevenLabs API for text-to-speech and voice management.
"""

from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper

__all__ = ["ElevenLabsClient", "VoiceMapper"]
