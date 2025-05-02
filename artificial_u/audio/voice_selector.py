"""
Voice selection for ArtificialU.

This module provides functionality to match professor profiles to appropriate ElevenLabs voices
based on characteristics like gender, accent, and age.
"""

import logging
import random
from typing import Any, Dict, List, Optional

from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.models.core import Professor


class VoiceSelector:
    """
    Handles the selection of appropriate ElevenLabs voices for professors.
    """

    # Supported accents in ElevenLabs (for English-capable voices)
    SUPPORTED_ACCENTS = [
        "american",
        "australian",
        "british",
        "canadian",
        "indian",
        "irish",
        "scottish",
        "south_african",
        "new_zealand",
    ]

    # Common accent mappings
    ACCENT_MAPPING = {
        "us": "american",
        "usa": "american",
        "united states": "american",
        "american": "american",
        "uk": "british",
        "united kingdom": "british",
        "england": "british",
        "british": "british",
        "australia": "australian",
        "canada": "canadian",
        "india": "indian",
        "ireland": "irish",
        "scotland": "scottish",
        "south africa": "south_african",
        "new zealand": "new_zealand",
    }

    def __init__(self, client: Optional[ElevenLabsClient] = None, logger=None):
        """
        Initialize the voice selector.

        Args:
            client: ElevenLabs client instance
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.client = client or ElevenLabsClient()

    def extract_profile_attributes(self, professor: Professor) -> Dict[str, Any]:
        """
        Extract relevant attributes from a professor profile for voice matching.

        Args:
            professor: Professor profile to extract attributes from

        Returns:
            Dictionary of attributes for voice matching
        """
        attributes = {
            "gender": self._map_gender(professor),
            "accent": self._map_accent(professor),
            "age": self._map_age(professor),
            "language": "en",  # Default to English
        }

        return attributes

    def _map_gender(self, professor: Professor) -> str:
        """Map professor gender to ElevenLabs gender category."""
        if hasattr(professor, "gender") and professor.gender:
            gender = professor.gender.lower()
            if "female" in gender or "woman" in gender or gender == "f":
                return "female"
            elif "male" in gender or "man" in gender or gender == "m":
                return "male"

        # Default or non-binary
        return "neutral"

    def _map_accent(self, professor: Professor) -> Optional[str]:
        """Map professor accent to ElevenLabs accent category."""
        if hasattr(professor, "accent") and professor.accent:
            # Use accent directly from professor model
            accent = professor.accent.lower()

            # Check if we need to map the accent to an ElevenLabs format
            normalized_accent = self.ACCENT_MAPPING.get(accent, accent)

            # Ensure accent is in supported list
            if normalized_accent in self.SUPPORTED_ACCENTS:
                return normalized_accent

        return None  # Default to no accent preference

    def _map_age(self, professor: Professor) -> str:
        """Map professor age to ElevenLabs age category."""
        if hasattr(professor, "age") and professor.age:
            try:
                age = int(professor.age)
                if age < 30:
                    return "young"
                elif age > 60:
                    return "old"
                else:
                    return "middle_aged"
            except (ValueError, TypeError):
                pass

        # Default age
        return "middle_aged"

    def select_voice(self, professor: Professor) -> Dict[str, Any]:
        """
        Select an appropriate voice for a professor.

        Args:
            professor: Professor profile

        Returns:
            Selected voice data containing el_voice_id and name
        """
        # Extract attributes for matching
        attributes = self.extract_profile_attributes(professor)

        # Get voices matching these attributes
        voices = self._get_matching_voices(attributes)

        # If no voices found, try with fewer constraints
        if not voices:
            # Try with just gender
            if attributes.get("gender"):
                voices = self._get_matching_voices(
                    {"gender": attributes["gender"], "language": "en"}
                )

            # If still no voices, get any English voices
            if not voices:
                voices = self._get_matching_voices({"language": "en"})

        # Select a voice randomly from the results
        if voices:
            # Sort by popularity/quality if available
            if any("cloned_by_count" in voice for voice in voices):
                voices.sort(key=lambda v: v.get("cloned_by_count", 0), reverse=True)
                # Take from top 5 to ensure quality while maintaining variety
                selected_voice = random.choice(voices[: min(5, len(voices))])
            else:
                selected_voice = random.choice(voices)

            # Ensure we return with the correct field name for ElevenLabs ID
            return {
                "el_voice_id": selected_voice["voice_id"],
                "name": selected_voice["name"],
            }

        # Fallback to a default voice if nothing found
        self.logger.warning("No matching voices found, using default")
        # Use hardcoded fallback voice ID (e.g., Rachel)
        return {"el_voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel"}

    def _get_matching_voices(self, attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get voices matching the given attributes.

        Args:
            attributes: Voice attributes to match

        Returns:
            List of matching voices from ElevenLabs API
        """
        try:
            voices, _ = self.client.get_shared_voices(
                gender=attributes.get("gender"),
                accent=attributes.get("accent"),
                age=attributes.get("age"),
                language=attributes.get("language", "en"),
                use_case="informative_educational",  # Prefer educational voices
                page_size=20,
            )
            return voices
        except Exception as e:
            self.logger.error(f"Error fetching matching voices: {e}")
            return []
