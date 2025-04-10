"""
Voice service for ArtificialU.

This service manages voice selection and assignment for professors.
"""

import logging
from typing import Dict, List, Optional, Any

from artificial_u.models.core import Professor
from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper
from artificial_u.integrations.elevenlabs.cache import VoiceCache


class VoiceService:
    """Service for managing voice selection and assignment."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: Optional[str] = None,
        client: Optional[ElevenLabsClient] = None,
        mapper: Optional[VoiceMapper] = None,
        cache: Optional[VoiceCache] = None,
        logger=None,
    ):
        """
        Initialize the voice service.

        Args:
            api_key: Optional ElevenLabs API key
            cache_dir: Optional directory for voice cache
            client: Optional ElevenLabs client instance
            mapper: Optional voice mapper instance
            cache: Optional voice cache instance
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Initialize client and components
        self.client = client or ElevenLabsClient(api_key=api_key)
        self.mapper = mapper or VoiceMapper(logger=self.logger)
        self.cache = cache or VoiceCache(cache_dir=cache_dir, logger=self.logger)

    def select_voice_for_professor(
        self,
        professor: Professor,
        refresh_cache: bool = False,
        additional_context: Optional[Dict[str, Any]] = None,
        selection_strategy: str = "top_random",
    ) -> Dict[str, Any]:
        """
        Select an appropriate voice for a professor.

        Args:
            professor: Professor to select voice for
            refresh_cache: Whether to refresh the voice cache
            additional_context: Optional additional context for voice selection
            selection_strategy: Strategy for voice selection ('top', 'top_random', 'weighted')

        Returns:
            Selected voice data
        """
        # Check if professor already has a voice mapping in cache
        if professor.id and not refresh_cache:
            voice_id = self.cache.get_professor_voice_mapping(professor.id)
            if voice_id:
                # Verify the voice still exists and get its data
                voice_data = self.cache.get_voice(voice_id)
                if voice_data:
                    self.logger.info(
                        f"Using cached voice mapping for professor {professor.id}"
                    )
                    return voice_data

                voice_data = self.client.get_voice(voice_id)
                if voice_data:
                    self.logger.info(
                        f"Retrieved voice for existing mapping: {voice_id}"
                    )
                    self.cache.set_voice(voice_id, voice_data)
                    return voice_data

        # Extract professor attributes for voice matching
        attributes = self.mapper.extract_profile_attributes(
            professor, additional_context
        )

        # Check for cached voices matching these criteria
        criteria_key = self.cache.build_criteria_key(**attributes)
        voices = self.cache.get_voices_by_criteria(criteria_key)

        # If no cache or refresh requested, get voices from API
        if not voices or refresh_cache:
            # Get voices from API
            self.logger.info("Fetching voices from API for selection")
            gender = attributes.get("gender")
            accent = attributes.get("accent")
            age = attributes.get("age")
            language = attributes.get("language", "en")
            use_case = attributes.get("use_case")

            # Get first page of results
            voices_page, has_more = self.client.get_shared_voices(
                gender=gender,
                accent=accent,
                age=age,
                language=language,
                use_case=use_case,
            )
            voices = voices_page

            # Get additional pages if needed
            page = 1
            while (
                has_more and page < 3
            ):  # Limit to 3 pages to avoid excessive API calls
                more_voices, has_more = self.client.get_shared_voices(
                    gender=gender,
                    accent=accent,
                    age=age,
                    language=language,
                    use_case=use_case,
                    page=page,
                )
                voices.extend(more_voices)
                page += 1

            # Cache the results
            self.cache.set_voices_by_criteria(criteria_key, voices)

        # If still no voices found, try with less restrictive criteria
        if not voices:
            self.logger.warning(
                "No voices found with initial criteria, relaxing constraints"
            )

            # Try with just gender
            if attributes.get("gender"):
                relax_criteria = {"gender": attributes["gender"], "language": "en"}
                relax_key = self.cache.build_criteria_key(**relax_criteria)
                voices = self.cache.get_voices_by_criteria(relax_key)

                # If not in cache, fetch from API
                if not voices:
                    voices_page, _ = self.client.get_shared_voices(
                        gender=attributes["gender"], language="en"
                    )
                    voices = voices_page
                    self.cache.set_voices_by_criteria(relax_key, voices)

            # If still no voices, get any voices
            if not voices:
                self.logger.warning("No voices found with gender, getting any voices")
                voices_page, _ = self.client.get_shared_voices(language="en")
                voices = voices_page
                self.cache.set_voices_by_criteria("voices_language_en", voices)

        # Rank the voices based on match criteria
        ranked_voices = self.mapper.rank_voices(voices, attributes)

        # Select voice using the specified strategy
        selected_voice = self.mapper.select_voice(ranked_voices, selection_strategy)

        if not selected_voice:
            raise ValueError("No suitable voice found for professor")

        # Save mapping for future queries
        if professor.id:
            self.cache.set_professor_voice_mapping(
                professor.id, selected_voice["voice_id"]
            )

        return selected_voice

    def get_voice_id_for_professor(
        self, professor: Professor, additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get the voice ID for a professor.

        Args:
            professor: Professor to get voice for
            additional_context: Optional additional context for voice selection

        Returns:
            Voice ID string
        """
        voice = self.select_voice_for_professor(
            professor, additional_context=additional_context
        )
        return voice["voice_id"]

    def get_voice_by_id(
        self, voice_id: str, refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get voice data by ID.

        Args:
            voice_id: Voice ID to retrieve
            refresh: Whether to refresh from API

        Returns:
            Voice data or None if not found
        """
        # Check cache first
        if not refresh:
            voice_data = self.cache.get_voice(voice_id)
            if voice_data:
                return voice_data

        # Get from API
        voice_data = self.client.get_voice(voice_id)

        # Cache the result if found
        if voice_data:
            self.cache.set_voice(voice_id, voice_data)

        return voice_data

    def rebuild_voice_cache(self) -> Dict[str, Any]:
        """
        Rebuild the voice cache with fresh data from API.

        Returns:
            Dictionary with status information
        """
        self.logger.info("Rebuilding voice cache")

        # Get voices from API
        all_voices = []

        # Get voices for different genders to ensure better coverage
        for gender in ["male", "female", "neutral"]:
            voices_page, has_more = self.client.get_shared_voices(gender=gender)
            all_voices.extend(voices_page)

            # Get additional pages if available
            page = 1
            while has_more and page < 3:  # Limit to 3 pages
                more_voices, has_more = self.client.get_shared_voices(
                    gender=gender, page=page
                )
                all_voices.extend(more_voices)
                page += 1

        # Also get some featured voices
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
            voice_data = self.client.get_voice(voice_id)
            if voice_data:
                all_voices.append(voice_data)

        # Rebuild cache with collected voices
        result = self.cache.rebuild_cache(all_voices)

        return result

    def manual_voice_assignment(self, professor_id: str, voice_id: str) -> None:
        """
        Manually assign a voice to a professor.

        Args:
            professor_id: ID of the professor
            voice_id: ID of the voice to assign
        """
        # Verify the voice exists
        voice_data = self.get_voice_by_id(voice_id)
        if not voice_data:
            raise ValueError(f"Voice ID {voice_id} not found")

        # Set the mapping
        self.cache.set_professor_voice_mapping(professor_id, voice_id)

        self.logger.info(
            f"Manually assigned voice {voice_id} to professor {professor_id}"
        )

    def list_available_voices(
        self,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List available voices with optional filtering.

        Args:
            gender: Optional gender filter
            accent: Optional accent filter
            age: Optional age filter
            refresh: Whether to refresh from API

        Returns:
            List of matching voices
        """
        # Build criteria key for cache lookup
        criteria = {}
        if gender:
            criteria["gender"] = gender
        if accent:
            criteria["accent"] = accent
        if age:
            criteria["age"] = age
        criteria["language"] = "en"  # Default to English

        criteria_key = self.cache.build_criteria_key(**criteria)

        # Check cache first if not refreshing
        if not refresh:
            voices = self.cache.get_voices_by_criteria(criteria_key)
            if voices:
                return voices

        # Get from API
        voices_page, has_more = self.client.get_shared_voices(
            gender=gender, accent=accent, age=age, language="en"
        )
        voices = voices_page

        # Get additional pages if needed
        page = 1
        while has_more and page < 3:  # Limit to 3 pages
            more_voices, has_more = self.client.get_shared_voices(
                gender=gender, accent=accent, age=age, language="en", page=page
            )
            voices.extend(more_voices)
            page += 1

        # Cache the results
        self.cache.set_voices_by_criteria(criteria_key, voices)

        return voices
