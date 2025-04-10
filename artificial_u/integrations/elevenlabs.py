"""
Smart voice selection system for ElevenLabs integration.

This module provides functionality to match professor profiles to appropriate ElevenLabs voices
based on characteristics like gender, nationality, accent, and age.
"""

import os
import re
import random
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import json
import time

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

    # Base URL for the shared voices API
    SHARED_VOICES_URL = "https://api.elevenlabs.io/v1/shared-voices"

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

        # Initialize standard client for other operations
        self.client = ElevenLabs(api_key=self.api_key)

        # Voice mapping database for consistency
        self.voice_mapping_db = {}
        self._load_voice_mapping()

        # Voice attributes cache (now contains full voice data)
        self.voice_cache = {}
        self._load_voice_cache()

        # Headers for API requests
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

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

    def _format_voice_data(self, voice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format shared voice data into a standardized structure.

        Args:
            voice_data: Raw voice data from the API

        Returns:
            Dict[str, Any]: Formatted voice information
        """
        # Calculate quality score
        quality_score = 0.5

        # Adjust based on category
        if voice_data.get("category") == "high_quality":
            quality_score += 0.3
        elif voice_data.get("category") == "professional":
            quality_score += 0.25

        # Usage stats indicate popularity and likely quality
        if "cloned_by_count" in voice_data and voice_data["cloned_by_count"] > 1000:
            quality_score += min(0.2, voice_data["cloned_by_count"] / 100000)

        # Use data typically has better voices
        if voice_data.get("use_case") == "informative_educational":
            quality_score += 0.1

        # Cap at 1.0
        quality_score = min(1.0, quality_score)

        return {
            "voice_id": voice_data.get("voice_id", ""),
            "name": voice_data.get("name", "Unknown"),
            "gender": voice_data.get("gender", "neutral"),
            "accent": voice_data.get("accent", "american"),
            "age": voice_data.get("age", "middle_aged"),
            "category": voice_data.get("category", ""),
            "language": voice_data.get("language", "en"),
            "description": voice_data.get("description", ""),
            "preview_url": voice_data.get("preview_url", ""),
            "quality_score": quality_score,
            "cloned_by_count": voice_data.get("cloned_by_count", 0),
            "usage_character_count": voice_data.get("usage_character_count_1y", 0),
            "notice_period": voice_data.get("notice_period", None),
        }

    def get_available_voices(
        self,
        refresh: bool = False,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        language: str = "en",
        use_case: Optional[str] = None,
        category: Optional[str] = None,
        page_size: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get a list of available voices from ElevenLabs shared voices API.

        Args:
            refresh: Whether to refresh the cache
            gender: Optional filter by gender ('male', 'female', 'neutral')
            accent: Optional filter by accent
            age: Optional filter by age ('young', 'middle_aged', 'old')
            language: Language code (default 'en')
            use_case: Optional filter by use case
            category: Optional filter by category
            page_size: Number of results per page

        Returns:
            List[Dict[str, Any]]: List of voice information dictionaries
        """
        # Generate cache key based on filters
        cache_key = f"voices_{language}_{gender or 'any'}_{accent or 'any'}_{age or 'any'}_{category or 'any'}"

        # Return cached results if available and not refreshing
        if not refresh and cache_key in self.voice_cache:
            return self.voice_cache[cache_key]

        # Build query parameters
        params = {"page_size": min(page_size, 100), "language": language}

        # Add optional filters
        if gender:
            params["gender"] = gender
        if accent:
            params["accent"] = accent
        if age:
            params["age"] = age
        if use_case:
            params["use_cases"] = use_case
        if category:
            params["category"] = category

        try:
            # Make API request
            all_voices = []
            page = 0
            has_more = True

            # Get all pages until no more results
            while has_more and page < 10:  # Limit to 10 pages (1000 voices) for safety
                params["page"] = page

                response = requests.get(
                    self.SHARED_VOICES_URL, headers=self.headers, params=params
                )

                if response.status_code != 200:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    break

                data = response.json()

                # Process voices from this page
                for voice in data.get("voices", []):
                    formatted_voice = self._format_voice_data(voice)
                    all_voices.append(formatted_voice)

                    # Also store in individual voice cache
                    self.voice_cache[voice.get("voice_id")] = formatted_voice

                # Check if there are more pages
                has_more = data.get("has_more", False)
                page += 1

            # Store results in cache
            self.voice_cache[cache_key] = all_voices
            self._save_voice_cache()

            return all_voices

        except Exception as e:
            logger.error(f"Error retrieving shared voices: {e}")
            # Return empty list if error occurs
            return []

    def get_voice_by_id(
        self, voice_id: str, refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific voice by ID.

        Args:
            voice_id: The ID of the voice to retrieve
            refresh: Whether to refresh from the API

        Returns:
            Optional[Dict[str, Any]]: Voice information or None if not found
        """
        # Check cache first
        if not refresh and voice_id in self.voice_cache:
            return self.voice_cache[voice_id]

        try:
            # If using regular voices (not shared), use the client API
            try:
                response = self.client.voices.get(voice_id=voice_id)
                voice_data = {
                    "voice_id": response.voice_id,
                    "name": response.name,
                    "category": getattr(response, "category", "premade"),
                    "gender": getattr(response, "labels", {}).get("gender", "neutral"),
                    "accent": getattr(response, "labels", {}).get("accent", "american"),
                    "age": getattr(response, "labels", {}).get("age", "middle_aged"),
                    "description": getattr(response, "description", ""),
                    "preview_url": getattr(response, "preview_url", ""),
                    "quality_score": 0.8,  # Premade voices are usually high quality
                }

                self.voice_cache[voice_id] = voice_data
                self._save_voice_cache()
                return voice_data
            except:
                # If not found in regular voices, try shared voices
                # We need to search for it as there's no direct endpoint
                pass

            # Search in shared voices
            params = {"page_size": 1, "voice_id": voice_id}

            response = requests.get(
                self.SHARED_VOICES_URL, headers=self.headers, params=params
            )

            if response.status_code != 200:
                return None

            data = response.json()
            voices = data.get("voices", [])

            if not voices:
                return None

            voice_data = self._format_voice_data(voices[0])

            # Cache for future use
            self.voice_cache[voice_id] = voice_data
            self._save_voice_cache()

            return voice_data

        except Exception as e:
            logger.error(f"Error retrieving voice {voice_id}: {e}")
            return None

    def filter_voices(self, **criteria) -> List[Dict[str, Any]]:
        """
        Filter voices based on criteria.
        This method now primarily uses the API's filtering capabilities.

        Args:
            **criteria: Filtering criteria (gender, accent, age, category, etc.)

        Returns:
            List[Dict[str, Any]]: Filtered list of voices
        """
        # Extract API filter parameters
        api_filters = {}

        if "gender" in criteria:
            api_filters["gender"] = criteria.pop("gender")

        if "accent" in criteria:
            api_filters["accent"] = criteria.pop("accent")

        if "age" in criteria:
            api_filters["age"] = criteria.pop("age")

        if "category" in criteria:
            api_filters["category"] = criteria.pop("category")

        if "language" in criteria:
            api_filters["language"] = criteria.pop("language")
        else:
            api_filters["language"] = "en"  # Default to English

        if "use_case" in criteria:
            api_filters["use_case"] = criteria.pop("use_case")

        # Get voices from API with filters
        voices = self.get_available_voices(**api_filters)

        # If there are additional criteria not handled by the API, apply them here
        if criteria:
            filtered_voices = []
            for voice in voices:
                matches = True
                for key, value in criteria.items():
                    if key not in voice or voice[key] != value:
                        matches = False
                        break
                if matches:
                    filtered_voices.append(voice)
            return filtered_voices

        return voices

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

        # Sample based on quality score
        selected_indices = []
        remaining_indices = list(range(len(voices)))

        # Normalize weights
        total_weight = sum(weights)
        norm_weights = [w / total_weight for w in weights]

        # Sample without replacement
        for _ in range(min(count, len(voices))):
            if not remaining_indices:
                break

            # Get a weighted sample
            idx = random.choices(
                remaining_indices,
                weights=[norm_weights[i] for i in remaining_indices],
                k=1,
            )[0]

            selected_indices.append(idx)
            remaining_indices.remove(idx)

        return [voices[i] for i in selected_indices]

    def get_voice_for_professor(
        self,
        professor: Professor,
        refresh_cache: bool = False,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get the best matching voice for a professor.

        Args:
            professor: Professor profile
            refresh_cache: Whether to refresh the voice cache
            additional_context: Optional additional context about the professor to help with voice selection

        Returns:
            Dict[str, Any]: Selected voice information
        """
        # Check if we already have a mapping for this professor
        if professor.id and professor.id in self.voice_mapping_db:
            voice_id = self.voice_mapping_db[professor.id]
            # Verify the voice still exists
            voice = self.get_voice_by_id(voice_id, refresh=refresh_cache)
            if voice:
                return voice

        # First use the explicit fields from the professor model
        # If additional_context is provided, use those values when available
        gender = None
        accent = None
        age = None

        # Use the additional context if provided, otherwise extract from professor
        if additional_context:
            gender = additional_context.get("gender")
            accent = additional_context.get("accent")
            age = additional_context.get("age")

            # Log the provided additional context
            logger.info(
                f"Using additional context for voice selection: {additional_context}"
            )

        # If values weren't found in additional_context, extract them from the professor
        if not gender:
            gender = self._extract_gender_from_professor(professor)
        if not accent:
            accent = self._extract_accent_from_professor(professor)
        if not age:
            age = self._extract_age_from_professor(professor)

        # Convert gender formats if needed
        if gender:
            gender = gender.lower()
            if gender in ["male", "man", "m"]:
                gender = "male"
            elif gender in ["female", "woman", "f"]:
                gender = "female"
            else:
                gender = "neutral"

        # Convert age to API format if needed
        if age and isinstance(age, int):
            if age < 30:
                age = "young"
            elif age < 50:
                age = "middle_aged"
            else:
                age = "old"

        # For educational content, prefer informative voices
        use_case = "informative_educational"

        # Prioritize high-quality voices for professors
        category = None  # Try both high_quality and professional

        # Try to find matches with all criteria
        criteria = {
            "gender": gender,
            "age": age,
            "use_case": use_case,
            "language": "en",
        }

        # Add accent if available and supported
        if accent:
            # Format accent to match API expectations
            formatted_accent = accent.lower().replace(" ", "_")
            if formatted_accent in self.SUPPORTED_ACCENTS:
                criteria["accent"] = formatted_accent

        voices = self.filter_voices(**criteria)

        # Fallback 1: Try just gender and accent
        if not voices and accent:
            criteria = {"gender": gender, "accent": formatted_accent, "language": "en"}
            voices = self.filter_voices(**criteria)

        # Fallback 2: Try just gender
        if not voices:
            criteria = {"gender": gender, "language": "en"}
            voices = self.filter_voices(**criteria)

        # Fallback 3: Try just accent
        if not voices and accent:
            criteria = {"accent": formatted_accent, "language": "en"}
            voices = self.filter_voices(**criteria)

        # Fallback 4: Default to any voice
        if not voices:
            voices = self.get_available_voices(language="en", refresh=refresh_cache)

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
        return {
            "genders": ["male", "female", "neutral"],
            "accents": self.SUPPORTED_ACCENTS,
            "ages": ["young", "middle_aged", "old"],
            "categories": ["famous", "high_quality", "professional"],
            "use_cases": [
                "narrative_story",
                "conversational",
                "characters_animation",
                "social_media",
                "entertainment_tv",
                "advertisement",
                "informative_educational",
            ],
        }

    def manual_override(self, professor_id: str, voice_id: str) -> None:
        """
        Manually override the voice selection for a specific professor.

        Args:
            professor_id: ID of the professor
            voice_id: ID of the voice to use
        """
        self.voice_mapping_db[professor_id] = voice_id
        self._save_voice_mapping()

    def rebuild_cache(self, clear_existing: bool = True) -> Dict[str, Any]:
        """
        Rebuild the voice cache by fetching fresh data from the API.

        Args:
            clear_existing: Whether to clear the existing cache before rebuilding

        Returns:
            Dict[str, Any]: Status information about the rebuild operation
        """
        start_time = time.time()
        result = {
            "status": "success",
            "voices_cached": 0,
            "errors": [],
            "time_taken": 0,
        }

        try:
            # Clear existing cache if requested
            if clear_existing:
                self.voice_cache = {}
                if VOICE_CACHE_FILE.exists():
                    VOICE_CACHE_FILE.unlink()
                    logger.info("Cleared existing voice cache")

            # Fetch all voices to rebuild the cache
            languages = ["en"]  # Start with English

            for language in languages:
                # Get voices for each gender to ensure better coverage
                for gender in ["male", "female", "neutral"]:
                    try:
                        voices = self.get_available_voices(
                            refresh=True, language=language, gender=gender
                        )
                        result["voices_cached"] += len(voices)
                        logger.info(
                            f"Cached {len(voices)} {gender} voices for language {language}"
                        )
                    except Exception as e:
                        error_msg = (
                            f"Error caching {gender} voices for {language}: {str(e)}"
                        )
                        logger.error(error_msg)
                        result["errors"].append(error_msg)

            # Save the cache
            self._save_voice_cache()

            # Get some specific high-quality voices to ensure they're cached
            featured_voices = [
                "21m00Tcm4TlvDq8ikWAM",  # Rachel
                "EXAVITQu4vr4xnSDxMaL",  # Bella
                "AZnzlk1XvdvUeBnXmlld",  # Adam
                "pNInz6obpgDQGcFmaJgB",  # Adam
                "ErXwobaYiN019PkySvjV",  # Antoni
                "MF3mGyEYCl7XYWbV9V6O",  # Elli
                "TxGEqnHWrfWFTfGW9XjX",  # Josh
                "VR6AewLTigWG4xSOukaG",  # Arnold
            ]

            for voice_id in featured_voices:
                try:
                    voice = self.get_voice_by_id(voice_id, refresh=True)
                    if voice:
                        logger.info(
                            f"Cached featured voice: {voice.get('name', 'Unknown')} ({voice_id})"
                        )
                except Exception as e:
                    error_msg = f"Error caching featured voice {voice_id}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)

            # Final save
            self._save_voice_cache()

            result["status"] = "success" if not result["errors"] else "partial_success"
            result["cache_file"] = str(VOICE_CACHE_FILE)

        except Exception as e:
            error_msg = f"Error during cache rebuild: {str(e)}"
            logger.error(error_msg)
            result["errors"].append(error_msg)
            result["status"] = "error"

        # Calculate time taken
        result["time_taken"] = time.time() - start_time

        return result


# Convenience functions
def get_voice_for_professor(
    professor: Professor,
    api_key: Optional[str] = None,
    additional_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to get a voice for a professor.

    Args:
        professor: Professor profile
        api_key: Optional ElevenLabs API key
        additional_context: Optional additional context about the professor to help with voice selection

    Returns:
        Dict[str, Any]: Selected voice information
    """
    manager = VoiceSelectionManager(api_key=api_key)
    # Call the method without additional_context if it's None, otherwise pass it
    if additional_context is None:
        return manager.get_voice_for_professor(professor)
    else:
        return manager.get_voice_for_professor(
            professor, additional_context=additional_context
        )


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


def rebuild_voice_cache(
    api_key: Optional[str] = None, clear_existing: bool = True
) -> Dict[str, Any]:
    """
    Convenience function to rebuild the voice cache.

    Args:
        api_key: ElevenLabs API key
        clear_existing: Whether to clear the existing cache

    Returns:
        Dict[str, Any]: Status of the rebuild operation
    """
    manager = VoiceSelectionManager(api_key=api_key)
    return manager.rebuild_cache(clear_existing=clear_existing)


# Command-line interface for cache rebuilding
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ElevenLabs voice cache management")
    parser.add_argument(
        "--rebuild", action="store_true", help="Rebuild the voice cache"
    )
    parser.add_argument(
        "--keep", action="store_true", help="Keep existing cache entries (don't clear)"
    )
    parser.add_argument(
        "--api-key", help="ElevenLabs API key (optional, uses env var if not provided)"
    )

    args = parser.parse_args()

    if args.rebuild:
        print("Rebuilding voice cache...")
        result = rebuild_voice_cache(api_key=args.api_key, clear_existing=not args.keep)

        print(f"Status: {result['status']}")
        print(f"Cached {result['voices_cached']} voices")
        print(f"Time taken: {result['time_taken']:.2f} seconds")

        if result["errors"]:
            print(f"Encountered {len(result['errors'])} errors:")
            for i, error in enumerate(result["errors"][:5]):  # Show only first 5 errors
                print(f"  {i+1}. {error}")

            if len(result["errors"]) > 5:
                print(f"  ... and {len(result['errors']) - 5} more errors")

        print(f"Cache file: {result.get('cache_file', 'unknown')}")
    else:
        parser.print_help()
