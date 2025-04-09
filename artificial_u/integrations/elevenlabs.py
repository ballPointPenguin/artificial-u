"""
Smart voice selection system for ElevenLabs integration.

This module provides functionality to match professor profiles to appropriate ElevenLabs voices
based on characteristics like gender, nationality, accent, and age.
"""

import os
import re
import random
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json

from elevenlabs.client import ElevenLabs
from artificial_u.models.core import Professor

# Set up logging
logger = logging.getLogger(__name__)

# Cache directory for voice data
CACHE_DIR = Path(os.environ.get("CACHE_DIR", "./.cache/elevenlabs"))
VOICE_CACHE_FILE = CACHE_DIR / "voice_data.json"


class VoiceSelectionManager:
    """
    Manages the selection of appropriate ElevenLabs voices for professors.
    Implements smart matching based on professor characteristics and includes
    fallback strategies for when ideal matches aren't available.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the voice selection manager.

        Args:
            api_key: ElevenLabs API key. If not provided, will use ELEVENLABS_API_KEY environment variable.
        """
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")

        # Initialize cache directory
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize client
        self.client = ElevenLabs(api_key=self.api_key)

        # Voice mapping database for consistency
        self.voice_mapping_db = {}
        self._load_voice_mapping()

        # Voice attributes cache
        self.voice_cache = {}
        self._load_voice_cache()

    def _load_voice_mapping(self):
        """Load the professor-to-voice mapping database from file."""
        mapping_file = CACHE_DIR / "voice_mapping.json"
        if mapping_file.exists():
            try:
                with open(mapping_file, "r") as f:
                    self.voice_mapping_db = json.load(f)
            except Exception as e:
                logger.error(f"Error loading voice mapping database: {e}")

    def _save_voice_mapping(self):
        """Save the professor-to-voice mapping database to file."""
        mapping_file = CACHE_DIR / "voice_mapping.json"
        try:
            with open(mapping_file, "w") as f:
                json.dump(self.voice_mapping_db, f)
        except Exception as e:
            logger.error(f"Error saving voice mapping database: {e}")

    def _load_voice_cache(self):
        """Load the voice attribute cache from file."""
        if VOICE_CACHE_FILE.exists():
            try:
                with open(VOICE_CACHE_FILE, "r") as f:
                    self.voice_cache = json.load(f)
            except Exception as e:
                logger.error(f"Error loading voice cache: {e}")

    def _save_voice_cache(self):
        """Save the voice attribute cache to file."""
        try:
            with open(VOICE_CACHE_FILE, "w") as f:
                json.dump(self.voice_cache, f)
        except Exception as e:
            logger.error(f"Error saving voice cache: {e}")

    def get_available_voices(self, refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get a list of available voices from ElevenLabs.

        Args:
            refresh: Whether to refresh the cache

        Returns:
            List[Dict[str, Any]]: List of voice information dictionaries
        """
        if not refresh and self.voice_cache:
            return list(self.voice_cache.values())

        try:
            response = self.client.voices.get_all()
            voices = []

            for voice in response.voices:
                voice_data = {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": getattr(voice, "category", "premade"),
                    "description": getattr(voice, "description", ""),
                    "preview_url": getattr(voice, "preview_url", ""),
                    # Parse additional metadata from description and labels
                    "gender": self._extract_gender(voice),
                    "accent": self._extract_accent(voice),
                    "age": self._extract_age(voice),
                    "is_cloned": getattr(voice, "category", "") == "cloned",
                    "quality_score": self._calculate_quality_score(voice),
                }

                voices.append(voice_data)
                self.voice_cache[voice.voice_id] = voice_data

            self._save_voice_cache()
            return voices

        except Exception as e:
            logger.error(f"Error retrieving voices: {e}")
            return list(self.voice_cache.values()) if self.voice_cache else []

    def _extract_gender(self, voice) -> str:
        """
        Extract gender information from voice metadata.

        Args:
            voice: ElevenLabs voice object

        Returns:
            str: Gender ('male', 'female', or 'neutral')
        """
        # Look for gender information in labels
        labels = getattr(voice, "labels", {})
        if labels and "gender" in labels:
            return labels["gender"].lower()

        # Look for gender information in description
        description = getattr(voice, "description", "").lower()

        # Check for female indicators first (to avoid 'female' matching 'male')
        female_indicators = ["female", "woman", "girl", "feminine", "her ", "she "]
        if any(indicator in description for indicator in female_indicators):
            return "female"

        # Check for male indicators
        male_indicators = ["male", "man", "boy", "masculine", "his ", "him "]
        if any(indicator in description for indicator in male_indicators):
            return "male"

        # Default based on name if available
        name = getattr(voice, "name", "").lower()
        # Use word boundaries to avoid partial matches like 'john' in 'johnson'
        male_names = [
            r"\bjames\b",
            r"\bjohn\b",
            r"\badam\b",
            r"\bjosh\b",
            r"\barnold\b",
            r"\bsam\b",
            r"\bthomas\b",
            r"\bmichael\b",
        ]
        female_names = [
            r"\brachel\b",
            r"\bdomi\b",
            r"\bbella\b",
            r"\belli\b",
            r"\bemily\b",
            r"\bsarah\b",
            r"\bgrace\b",
            r"\bmary\b",
        ]

        if any(re.search(pattern, name) for pattern in male_names):
            return "male"
        elif any(re.search(pattern, name) for pattern in female_names):
            return "female"

        # Default to neutral if we can't determine
        return "neutral"

    def _extract_accent(self, voice) -> str:
        """
        Extract accent information from voice metadata.

        Args:
            voice: ElevenLabs voice object

        Returns:
            str: Accent (e.g., 'american', 'british', etc.)
        """
        # Look for accent in labels
        labels = getattr(voice, "labels", {})
        if labels and "accent" in labels:
            return labels["accent"].lower()

        # Look for accent info in description
        description = getattr(voice, "description", "").lower()

        # Common accent keywords
        accent_keywords = {
            "american": ["american", "us ", "united states", "californian"],
            "british": ["british", "uk ", "england", "london"],
            "australian": ["australian", "aussie", "australia"],
            "indian": ["indian", "india"],
            "german": ["german", "germany"],
            "french": ["french", "france"],
            "spanish": ["spanish", "spain"],
            "italian": ["italian", "italy"],
            "japanese": ["japanese", "japan"],
            "chinese": ["chinese", "china", "mandarin"],
            "russian": ["russian", "russia"],
            "irish": ["irish", "ireland", "scottish", "scotland"],
            "canadian": ["canadian", "canada"],
            "swedish": ["swedish", "sweden"],
        }

        for accent, keywords in accent_keywords.items():
            if any(keyword in description for keyword in keywords):
                return accent

        # Default to american if we can't determine (most common default)
        return "american"

    def _extract_age(self, voice) -> str:
        """
        Extract age information from voice metadata.

        Args:
            voice: ElevenLabs voice object

        Returns:
            str: Age category ('young', 'middle_aged', 'old')
        """
        # Look for age in labels
        labels = getattr(voice, "labels", {})
        if labels and "age" in labels:
            return labels["age"].lower()

        # Extract from description
        description = getattr(voice, "description", "").lower()

        # Age-related keywords
        young_keywords = ["young", "youthful", "teen", "20s", "twenties"]
        old_keywords = ["elderly", "old", "mature", "senior", "60s", "70s", "eighties"]

        if any(keyword in description for keyword in young_keywords):
            return "young"
        elif any(keyword in description for keyword in old_keywords):
            return "old"

        # Default to middle-aged if we can't determine
        return "middle_aged"

    def _calculate_quality_score(self, voice) -> float:
        """
        Calculate a quality score for the voice, used for ranking.

        Args:
            voice: ElevenLabs voice object

        Returns:
            float: Quality score between 0-1
        """
        # Base quality score
        quality = 0.5

        # Default/premade voices typically have higher quality
        if getattr(voice, "category", "") == "premade":
            quality += 0.3

        # Professional clones have better quality than community ones
        labels = getattr(voice, "labels", {})
        if labels and "professional" in labels:
            quality += 0.2

        # Additional metadata might indicate quality (likes, etc.)
        if hasattr(voice, "likes") and voice.likes is not None:
            if voice.likes > 100:
                quality += min(0.2, voice.likes / 1000)  # Cap at 0.2

        # Preview availability might indicate better testing
        if hasattr(voice, "preview_url") and voice.preview_url:
            quality += 0.1

        # Cap at 1.0
        return min(1.0, quality)

    def filter_voices(self, **criteria) -> List[Dict[str, Any]]:
        """
        Filter available voices based on criteria.

        Args:
            **criteria: Filtering criteria (gender, accent, age, category, etc.)

        Returns:
            List[Dict[str, Any]]: Filtered list of voices
        """
        # Ensure we have voice data
        voices = self.get_available_voices()

        # Apply filters
        filtered_voices = voices

        for key, value in criteria.items():
            # Skip None values
            if value is None:
                continue

            # Filter voices that match the criterion
            filtered_voices = [
                voice
                for voice in filtered_voices
                if (key in voice and voice[key] == value)
            ]

        return filtered_voices

    def sample_voices_by_criteria(
        self, count: int = 3, **criteria
    ) -> List[Dict[str, Any]]:
        """
        Sample a number of voices matching the given criteria.

        Args:
            count: Number of voices to return
            **criteria: Filtering criteria

        Returns:
            List[Dict[str, Any]]: Sampled voices
        """
        # Get filtered voices
        voices = self.filter_voices(**criteria)

        # If not enough voices, try relaxing criteria
        if len(voices) < count:
            # Try without accent
            if "accent" in criteria:
                accent = criteria.pop("accent")
                voices = self.filter_voices(**criteria)
                # If still not enough, try with original criteria but any gender
                if len(voices) < count and "gender" in criteria:
                    # Restore accent but remove gender
                    criteria["accent"] = accent
                    gender = criteria.pop("gender")
                    voices = self.filter_voices(**criteria)
                    # If still not enough, remove all filtering
                    if len(voices) < count:
                        voices = self.get_available_voices()
            # If not filtering by accent but by gender and not enough
            elif "gender" in criteria and len(voices) < count:
                # Remove gender filter
                criteria.pop("gender")
                voices = self.filter_voices(**criteria)

        # Sort by quality score
        voices = sorted(voices, key=lambda v: v.get("quality_score", 0), reverse=True)

        # Sample voices, prioritizing higher quality
        if len(voices) <= count:
            return voices

        # Weighted random sampling based on quality score
        weights = [v.get("quality_score", 0.5) for v in voices]
        # Ensure all weights are positive
        min_weight = min(weights)
        if min_weight <= 0:
            weights = [w - min_weight + 0.1 for w in weights]

        # Sample without replacement
        selected_indices = random.sample(
            range(len(voices)),
            k=min(count, len(voices)),
            counts=[int(w * 100) for w in weights],  # Convert to integer counts
        )

        return [voices[i] for i in selected_indices]

    def get_voice_for_professor(
        self, professor: Professor, refresh_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Get the best matching voice for a professor.

        Args:
            professor: Professor profile
            refresh_cache: Whether to refresh the voice cache

        Returns:
            Dict[str, Any]: Selected voice information
        """
        # Check if we already have a mapping for this professor
        if professor.id and professor.id in self.voice_mapping_db:
            voice_id = self.voice_mapping_db[professor.id]
            # Verify the voice still exists
            voices = self.get_available_voices(refresh=refresh_cache)
            for voice in voices:
                if voice["voice_id"] == voice_id:
                    return voice

        # Extract professor characteristics
        gender = self._extract_gender_from_professor(professor)
        accent = self._extract_accent_from_professor(professor)
        age = self._extract_age_from_professor(professor)

        # Try to find matches with all criteria
        voices = self.filter_voices(gender=gender, accent=accent, age=age)

        # Fallback 1: Try just gender and accent
        if not voices:
            voices = self.filter_voices(gender=gender, accent=accent)

        # Fallback 2: Try just gender
        if not voices:
            voices = self.filter_voices(gender=gender)

        # Fallback 3: Try just accent
        if not voices and accent:
            voices = self.filter_voices(accent=accent)

        # Fallback 4: Default to any voice
        if not voices:
            voices = self.get_available_voices(refresh=refresh_cache)

        # Sort by quality and choose the best one (or random from top 3)
        if voices:
            voices = sorted(
                voices, key=lambda v: v.get("quality_score", 0), reverse=True
            )
            selected_voice = random.choice(voices[: min(3, len(voices))])

            # Save mapping for future consistency
            if professor.id:
                self.voice_mapping_db[professor.id] = selected_voice["voice_id"]
                self._save_voice_mapping()

            return selected_voice

        # Should never reach here if get_available_voices returns a non-empty list
        raise ValueError("No voices available")

    def _extract_gender_from_professor(self, professor: Professor) -> str:
        """
        Extract gender information from professor profile.

        Args:
            professor: Professor profile

        Returns:
            str: Gender ('male', 'female', or 'neutral')
        """
        # Extract from background or name
        background = professor.background.lower()
        name = professor.name.lower()

        # Check for female indicators first (to avoid 'female' matching 'male')
        female_indicators = [
            "she ",
            "her ",
            "female",
            "woman",
            "lady",
            "mrs.",
            "mrs ",
            "ms.",
            "ms ",
            "miss",
            "mother",
            "sister",
            "daughter",
        ]
        if any(indicator in background for indicator in female_indicators):
            return "female"

        # Check for male indicators
        male_indicators = [
            "he ",
            "his ",
            "him ",
            "male",
            "man",
            "gentleman",
            "mr.",
            "mr ",
            "sir",
            "father",
            "brother",
            "son",
        ]
        if any(indicator in background for indicator in male_indicators):
            return "male"

        # Check name prefix
        if re.search(r"\b(mr|mister|sir|lord)\b", name):
            return "male"
        elif re.search(r"\b(mrs|miss|ms|madam|lady|sister)\b", name):
            return "female"

        # Check common name patterns with word boundaries
        # This is oversimplified and not inclusive of all cultures
        if re.search(
            r"\b(john|james|robert|michael|william|david|richard)\b",
            name,
            re.IGNORECASE,
        ):
            return "male"
        elif re.search(
            r"\b(mary|patricia|jennifer|linda|elizabeth|barbara|susan)\b",
            name,
            re.IGNORECASE,
        ):
            return "female"

        # Default to neutral if we can't determine
        return "neutral"

    def _extract_accent_from_professor(self, professor: Professor) -> Optional[str]:
        """
        Extract accent/nationality information from professor profile.

        Args:
            professor: Professor profile

        Returns:
            Optional[str]: Accent if detected, None otherwise
        """
        # Extract from background
        background = professor.background.lower()

        # Nationality/region indicators with corresponding accents
        nationality_accents = {
            "american": ["american", "united states", "u.s.", "usa"],
            "british": ["british", "england", "uk", "scotland", "wales", "london"],
            "australian": ["australia", "aussie", "sydney", "melbourne"],
            "indian": ["india", "mumbai", "delhi", "bangalore"],
            "german": ["germany", "berlin", "munich", "frankfurt", "hamburg"],
            "french": ["france", "paris", "lyon", "marseille"],
            "spanish": ["spain", "madrid", "barcelona", "spanish"],
            "italian": ["italy", "rome", "milan", "naples", "italian"],
            "russian": ["russia", "moscow", "st. petersburg", "russian"],
            "japanese": ["japan", "tokyo", "kyoto", "japanese"],
            "chinese": ["china", "beijing", "shanghai", "chinese", "mandarin"],
            "canadian": ["canada", "toronto", "vancouver", "montreal", "canadian"],
            "irish": ["ireland", "dublin", "irish"],
            "swedish": ["sweden", "stockholm", "swedish"],
            "mexican": ["mexico", "mexican", "mexico city"],
            "nigerian": ["nigeria", "lagos", "nigerian"],
        }

        for accent, indicators in nationality_accents.items():
            if any(indicator in background for indicator in indicators):
                return accent

        # No clear accent detected
        return None

    def _extract_age_from_professor(self, professor: Professor) -> str:
        """
        Extract age information from professor profile.

        Args:
            professor: Professor profile

        Returns:
            str: Age category ('young', 'middle_aged', 'old')
        """
        # Extract from background
        background = professor.background.lower()

        # Look for explicit age
        age_match = re.search(r"(\d+)[- ]year[s]?[- ]old", background)
        if age_match:
            age = int(age_match.group(1))
            if age < 35:
                return "young"
            elif age > 60:
                return "old"
            else:
                return "middle_aged"

        # Look for age indicators
        young_indicators = ["young", "early career", "junior", "assistant professor"]
        old_indicators = ["emeritus", "veteran", "senior", "distinguished", "retired"]

        if any(indicator in background for indicator in young_indicators):
            return "young"
        elif any(indicator in background for indicator in old_indicators):
            return "old"

        # Default to middle-aged for professors
        return "middle_aged"

    def list_available_voice_filters(self) -> Dict[str, List[str]]:
        """
        Get a list of available filter categories and values.

        Returns:
            Dict[str, List[str]]: Filter categories and their possible values
        """
        voices = self.get_available_voices()

        filters = {
            "genders": set(),
            "accents": set(),
            "ages": set(),
            "categories": set(),
        }

        for voice in voices:
            if "gender" in voice and voice["gender"]:
                filters["genders"].add(voice["gender"])
            if "accent" in voice and voice["accent"]:
                filters["accents"].add(voice["accent"])
            if "age" in voice and voice["age"]:
                filters["ages"].add(voice["age"])
            if "category" in voice and voice["category"]:
                filters["categories"].add(voice["category"])

        # Convert sets to sorted lists
        return {k: sorted(list(v)) for k, v in filters.items()}

    def manual_override(self, professor_id: str, voice_id: str) -> None:
        """
        Manually override the voice selection for a specific professor.

        Args:
            professor_id: ID of the professor
            voice_id: ID of the voice to use
        """
        self.voice_mapping_db[professor_id] = voice_id
        self._save_voice_mapping()


# Convenience functions
def get_voice_for_professor(
    professor: Professor, api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to get a voice for a professor.

    Args:
        professor: Professor profile
        api_key: Optional ElevenLabs API key

    Returns:
        Dict[str, Any]: Selected voice information
    """
    manager = VoiceSelectionManager(api_key=api_key)
    return manager.get_voice_for_professor(professor)


def sample_voices(
    count: int = 3,
    gender: Optional[str] = None,
    accent: Optional[str] = None,
    age: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Sample voices matching criteria.

    Args:
        count: Number of voices to return
        gender: Optional gender filter
        accent: Optional accent filter
        age: Optional age filter
        api_key: Optional ElevenLabs API key

    Returns:
        List[Dict[str, Any]]: List of sampled voices
    """
    manager = VoiceSelectionManager(api_key=api_key)
    criteria = {}
    if gender:
        criteria["gender"] = gender
    if accent:
        criteria["accent"] = accent
    if age:
        criteria["age"] = age

    return manager.sample_voices_by_criteria(count=count, **criteria)


def get_voice_filters(api_key: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Get available voice filters.

    Args:
        api_key: Optional ElevenLabs API key

    Returns:
        Dict[str, List[str]]: Filter categories and possible values
    """
    manager = VoiceSelectionManager(api_key=api_key)
    return manager.list_available_voice_filters()
