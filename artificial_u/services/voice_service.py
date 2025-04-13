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
        api_key: Optional[str] = None,
        client: Optional[ElevenLabsClient] = None,
        mapper: Optional[VoiceMapper] = None,
        repository: Optional[RepositoryFactory] = None,
        logger=None,
    ):
        """
        Initialize the voice service.

        Args:
            api_key: Optional ElevenLabs API key
            client: Optional ElevenLabs client instance
            mapper: Optional voice mapper instance
            repository: Optional database repository instance
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Initialize client and components
        self.client = client or ElevenLabsClient(api_key=api_key)
        self.mapper = mapper or VoiceMapper(logger=self.logger)
        self.repository = repository

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

        # If still no voices or refresh requested, get voices from API
        if not voices:
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

        # Add the db voice record if we have a repository
        if self.repository:
            # Find or create the voice record in db
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

            # Update the selected_voice with the db id
            selected_voice["db_voice_id"] = voice_db.id

            if professor.id:
                self.repository.update_professor_field(
                    professor.id, voice_id=voice_db.id
                )
                self.logger.info(
                    f"Updated professor {professor.id} with voice ID {voice_db.id}"
                )

        return selected_voice

    def _save_voice_to_db(self, el_voice_data: Dict[str, Any]) -> None:
        """Save a voice to the database."""
        if not self.repository:
            return

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
        # Try to get from database first if repository is available
        if self.repository and not refresh:
            db_voice = self.repository.get_voice_by_elevenlabs_id(el_voice_id)
            if db_voice:
                return db_voice.dict()

        # Fall back to API
        el_voice_data = self.client.get_el_voice(el_voice_id)
        if el_voice_data:
            # Save to database if repository available
            if self.repository:
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

        # Save to database if repository available
        if self.repository:
            for voice in voices_page:
                self._save_voice_to_db(voice)

        return voices_page

    def set_repository(self, repository: RepositoryFactory) -> None:
        """
        Set the database repository.

        Args:
            repository: Repository instance to use
        """
        self.repository = repository
