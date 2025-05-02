"""
Smart voice selection system for ElevenLabs integration.

This module provides functionality to match professor profiles to appropriate ElevenLabs voices
based on characteristics like gender, nationality, accent, and age.
"""

import logging
import os
import random
from typing import Any, Dict, List, Optional

import requests
from elevenlabs.client import ElevenLabs

# Set up logging
logger = logging.getLogger(__name__)


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

        # Initialize standard client for other operations
        self.client = ElevenLabs(api_key=self.api_key)

        # Headers for API requests
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

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
            "el_voice_id": voice_data.get("voice_id", ""),
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

                # Check if there are more pages
                has_more = data.get("has_more", False)
                page += 1

            return all_voices

        except Exception as e:
            logger.error(f"Error retrieving shared voices: {e}")
            # Return empty list if error occurs
            return []

    def get_voice_by_el_id(self, el_voice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific voice by ElevenLabs voice ID using the standard client.

        Args:
            el_voice_id: The ID of the voice to retrieve

        Returns:
            Optional[Dict[str, Any]]: Voice information or None if not found
        """
        try:
            response = self.client.voices.get(voice_id=el_voice_id)
            # Format the response, using None for missing optional attributes
            voice_data = {
                "el_voice_id": response.voice_id,
                "name": response.name,
                "category": getattr(
                    response, "category", None
                ),  # Premade, cloned, professional, generated
                "gender": (
                    getattr(response.labels, "gender", None)
                    if response.labels
                    else None
                ),
                "accent": (
                    getattr(response.labels, "accent", None)
                    if response.labels
                    else None
                ),
                "age": (
                    getattr(response.labels, "age", None) if response.labels else None
                ),
                "description": (
                    getattr(response.labels, "description", None)
                    if response.labels
                    else None
                ),
                "preview_url": getattr(response, "preview_url", None),
            }
            return voice_data
        except (
            Exception
        ) as e:  # Catch specific exceptions if known, e.g., elevenlabs.ApiException
            logger.warning(
                f"Could not retrieve voice {el_voice_id} using standard client: {e}"
            )
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
        el_voices = self.get_available_voices(**api_filters)

        # If there are additional criteria not handled by the API, apply them here
        if criteria:
            filtered_voices = []
            for el_voice in el_voices:
                matches = True
                for key, value in criteria.items():
                    if key not in el_voice or el_voice[key] != value:
                        matches = False
                        break
                if matches:
                    filtered_voices.append(el_voice)
            return filtered_voices

        return el_voices

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
        el_voices = self.filter_voices(**criteria)

        # If not enough voices, try relaxing criteria
        if len(el_voices) < count:
            # Try without accent
            if "accent" in criteria:
                accent = criteria.pop("accent")
                el_voices = self.filter_voices(**criteria)
                # If still not enough, try with original criteria but any gender
                if len(el_voices) < count and "gender" in criteria:
                    # Restore accent but remove gender
                    criteria["accent"] = accent
                    criteria.pop("gender")
                    el_voices = self.filter_voices(**criteria)
                    # If still not enough, remove all filtering
                    if len(el_voices) < count:
                        el_voices = self.get_available_voices()
            # If not filtering by accent but by gender and not enough
            elif "gender" in criteria and len(el_voices) < count:
                # Remove gender filter
                criteria.pop("gender")
                el_voices = self.filter_voices(**criteria)

        # Sample voices, prioritizing higher quality
        if len(el_voices) <= count:
            return el_voices

        # Weighted random sampling based on quality score
        weights = [v.get("quality_score", 0.5) for v in el_voices]
        # Ensure all weights are positive
        min_weight = min(weights)
        if min_weight <= 0:
            weights = [w - min_weight + 0.1 for w in weights]

        # Sample based on quality score
        selected_indices = []
        remaining_indices = list(range(len(el_voices)))

        # Normalize weights
        total_weight = sum(weights)
        norm_weights = [w / total_weight for w in weights]

        # Sample without replacement
        for _ in range(min(count, len(el_voices))):
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

        return [el_voices[i] for i in selected_indices]

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
