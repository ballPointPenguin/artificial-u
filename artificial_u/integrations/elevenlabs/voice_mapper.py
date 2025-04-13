"""
Voice mapper for matching professor attributes to ElevenLabs voices.

This module provides functionality to match professor profiles to appropriate voices based on
characteristics like gender, nationality, accent, and age.
"""

import logging
import random
import re
from typing import Any, Dict, List, Optional

from artificial_u.models.core import Professor


class VoiceMapper:
    """
    Maps professor attributes to appropriate ElevenLabs voices.
    Provides algorithms for matching professors to voices.
    """

    # Supported accents in ElevenLabs (for English-capable voices)
    SUPPORTED_ACCENTS = [
        "american",
        "australian",
        "british",
        "canadian",
        "indian",
        "irish",
        "jamaican",
        "new_zealand",
        "nigerian",
        "scottish",
        "south_african",
        "african_american",
        "singaporean",
        "boston",
        "chicago",
        "new_york",
        "us_southern",
        "us_midwest",
        "us_northeast",
        "cockney",
        "geordie",
        "received_pronunciation",
        "scouse",
        "welsh",
        "yorkshire",
        "arabic",
        "bulgarian",
        "chinese",
        "croatian",
        "czech",
        "danish",
        "dutch",
        "filipino",
        "finnish",
        "french",
        "german",
        "greek",
        "hindi",
        "indonesian",
        "italian",
        "japanese",
        "korean",
        "malay",
        "polish",
        "portuguese",
        "romanian",
        "russian",
        "slovak",
        "spanish",
        "swedish",
        "tamil",
        "turkish",
        "ukrainian",
    ]

    def __init__(self, logger=None):
        """
        Initialize the voice mapper.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    def extract_gender(self, professor: Professor) -> Optional[str]:
        """
        Extract gender information from professor profile.

        Args:
            professor: Professor profile

        Returns:
            Gender ('male', 'female', or None for any/neutral)
        """
        # Skip processing if no gender provided
        if not hasattr(professor, "gender") or not professor.gender:
            return None

        # Normalize the input
        gender_str = professor.gender.lower().strip()

        # Use word boundaries to avoid substring issues
        # Check for explicit male indicators
        if (
            gender_str == "male"
            or gender_str == "man"
            or gender_str == "boy"
            or gender_str == "m"
            or gender_str == "he"
            or gender_str == "his"
            or gender_str == "him"
            or gender_str.startswith("he/")
            or gender_str.startswith("his/")
            or gender_str.startswith("him/")
        ):
            return "male"

        # Check for explicit female indicators
        if (
            gender_str == "female"
            or gender_str == "woman"
            or gender_str == "girl"
            or gender_str == "f"
            or gender_str == "she"
            or gender_str == "her"
            or gender_str == "hers"
            or gender_str.startswith("she/")
            or gender_str.startswith("her/")
            or gender_str.startswith("hers/")
        ):
            return "female"

        # Check for terms that should be treated as neutral/any
        neutral_terms = [
            "non-binary",
            "nonbinary",
            "enby",
            "nb",
            "genderqueer",
            "genderfluid",
            "agender",
            "they",
            "them",
            "theirs",
            "ze",
            "zir",
            "neutral",
            "any",
            "other",
        ]

        for term in neutral_terms:
            if term in gender_str or gender_str.startswith(f"{term}/"):
                return None

        # If we reach here, we're unsure - default to None (any) as requested
        self.logger.debug(
            f"Unable to determine gender from string '{professor.gender}', defaulting to None (any)"
        )
        return None

    def extract_accent(self, professor: Professor) -> Optional[str]:
        """
        Extract accent/nationality information from professor profile.

        Args:
            professor: Professor profile

        Returns:
            Optional[str]: Accent if detected, None otherwise
        """
        # If professor has an accent attribute, use it
        if hasattr(professor, "accent") and professor.accent:
            # Format accent to match API expectations
            accent = professor.accent.lower().replace(" ", "_")
            if accent in self.SUPPORTED_ACCENTS:
                return accent

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

    def extract_age(self, professor: Professor) -> str:
        """
        Extract age information from professor profile.

        Args:
            professor: Professor profile

        Returns:
            Age category ('young', 'middle_aged', 'old')
        """
        # If professor has an age attribute, use it
        if hasattr(professor, "age") and professor.age:
            if isinstance(professor.age, int):
                if professor.age < 35:
                    return "young"
                elif professor.age > 60:
                    return "old"
                else:
                    return "middle_aged"

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

    def extract_profile_attributes(self, professor: Professor) -> Dict[str, Any]:
        """
        Extract all relevant attributes from a professor profile for voice matching.

        Args:
            professor: Professor profile

        Returns:
            Dict of attributes for voice matching
        """
        # Basic attributes directly from professor fields
        gender = self.extract_gender(professor)
        accent = self.extract_accent(professor)
        age = self.extract_age(professor)

        # Build attributes dictionary
        attributes = {
            "language": "en",  # Default to English
            "use_case": "informative_educational",  # Educational content
        }

        # Only add attributes if they have values
        if gender:
            attributes["gender"] = gender
        if accent:
            attributes["accent"] = accent
        if age:
            attributes["age"] = age

        return attributes

    def rank_voices(
        self, voices: List[Dict[str, Any]], criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Rank voices by how well they match the given criteria.

        Args:
            voices: List of voice data dictionaries
            criteria: Matching criteria

        Returns:
            List of voices sorted by match quality
        """
        if not voices:
            return []

        # Calculate match score for each voice
        for voice in voices:
            score = voice.get("quality_score", 0.5)  # Start with quality score

            # Gender match is important
            if criteria.get("gender") and voice.get("gender") == criteria["gender"]:
                score += 0.3

            # Accent match is also important
            if criteria.get("accent") and voice.get("accent") == criteria["accent"]:
                score += 0.2

            # Age match is less important but still relevant
            if criteria.get("age") and voice.get("age") == criteria["age"]:
                score += 0.1

            # Use case match
            if (
                criteria.get("use_case")
                and voice.get("use_case") == criteria["use_case"]
            ):
                score += 0.1

            # Store the match score
            voice["match_score"] = score

        # Sort by match score
        return sorted(voices, key=lambda v: v.get("match_score", 0), reverse=True)

    def select_voice(
        self,
        ranked_voices: List[Dict[str, Any]],
        selection_strategy: str = "top_random",
        top_n: int = 3,
    ) -> Optional[Dict[str, Any]]:
        """
        Select a voice from a ranked list using the specified strategy.

        Args:
            ranked_voices: List of voices sorted by match quality
            selection_strategy: Strategy for selection ('top', 'top_random', 'weighted')
            top_n: Number of top voices to consider for random selection

        Returns:
            Selected voice or None if no voices available
        """
        if not ranked_voices:
            self.logger.warning("No voices available for selection")
            return None

        if selection_strategy == "top":
            # Simply take the top ranked voice
            return ranked_voices[0]

        elif selection_strategy == "top_random":
            # Take a random voice from the top N
            n = min(top_n, len(ranked_voices))
            return random.choice(ranked_voices[:n])

        elif selection_strategy == "weighted":
            # Weighted random selection based on match score
            total_score = sum(v.get("match_score", 0.1) for v in ranked_voices)
            if total_score <= 0:
                # If all scores are zero or negative, use equal weights
                return random.choice(ranked_voices)

            # Random selection with weights proportional to match scores
            r = random.random() * total_score
            cumulative = 0
            for voice in ranked_voices:
                cumulative += voice.get("match_score", 0.1)
                if cumulative >= r:
                    return voice

            # Fallback in case of floating point issues
            return ranked_voices[-1]

        else:
            # Unknown strategy, use top ranked
            self.logger.warning(
                f"Unknown selection strategy: {selection_strategy}, using top ranked"
            )
            return ranked_voices[0]
