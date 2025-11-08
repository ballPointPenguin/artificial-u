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

    # Mapping of nationalities/accents to two-letter language codes
    # Used for converting accent descriptions to language codes for API queries
    ACCENT_TO_LANGUAGE_MAP = {
        # English variants
        "american": "en",
        "british": "en",
        "australian": "en",
        "canadian": "en",
        "irish": "en",
        "scottish": "en",
        "welsh": "en",
        "new_zealand": "en",
        "south_african": "en",
        "indian": "en",  # For English-speaking Indians
        "singaporean": "en",
        "nigerian": "en",
        "jamaican": "en",
        # Other languages
        "french": "fr",
        "german": "de",
        "spanish": "es",
        "italian": "it",
        "portuguese": "pt",
        "russian": "ru",
        "polish": "pl",
        "czech": "cs",
        "slovak": "sk",
        "croatian": "hr",
        "bulgarian": "bg",
        "romanian": "ro",
        "greek": "el",
        "turkish": "tr",
        "arabic": "ar",
        "hebrew": "he",
        "hindi": "hi",
        "tamil": "ta",
        "chinese": "zh",
        "japanese": "ja",
        "korean": "ko",
        "vietnamese": "vi",
        "thai": "th",
        "indonesian": "id",
        "malay": "ms",
        "filipino": "tl",
        "dutch": "nl",
        "danish": "da",
        "swedish": "sv",
        "norwegian": "no",
        "finnish": "fi",
        "ukrainian": "uk",
        # Regional variants (map to primary language)
        "mexican": "es",
        "argentinian": "es",
        "brazilian": "pt",
        "quebec": "fr",
        "athenian": "el",
    }

    def __init__(self, logger=None):
        """
        Initialize the voice mapper.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    def _detect_accent_from_text(self, accent_text: str) -> Optional[str]:
        """Best-effort detection of accent keyword from free-text.

        Prefers any detected non-English accent over English variants.
        """
        tokens = re.split(r"[^a-z]+", accent_text)
        tokens = [t for t in tokens if t]

        detected_accents: List[str] = []
        for token in tokens:
            if token in self.ACCENT_TO_LANGUAGE_MAP:
                detected_accents.append(token)

        if detected_accents:
            for acc in detected_accents:
                if self.ACCENT_TO_LANGUAGE_MAP.get(acc) != "en":
                    return acc
            return detected_accents[0]

        # Fallback: substring search for any known key
        for key in self.ACCENT_TO_LANGUAGE_MAP.keys():
            if key in accent_text:
                return key
        return None

    def _extract_gender(self, professor: Professor) -> Optional[str]:
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

    def _extract_accent(self, professor: Professor) -> Optional[str]:
        """
        Extract accent/nationality information from professor profile.

        Args:
            professor: Professor profile

        Returns:
            Optional[str]: Accent if detected, None otherwise
        """
        # If professor has an accent attribute, try to normalize it to a known accent token
        if hasattr(professor, "accent") and professor.accent:
            accent_text = professor.accent.lower().strip()
            self.logger.debug(f"Parsing accent text: '{accent_text}'")
            detected = self._detect_accent_from_text(accent_text)
            if detected:
                return detected
            # If we couldn't parse, return the raw text so downstream can still attempt mapping
            return accent_text

        # Extract from background as fallback
        background = professor.background.lower()
        self.logger.debug(f"Falling back to background extraction: '{background[:100]}...'")

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
            "greek": ["greece", "athens", "greek"],
        }

        for accent, indicators in nationality_accents.items():
            if any(indicator in background for indicator in indicators):
                self.logger.debug(f"Found accent '{accent}' from background indicators")
                return accent

        # No clear accent detected
        self.logger.debug("No accent detected from either accent field or background")
        return None

    def accent_to_language_code(self, accent: Optional[str]) -> str:
        """
        Convert an accent string to a two-letter language code.

        Args:
            accent: Accent string (e.g., "british", "french", "athenian")

        Returns:
            Two-letter language code (defaults to "en" if not found)
        """
        if not accent:
            return "en"

        accent_lower = accent.lower().strip()

        # Check if it's already a two-letter code
        if len(accent_lower) == 2:
            return accent_lower

        # Direct look up first
        direct = self.ACCENT_TO_LANGUAGE_MAP.get(accent_lower)
        if direct:
            return direct

        # Try substring/keyword matching across known accents
        matched_codes: List[str] = []
        for key, code in self.ACCENT_TO_LANGUAGE_MAP.items():
            if key in accent_lower:
                matched_codes.append(code)

        # Prefer any non-English code if present, otherwise fall back to English
        for code in matched_codes:
            if code != "en":
                return code
        if matched_codes:
            return matched_codes[0]

        # Default to English
        return "en"

    def _extract_age(self, professor: Professor) -> str:
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
                if professor.age < 40:
                    return "young"
                elif professor.age > 75:
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

    def _calculate_quality_score(self, voice: Dict[str, Any]) -> float:
        """
        Calculate a quality score for a voice based on its attributes.
        """
        quality_score = 0.5

        # Prioritize premade voices highest
        if voice.get("category") == "premade":
            quality_score += 0.45
        # Then high_quality and professional
        elif voice.get("category") == "high_quality":
            quality_score += 0.35
        elif voice.get("category") == "professional":
            quality_score += 0.25

        # Usage stats indicate popularity and likely quality
        if "cloned_by_count" in voice and voice["cloned_by_count"] > 1000:
            quality_score += min(0.2, voice["cloned_by_count"] / 100000)

        # Use-case signals typically correlate with better narration quality
        if voice.get("use_case") in {
            "informative_educational",
            "conversational",
            "narrative_story",
            "narration",
        }:
            quality_score += 0.1

        # Cap at 1.0
        quality_score = min(1.0, quality_score)

        return quality_score

    def _calculate_voice_match_score(
        self, voice: Dict[str, Any], criteria: Dict[str, Any]
    ) -> float:
        """
        Calculate match score for a single voice against criteria.

        Args:
            voice: Voice data dictionary
            criteria: Matching criteria

        Returns:
            Match score for the voice
        """
        # Start with quality score
        quality_score = self._calculate_quality_score(voice)
        score = quality_score

        # Gender match is important
        voice_gender = voice.get("gender")
        criteria_gender = criteria.get("gender")
        if criteria_gender and voice_gender == criteria_gender:
            score += 0.3
            # self.logger.debug(f"  +0.3 for gender match: {voice_gender}")

        # Accent match is also important
        voice_accent = voice.get("accent")
        criteria_accent = criteria.get("accent")
        if criteria_accent and voice_accent == criteria_accent:
            score += 0.2
            # self.logger.debug(f"  +0.2 for accent match: {voice_accent}")

        # Age match is less important but still relevant
        voice_age = voice.get("age")
        criteria_age = criteria.get("age")
        if criteria_age and voice_age == criteria_age:
            score += 0.1
            # self.logger.debug(f"  +0.1 for age match: {voice_age}")

        # Use case match
        voice_use_case = voice.get("use_case")
        criteria_use_case = criteria.get("use_case")
        if criteria_use_case and voice_use_case == criteria_use_case:
            score += 0.1
            # self.logger.debug(f"  +0.1 for use case match: {voice_use_case}")

        return score

    def _apply_reuse_penalty(
        self, voice: Dict[str, Any], used_voice_ids: Optional[List[str]]
    ) -> None:
        """
        Apply penalty if voice is already in use.

        Args:
            voice: Voice data dictionary
            used_voice_ids: List of voice IDs already in use
        """
        if used_voice_ids and voice.get("el_voice_id") in used_voice_ids:
            voice["match_score"] -= 0.3  # Significant penalty for reuse
            # self.logger.debug("  -0.3 penalty for voice already in use")

    def extract_profile_attributes(self, professor: Professor) -> Dict[str, Any]:
        """
        Extract all relevant attributes from a professor profile for voice matching.

        Args:
            professor: Professor profile

        Returns:
            Dict of attributes for voice matching
        """
        # Basic attributes directly from professor fields
        gender = self._extract_gender(professor)
        accent = self._extract_accent(professor)
        age = self._extract_age(professor)

        # Convert accent to language code
        language = self.accent_to_language_code(accent)

        # Build attributes dictionary
        attributes = {
            "language": language,  # Use derived language code
        }

        # Only add attributes if they have values
        if gender:
            attributes["gender"] = gender
        if accent:
            attributes["accent"] = accent  # Keep original accent for matching
        if age:
            attributes["age"] = age

        return attributes

    def rank_voices(
        self,
        voices: List[Dict[str, Any]],
        criteria: Dict[str, Any],
        used_voice_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rank voices by how well they match the given criteria.

        Args:
            voices: List of voice data dictionaries
            criteria: Matching criteria
            used_voice_ids: Optional list of voice IDs already in use

        Returns:
            List of voices sorted by match quality
        """
        self.logger.debug(f"=== Starting voice ranking for {len(voices)} voices ===")
        self.logger.debug(f"Ranking criteria: {criteria}")

        if not voices:
            self.logger.debug("No voices to rank, returning empty list")
            return []

        # Calculate match score for each voice
        self.logger.debug("Calculating match scores for each voice...")
        for i, voice in enumerate(voices):
            # voice_name = voice.get("name", f"Voice_{i}")
            # voice_id = voice.get("el_voice_id", "unknown")

            # self.logger.debug(f"Voice {i+1}: {voice_name} (ID: {voice_id})")

            # Calculate base match score
            score = self._calculate_voice_match_score(voice, criteria)
            voice["match_score"] = score

            # Apply reuse penalty
            self._apply_reuse_penalty(voice, used_voice_ids)

            # self.logger.debug(f"  Final match score: {voice['match_score']:.3f}")

        # Sort by match score
        ranked_voices = sorted(voices, key=lambda v: v.get("match_score", 0), reverse=True)

        self.logger.debug("=== Voice ranking completed ===")
        self.logger.debug("Top 8 ranked voices:")
        for i, voice in enumerate(ranked_voices[:8]):
            name = voice.get("name", f"Voice_{i}")
            voice_id = voice.get("el_voice_id", "unknown")
            score = voice.get("match_score", 0)
            self.logger.debug(f"  {i+1}. {name} (ID: {voice_id}) - Score: {score:.3f}")

        return ranked_voices

    def select_voice(
        self,
        ranked_voices: List[Dict[str, Any]],
        selection_strategy: str = "top_random",
        top_n: int = 8,
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
        self.logger.debug("=== Starting voice selection ===")
        self.logger.debug(f"Strategy: {selection_strategy}, Top N: {top_n}")
        self.logger.debug(f"Available voices: {len(ranked_voices)}")

        if not ranked_voices:
            self.logger.warning("No voices available for selection")
            return None

        if selection_strategy == "top":
            # Simply take the top ranked voice
            selected = ranked_voices[0]
            self.logger.debug(
                f"Selected top voice: {selected.get('name', 'Unknown')} "
                f"(ID: {selected.get('el_voice_id', 'Unknown')})"
            )
            return selected

        elif selection_strategy == "top_random":
            # Take a random voice from the top N
            n = min(top_n, len(ranked_voices))
            self.logger.debug(f"Random selection from top {n} voices")

            # Log the candidates
            candidates = ranked_voices[:n]
            self.logger.debug("Candidates for random selection:")
            for i, voice in enumerate(candidates):
                name = voice.get("name", f"Voice_{i}")
                voice_id = voice.get("el_voice_id", "unknown")
                score = voice.get("match_score", 0)
                self.logger.debug(f"  {i+1}. {name} (ID: {voice_id}) - Score: {score:.3f}")

            selected = random.choice(candidates)
            selected_name = selected.get("name", "Unknown")
            selected_id = selected.get("el_voice_id", "Unknown")
            self.logger.debug(f"Randomly selected: {selected_name} (ID: {selected_id})")
            return selected

        elif selection_strategy == "weighted":
            # Weighted random selection based on match score
            self.logger.debug("Using weighted random selection")

            total_score = sum(v.get("match_score", 0.1) for v in ranked_voices)
            self.logger.debug(f"Total score: {total_score:.3f}")

            if total_score <= 0:
                # If all scores are zero or negative, use equal weights
                self.logger.debug("All scores <= 0, using equal weights")
                selected = random.choice(ranked_voices)
                self.logger.debug(
                    f"Equal weight selected: {selected.get('name', 'Unknown')} "
                    f"(ID: {selected.get('el_voice_id', 'Unknown')})"
                )
                return selected

            # Random selection with weights proportional to match scores
            r = random.random() * total_score
            self.logger.debug(f"Random threshold: {r:.3f}")

            cumulative = 0
            for i, voice in enumerate(ranked_voices):
                voice_score = voice.get("match_score", 0.1)
                cumulative += voice_score
                voice_name = voice.get("name", "Unknown")
                self.logger.debug(
                    f"Voice {i+1}: {voice_name} - Score: {voice_score:.3f}, "
                    f"Cumulative: {cumulative:.3f}"
                )

                if cumulative >= r:
                    voice_id = voice.get("el_voice_id", "Unknown")
                    self.logger.debug(f"Weighted selection: {voice_name} (ID: {voice_id})")
                    return voice

            # Fallback in case of floating point issues
            self.logger.debug("Using fallback selection (last voice)")
            selected = ranked_voices[-1]
            selected_name = selected.get("name", "Unknown")
            selected_id = selected.get("el_voice_id", "Unknown")
            self.logger.debug(f"Fallback selected: {selected_name} (ID: {selected_id})")
            return selected

        else:
            # Unknown strategy, use top ranked
            self.logger.warning(
                f"Unknown selection strategy: {selection_strategy}, using top ranked"
            )
            selected = ranked_voices[0]
            selected_name = selected.get("name", "Unknown")
            selected_id = selected.get("el_voice_id", "Unknown")
            self.logger.debug(f"Unknown strategy fallback: {selected_name} (ID: {selected_id})")
            return selected
