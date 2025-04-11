"""
Voice service for ArtificialU.

This service manages voice selection and assignment for professors.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from artificial_u.models.core import Professor, Voice
from artificial_u.models.database import Repository
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
        repository: Optional[Repository] = None,
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
            repository: Optional database repository instance
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Initialize client and components
        self.client = client or ElevenLabsClient(api_key=api_key)
        self.mapper = mapper or VoiceMapper(logger=self.logger)
        self.cache = cache or VoiceCache(cache_dir=cache_dir, logger=self.logger)
        self.repository = repository

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
                # Try to get voice from database first
                if self.repository:
                    db_voice = self.repository.get_voice_by_elevenlabs_id(voice_id)
                    if db_voice:
                        self.logger.info(
                            f"Using database voice for professor {professor.id}"
                        )
                        return db_voice.dict()

                # Fall back to cache if not in database or no repository
                voice_data = self.cache.get_voice(voice_id)
                if voice_data:
                    self.logger.info(
                        f"Using cached voice mapping for professor {professor.id}"
                    )
                    return voice_data

                # If not in cache, try to get from API
                voice_data = self.client.get_voice(voice_id)
                if voice_data:
                    self.logger.info(
                        f"Retrieved voice for existing mapping: {voice_id}"
                    )
                    self.cache.set_voice(voice_id, voice_data)

                    # Save to database if repository available
                    if self.repository:
                        self._save_voice_to_db(voice_data)

                    return voice_data

        # Extract professor attributes for voice matching
        attributes = self.mapper.extract_profile_attributes(
            professor, additional_context
        )

        # Check if we can find voices in the database first
        voices = []
        if self.repository:
            voices = self.repository.list_voices(
                gender=attributes.get("gender"),
                accent=attributes.get("accent"),
                age=attributes.get("age"),
                language=attributes.get("language", "en"),
                use_case=attributes.get("use_case"),
                category=attributes.get("category"),
            )

            if voices:
                # Convert to dict format for compatibility
                voices = [v.dict() for v in voices]
                self.logger.info(f"Found {len(voices)} voices in database")

        # If no voices in DB or we want to refresh, check the cache
        if not voices or refresh_cache:
            # Check for cached voices matching these criteria
            criteria_key = self.cache.build_criteria_key(**attributes)
            cached_voices = self.cache.get_voices_by_criteria(criteria_key)

            if cached_voices and not refresh_cache:
                voices = cached_voices
                self.logger.info(f"Using {len(voices)} voices from cache")

        # If still no voices or refresh requested, get voices from API
        if not voices or refresh_cache:
            # Get voices from API
            self.logger.info("Fetching voices from API for selection")
            gender = attributes.get("gender")
            accent = attributes.get("accent")
            age = attributes.get("age")
            language = attributes.get("language", "en")
            use_case = attributes.get("use_case")
            category = attributes.get("category")

            # Get first page of results
            voices_page, has_more = self.client.get_shared_voices(
                gender=gender,
                accent=accent,
                age=age,
                language=language,
                use_case=use_case,
                category=category,
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
                    category=category,
                    page=page,
                )
                voices.extend(more_voices)
                page += 1

            # Cache the results
            self.cache.set_voices_by_criteria(criteria_key, voices)

            # Save to database if repository available
            if self.repository:
                for voice_data in voices:
                    self._save_voice_to_db(voice_data)

        # If still no voices found, try with less restrictive criteria
        if not voices:
            self.logger.warning(
                "No voices found with initial criteria, relaxing constraints"
            )

            # Try with just gender
            if attributes.get("gender"):
                # First try database
                if self.repository:
                    db_voices = self.repository.list_voices(
                        gender=attributes.get("gender"), language="en"
                    )
                    if db_voices:
                        voices = [v.dict() for v in db_voices]

                # If not in database, try cache
                if not voices:
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

                        # Save to database
                        if self.repository:
                            for voice_data in voices:
                                self._save_voice_to_db(voice_data)

            # If still no voices, get any voices
            if not voices:
                self.logger.warning("No voices found with gender, getting any voices")

                # Try database first
                if self.repository:
                    db_voices = self.repository.list_voices(language="en")
                    if db_voices:
                        voices = [v.dict() for v in db_voices]

                # If still no voices, try API
                if not voices:
                    voices_page, _ = self.client.get_shared_voices(language="en")
                    voices = voices_page
                    self.cache.set_voices_by_criteria("voices_language_en", voices)

                    # Save to database
                    if self.repository:
                        for voice_data in voices:
                            self._save_voice_to_db(voice_data)

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

    def _save_voice_to_db(self, voice_data: Dict[str, Any]) -> None:
        """Save a voice to the database."""
        if not self.repository:
            return

        # Convert popularity score
        popularity_score = voice_data.get("cloned_by_count", 0)
        if not popularity_score:
            popularity_score = voice_data.get("usage_character_count_1y", 0)

        # Create Voice model
        voice = Voice(
            voice_id=voice_data["voice_id"],
            name=voice_data["name"],
            accent=voice_data.get("accent"),
            gender=voice_data.get("gender"),
            age=voice_data.get("age"),
            descriptive=voice_data.get("descriptive"),
            use_case=voice_data.get("use_case"),
            category=voice_data.get("category"),
            language=voice_data.get("language"),
            locale=voice_data.get("locale"),
            description=voice_data.get("description"),
            preview_url=voice_data.get("preview_url"),
            verified_languages=voice_data.get("verified_languages", {}),
            popularity_score=popularity_score,
            last_updated=datetime.now(),
        )

        # Upsert to database
        try:
            self.repository.upsert_voice(voice)
        except Exception as e:
            self.logger.error(f"Error saving voice to database: {e}")

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
            voice_id: Voice ID to look up
            refresh: Whether to force refresh from API

        Returns:
            Voice data dictionary or None if not found
        """
        # Try to get from database first if repository is available
        if self.repository and not refresh:
            db_voice = self.repository.get_voice_by_elevenlabs_id(voice_id)
            if db_voice:
                return db_voice.dict()

        # Try cache next
        if not refresh:
            voice_data = self.cache.get_voice(voice_id)
            if voice_data:
                return voice_data

        # Fall back to API
        voice_data = self.client.get_voice(voice_id)
        if voice_data:
            self.cache.set_voice(voice_id, voice_data)

            # Save to database if repository available
            if self.repository:
                self._save_voice_to_db(voice_data)

        return voice_data

    def rebuild_voice_cache(self) -> Dict[str, Any]:
        """
        Rebuild the voice cache from ElevenLabs API.

        Returns:
            Dictionary with rebuild statistics
        """
        self.logger.info("Rebuilding voice cache...")

        # Clear existing cache
        self.cache.clear_voice_cache()

        # Get shared voices
        voice_data = []

        # Get English voices
        page = 0
        has_more = True
        while has_more and page < 5:  # Limit to 5 pages
            voices_page, has_more = self.client.get_shared_voices(
                language="en", page=page, page_size=100
            )
            voice_data.extend(voices_page)
            page += 1

        # Get Hindi voices
        page = 0
        has_more = True
        while has_more and page < 2:  # Limit to 2 pages
            voices_page, has_more = self.client.get_shared_voices(
                language="hi", page=page, page_size=100
            )
            voice_data.extend(voices_page)
            page += 1

        # Get Spanish voices
        page = 0
        has_more = True
        while has_more and page < 2:  # Limit to 2 pages
            voices_page, has_more = self.client.get_shared_voices(
                language="es", page=page, page_size=100
            )
            voice_data.extend(voices_page)
            page += 1

        # Cache the raw data
        self.cache.rebuild_cache(voice_data)

        # Save to database if repository available
        if self.repository:
            for voice in voice_data:
                self._save_voice_to_db(voice)

        return {
            "voices_cached": len(voice_data),
            "timestamp": datetime.now().isoformat(),
        }

    def manual_voice_assignment(self, professor_id: str, voice_id: str) -> None:
        """
        Manually assign a voice to a professor.

        Args:
            professor_id: ID of the professor to assign voice to
            voice_id: ID of the voice to assign
        """
        # Verify voice exists
        voice_data = self.get_voice_by_id(voice_id)
        if not voice_data:
            raise ValueError(f"Voice with ID {voice_id} not found")

        # Save mapping
        self.cache.set_professor_voice_mapping(professor_id, voice_id)
        self.logger.info(
            f"Manually assigned voice {voice_id} to professor {professor_id}"
        )

    def list_available_voices(
        self,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        language: Optional[str] = "en",
        use_case: Optional[str] = None,
        category: Optional[str] = None,
        refresh: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List available voices with optional filtering.

        Args:
            gender: Optional filter by gender
            accent: Optional filter by accent
            age: Optional filter by age
            language: Optional filter by language (default: 'en')
            use_case: Optional filter by use case
            category: Optional filter by category
            refresh: Whether to force refresh from API
            limit: Maximum number of results (for DB/API pagination)
            offset: Offset for pagination

        Returns:
            List of voice dictionaries
        """
        # Try database first if repository is available
        if self.repository and not refresh:
            voices = self.repository.list_voices(
                gender=gender,
                accent=accent,
                age=age,
                language=language,
                use_case=use_case,
                category=category,
                limit=limit,
                offset=offset,
            )

            if voices:
                return [v.dict() for v in voices]

        # Build cache key for the criteria
        criteria = {
            "gender": gender,
            "accent": accent,
            "age": age,
            "language": language or "en",
            "use_case": use_case,
            "category": category,
        }
        criteria_key = self.cache.build_criteria_key(
            **{k: v for k, v in criteria.items() if v}
        )

        # Try cache next if not refreshing
        if not refresh:
            voices = self.cache.get_voices_by_criteria(criteria_key)
            if voices:
                # Apply pagination manually for cached results
                paginated = (
                    voices[offset : offset + limit] if offset < len(voices) else []
                )
                return paginated

        # Get from API
        voices_page, _ = self.client.get_shared_voices(
            gender=gender,
            accent=accent,
            age=age,
            language=language or "en",
            use_case=use_case,
            category=category,
            page_size=limit,
            page=offset // limit if limit > 0 else 0,
        )

        # Cache the results
        self.cache.set_voices_by_criteria(criteria_key, voices_page)

        # Save to database if repository available
        if self.repository:
            for voice in voices_page:
                self._save_voice_to_db(voice)

        return voices_page

    def set_repository(self, repository: Repository) -> None:
        """
        Set the database repository.

        Args:
            repository: Repository instance to use
        """
        self.repository = repository
