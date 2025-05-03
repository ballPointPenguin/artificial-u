"""
Voice service for ArtificialU.

This service manages voice selection and assignment for professors.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper
from artificial_u.models.core import Professor, Voice
from artificial_u.models.repositories import RepositoryFactory


class VoiceService:
    """Service for managing voice selection and assignment."""

    def __init__(
        self,
        api_key: str,
        client: ElevenLabsClient,
        mapper: VoiceMapper,
        repository: RepositoryFactory,
        logger=None,
    ):
        """
        Initialize the voice service.

        Args:
            api_key: ElevenLabs API key
            client: ElevenLabs client instance
            mapper: voice mapper instance
            repository: database repository instance
            logger: logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Initialize client and components
        self.client = client or ElevenLabsClient(api_key=api_key)
        self.mapper = mapper or VoiceMapper(logger=self.logger)
        self.repository = repository

    def _find_voices_in_db(self, attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Attempt to find matching voices in the database.

        Args:
            attributes: Professor attributes for voice matching

        Returns:
            List of voice dictionaries
        """
        voices = self.repository.list_voices(
            gender=attributes.get("gender"),
            accent=attributes.get("accent"),
            age=attributes.get("age"),
            language=attributes.get("language", "en"),
            use_case=attributes.get("use_case"),
            category=attributes.get("category"),
        )

        if voices:
            self.logger.info(f"Found {len(voices)} voices in database")
            return [v.dict() for v in voices]

        return []

    def _fetch_voices_from_api(
        self,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        language: str = "en",
        use_case: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch voices from ElevenLabs API.

        Args:
            gender: Optional filter by gender
            accent: Optional filter by accent
            age: Optional filter by age
            language: Language filter (default: 'en')
            use_case: Optional filter by use case
            category: Optional filter by category

        Returns:
            List of voice dictionaries from API
        """
        self.logger.info("Fetching voices from API for selection")

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

        # Get additional pages if needed (limit to 3 pages)
        page = 1
        while has_more and page < 3:
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

        # Save to database
        for voice_data in voices:
            self._save_voice_to_db(voice_data)

        return voices

    def _find_voices_with_relaxed_criteria(
        self, attributes: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find voices with relaxed search criteria when strict criteria yield no results.

        Args:
            attributes: Professor attributes for voice matching

        Returns:
            List of voice dictionaries
        """
        self.logger.warning(
            "No voices found with initial criteria, relaxing constraints"
        )
        voices = []

        # Try with just gender if available
        if attributes.get("gender"):
            db_voices = self.repository.list_voices(
                gender=attributes.get("gender"), language="en"
            )
            if db_voices:
                return [v.dict() for v in db_voices]

            # If DB search with gender failed, try API with gender only
            voices = self._fetch_voices_from_api(
                gender=attributes.get("gender"), language="en"
            )
            if voices:
                return voices

        # If still no voices, get any voices with language='en'
        db_voices = self.repository.list_voices(language="en")
        if db_voices:
            return [v.dict() for v in db_voices]

        # Last resort: get any English voices from API
        return self._fetch_voices_from_api(language="en")

    def _find_or_create_db_voice(self, selected_voice: Dict[str, Any]) -> Voice:
        """
        Find or create a voice record in the database.

        Args:
            selected_voice: Selected voice data

        Returns:
            Voice database record
        """
        voice_db = self.repository.get_voice_by_elevenlabs_id(
            selected_voice["voice_id"]
        )

        if not voice_db:
            # Create a new voice record
            voice = Voice(
                el_voice_id=selected_voice["voice_id"],
                name=selected_voice["name"],
                gender=selected_voice.get("gender"),
                accent=selected_voice.get("accent"),
                age=selected_voice.get("age"),
                descriptive=selected_voice.get("descriptive"),
                use_case=selected_voice.get("use_case"),
                category=selected_voice.get("category"),
            )
            voice_db = self.repository.upsert_voice(voice)

        return voice_db

    def select_voice_for_professor(
        self,
        professor: Professor,
        selection_strategy: str = "top_random",
    ) -> Dict[str, Any]:
        """
        Select an appropriate voice for a professor and update the professor record.

        Args:
            professor: Professor for whom to select voice
            selection_strategy: Strategy for voice selection ('top', 'top_random', 'weighted')

        Returns:
            Selected voice data including both el_voice_id and db voice record id
        """
        # Extract professor attributes for voice matching
        attributes = self.mapper.extract_profile_attributes(professor)

        # Step 1: Try to find suitable voices
        voices = self._find_voices_in_db(attributes)

        # Step 2: If no voices found in DB, fetch from API
        if not voices:
            voices = self._fetch_voices_from_api(
                gender=attributes.get("gender"),
                accent=attributes.get("accent"),
                age=attributes.get("age"),
                language=attributes.get("language", "en"),
                use_case=attributes.get("use_case"),
                category=attributes.get("category"),
            )

        # Step 3: If still no voices, try with relaxed criteria
        if not voices:
            voices = self._find_voices_with_relaxed_criteria(attributes)

        # Step 4: Rank the voices based on match criteria
        ranked_voices = self.mapper.rank_voices(voices, attributes)

        # Step 5: Select voice using the specified strategy
        selected_voice = self.mapper.select_voice(ranked_voices, selection_strategy)

        if not selected_voice:
            raise ValueError("No suitable voice found for professor")

        # Step 6: Add the db voice record
        voice_db = self._find_or_create_db_voice(selected_voice)

        # Update the selected_voice with the db id
        selected_voice["db_voice_id"] = voice_db.id

        # Update professor's voice_id if professor has an id
        if professor.id:
            self.repository.update_professor_field(professor.id, voice_id=voice_db.id)
            self.logger.info(
                f"Updated professor {professor.id} with voice ID {voice_db.id}"
            )

        return selected_voice

    def _save_voice_to_db(self, el_voice_data: Dict[str, Any]) -> None:
        """Save a voice to the database."""

        # Convert popularity score
        popularity_score = el_voice_data.get("cloned_by_count", 0)
        if not popularity_score:
            popularity_score = el_voice_data.get("usage_character_count_1y", 0)

        # Create Voice model
        voice = Voice(
            el_voice_id=el_voice_data["voice_id"],
            name=el_voice_data["name"],
            accent=el_voice_data.get("accent"),
            gender=el_voice_data.get("gender"),
            age=el_voice_data.get("age"),
            descriptive=el_voice_data.get("descriptive"),
            use_case=el_voice_data.get("use_case"),
            category=el_voice_data.get("category"),
            language=el_voice_data.get("language"),
            locale=el_voice_data.get("locale"),
            description=el_voice_data.get("description"),
            preview_url=el_voice_data.get("preview_url"),
            verified_languages=el_voice_data.get("verified_languages", {}),
            popularity_score=popularity_score,
            last_updated=datetime.now(),
        )

        # Upsert to database
        try:
            self.repository.upsert_voice(voice)
        except Exception as e:
            self.logger.error(f"Error saving voice to database: {e}")

    def get_voice_by_el_id(
        self, el_voice_id: str, refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get voice data by ElevenLabs voice ID.

        Args:
            el_voice_id: ElevenLabs voice ID to look up
            refresh: Whether to force refresh from API

        Returns:
            Voice data dictionary or None if not found
        """
        # Try to get from database first
        db_voice = self.repository.get_voice_by_elevenlabs_id(el_voice_id)
        if db_voice:
            return db_voice.dict()

        # Fall back to API
        el_voice_data = self.client.get_el_voice(el_voice_id)
        if el_voice_data:
            # Save to database
            self._save_voice_to_db(el_voice_data)

        return el_voice_data

    def manual_voice_assignment(self, professor_id: str, el_voice_id: str) -> None:
        """
        Manually assign a voice to a professor.

        Args:
            professor_id: ID of the professor to assign voice to
            el_voice_id: ID of the voice to assign
        """
        # Verify voice exists
        voice_data = self.get_voice_by_el_id(el_voice_id)
        if not voice_data:
            raise ValueError(f"Voice with ID {el_voice_id} not found")

        # Find or Create DB Voice record with el_voice_id
        voice = self.repository.get_voice_by_elevenlabs_id(el_voice_id)
        if not voice:
            voice = Voice(
                el_voice_id=el_voice_id,
                name=voice_data["name"],
            )
            self.repository.upsert_voice(voice)

        # Update professor with voice ID
        self.repository.update_professor_field(professor_id, voice_id=voice.id)

        self.logger.info(
            f"Manually assigned voice {el_voice_id} to professor {professor_id}"
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
        # Try database first
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

        # Save to database
        for voice in voices_page:
            self._save_voice_to_db(voice)

        return voices_page
