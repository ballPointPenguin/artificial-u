"""
ElevenLabs integration package for ArtificialU.

This package provides integration with the ElevenLabs API for text-to-speech and voice management.
"""

import os
import sys
import random
from typing import Dict, List, Optional, Any

from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper
from artificial_u.integrations.elevenlabs.cache import VoiceCache

__all__ = ["ElevenLabsClient", "VoiceMapper", "VoiceCache"]

# For test compatibility, expose required functions and classes
# This prevents import errors in test modules that expect the old structure


class VoiceSelectionManager:
    """
    Compatibility class to prevent import errors in tests.
    This ensures existing tests continue to work with the refactored architecture.
    """

    def __init__(self, api_key=None):
        """Initialize with the new refactored components"""
        self.client = ElevenLabsClient(api_key=api_key)
        self.voice_mapper = VoiceMapper()
        self.voice_mapping_db = {}  # For tracking selected voices

    def get_available_voices(self, page_size=100, refresh=False):
        """Get available voices from the ElevenLabs API"""
        voices, _ = self.client.get_shared_voices(page_size=page_size)
        return voices

    def filter_voices(self, **criteria):
        """Filter voices by various criteria"""
        voices, _ = self.client.get_shared_voices(**criteria)
        return voices

    def sample_voices_by_criteria(self, count=3, **criteria):
        """Sample a random subset of voices matching criteria"""
        voices = self.filter_voices(**criteria)
        if not voices:
            return []
        return random.sample(voices, min(count, len(voices)))

    def get_voice_for_professor(self, professor, additional_context=None):
        """Get the most appropriate voice for a professor"""
        attrs = self.voice_mapper.extract_profile_attributes(
            professor, additional_context
        )

        # Try with all criteria
        voices = self.filter_voices(
            gender=attrs.get("gender"), accent=attrs.get("accent"), age=attrs.get("age")
        )

        if not voices:
            # Fallback to just gender
            voices = self.filter_voices(gender=attrs.get("gender"))

        if voices:
            # Rank voices by criteria match
            ranked_voices = self.voice_mapper.rank_voices(voices, attrs)
            # Select a voice using the configured strategy
            voice = self.voice_mapper.select_voice(ranked_voices)
            if voice:
                # Save mapping for consistency
                if hasattr(professor, "id") and professor.id:
                    self.voice_mapping_db[professor.id] = voice["voice_id"]
                return voice

        # Last resort fallback
        all_voices, _ = self.client.get_shared_voices()
        if all_voices:
            voice = random.choice(all_voices)
            if hasattr(professor, "id") and professor.id:
                self.voice_mapping_db[professor.id] = voice["voice_id"]
            return voice

        # Ultimate fallback - minimal data
        return {
            "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel voice as fallback
            "name": "Rachel (Default)",
            "gender": "female",
            "accent": "american",
            "age": "middle_aged",
            "category": "premade",
        }

    def _extract_gender_from_professor(self, professor):
        """Extract gender information from a professor profile"""
        return self.voice_mapper.extract_gender(professor)

    def _extract_accent_from_professor(self, professor):
        """Extract accent information from a professor profile"""
        return self.voice_mapper.extract_accent(professor)

    def _extract_age_from_professor(self, professor):
        """Extract age information from a professor profile"""
        return self.voice_mapper.extract_age(professor)

    def list_available_voice_filters(self):
        """List all available voice filters and their values"""
        return {
            "gender": ["male", "female", "neutral"],
            "accent": VoiceMapper.SUPPORTED_ACCENTS,
            "age": ["child", "young", "middle_aged", "old"],
            "category": ["professional", "premade", "cloned", "generated"],
        }


# Helper functions for backwards compatibility
def get_voice_for_professor(professor, api_key=None):
    """Get a voice for a professor profile - compatibility function"""
    manager = VoiceSelectionManager(api_key=api_key)
    return manager.get_voice_for_professor(professor)


def sample_voices(count=3, **criteria):
    """Sample voices with given criteria - compatibility function"""
    manager = VoiceSelectionManager()
    return manager.sample_voices_by_criteria(count=count, **criteria)


def get_voice_filters():
    """Get available voice filters - compatibility function"""
    manager = VoiceSelectionManager()
    return manager.list_available_voice_filters()
