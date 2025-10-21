"""
Voice service for ArtificialU.

This service manages voice selection and assignment for professors.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from artificial_u.config import get_settings
from artificial_u.integrations import elevenlabs
from artificial_u.models.core import Professor, Voice
from artificial_u.models.repositories import RepositoryFactory


class VoiceService:
    """Service for managing voice selection and assignment."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        client: Optional[elevenlabs.ElevenLabsClient] = None,
        logger=None,
    ):
        """
        Initialize the voice service.

        Args:
            repository_factory: Repository factory instance
            client: ElevenLabs client instance (optional)
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Initialize client and components
        self.repository_factory = repository_factory
        self.client = client or elevenlabs.ElevenLabsClient()
        self.mapper = elevenlabs.VoiceMapper(logger=self.logger)
        self.settings = get_settings()

    def _find_voices_in_db(self, attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Attempt to find matching voices in the database.

        First tries with strict matching on all attributes, then falls back to matching
        only on core attributes (gender, age, language) if no results are found.

        Args:
            attributes: Professor attributes for voice matching

        Returns:
            List of voice dictionaries
        """
        # Try strict matching first
        self.logger.debug(
            f"Strict matching filters: gender={attributes.get('gender')}, "
            f"accent={attributes.get('accent')}, age={attributes.get('age')}, "
            f"language={attributes.get('language', 'en')}, "
            f"use_case={attributes.get('use_case')}, category={attributes.get('category')}"
        )
        voices = self.repository_factory.voice.list(
            gender=attributes.get("gender"),
            accent=attributes.get("accent"),
            age=attributes.get("age"),
            language=attributes.get("language", "en"),
            use_case=attributes.get("use_case"),
            category=attributes.get("category"),
        )

        if voices:
            self.logger.info(f"Found {len(voices)} voices in database with strict matching")
            # Log the actual voices found for debugging
            for i, voice in enumerate(voices):
                self.logger.debug(
                    f"  Strict match {i+1}: {voice.name} "
                    f"(gender: {voice.gender}, age: {voice.age}, accent: {voice.accent})"
                )
            return [v.model_dump() for v in voices]

        # If no results, try more relaxed matching (omitting accent, use_case, category)
        self.logger.debug(
            f"Relaxed matching filters: gender={attributes.get('gender')}, "
            f"age={attributes.get('age')}, language={attributes.get('language')}"
        )
        voices = self.repository_factory.voice.list(
            gender=attributes.get("gender"),
            age=attributes.get("age"),
            language=attributes.get("language"),
        )

        if voices:
            self.logger.info(f"Found {len(voices)} voices in database with relaxed matching")
            # Log the actual voices found for debugging
            for i, voice in enumerate(voices):
                self.logger.debug(
                    f"  Relaxed match {i+1}: {voice.name} "
                    f"(gender: {voice.gender}, age: {voice.age}, accent: {voice.accent})"
                )
            return [v.model_dump() for v in voices]

        # If still no results, try with just gender and language (ignore age)
        self.logger.debug(
            f"Very relaxed matching filters: gender={attributes.get('gender')}, "
            f"language={attributes.get('language')} (ignoring age)"
        )
        voices = self.repository_factory.voice.list(
            gender=attributes.get("gender"),
            language=attributes.get("language"),
        )

        if voices:
            self.logger.info(
                f"Found {len(voices)} voices in database with very relaxed matching (ignoring age)"
            )
            # Log the actual voices found for debugging
            for i, voice in enumerate(voices):
                self.logger.debug(
                    f"  Very relaxed match {i+1}: {voice.name} "
                    f"(gender: {voice.gender}, age: {voice.age}, accent: {voice.accent})"
                )
            return [v.model_dump() for v in voices]

        return []

    def _get_used_voice_ids(self) -> List[str]:
        """
        Get a list of ElevenLabs voice IDs that are already assigned to professors.

        Returns:
            List of ElevenLabs voice IDs in use
        """
        # Get all professors with assigned voices
        professors = self.repository_factory.professor.list()

        used_voice_ids = []
        for professor in professors:
            if professor.voice_id:
                # Get the voice from database
                voice = self.repository_factory.voice.get(professor.voice_id)
                if voice and voice.el_voice_id:
                    used_voice_ids.append(voice.el_voice_id)

        self.logger.debug(f"Found {len(used_voice_ids)} unique voices in use")
        return used_voice_ids

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

        voices: List[Dict[str, Any]] = []
        required_model = getattr(self.settings, "TTS_VOICE_MODEL", None)

        # First, try to get premade voices if we haven't already
        premade_voices = self.client.get_premade_voices()
        voices.extend(
            self._filter_and_store_premade_voices(
                premade_voices,
                gender=gender,
                age=age,
                language=language,
                use_case=use_case,
                category=category,
                required_model=required_model,
            )
        )

        # Don't pass accent to shared voices API, use language instead
        # The shared voices API doesn't support 'accent' query param effectively
        voices_page, has_more = self.client.get_shared_voices(
            gender=gender,
            age=age,
            language=language,
            use_case=use_case,
            category=category,
        )
        if required_model:
            for v in voices_page:
                if self._voice_supports_model(v, required_model):
                    voices.append(v)
        else:
            voices.extend(voices_page)

        # Get additional pages if needed (limit to 3 pages)
        voices.extend(
            self._fetch_additional_shared_voice_pages(
                start_page=1,
                has_more=has_more,
                gender=gender,
                age=age,
                language=language,
                use_case=use_case,
                category=category,
                required_model=required_model,
            )
        )

        return voices

    def _ensure_language_population(self, language: str) -> None:
        """If our DB has very few voices for a target language, proactively fetch some.

        This helps non-English professors get matched to appropriate voices by
        warming the local catalog from the Shared Voices API.
        """
        try:
            existing_count = self.repository_factory.voice.count(language=language)
        except Exception:
            existing_count = 0

        # If almost empty (e.g., < 20), pull a few pages of shared voices for that language
        if existing_count < 20:
            self.logger.info(
                f"Language '{language}' under-populated in DB (count={existing_count}). "
                "Fetching additional shared voices."
            )
            page = 0
            pages_to_fetch = 3
            while page < pages_to_fetch:
                page_voices, has_more = self.client.get_shared_voices(
                    language=language,
                    page_size=100,
                    page=page,
                )
                for voice in page_voices:
                    self._save_voice_to_db(voice)
                if not has_more:
                    break
                page += 1

    def _filter_and_store_premade_voices(
        self,
        voices: List[Dict[str, Any]],
        *,
        gender: Optional[str],
        age: Optional[str],
        language: str,
        use_case: Optional[str],
        category: Optional[str],
        required_model: Optional[str],
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for voice in voices:
            if not self._voice_matches_filters(voice, gender, age, language, use_case, category):
                continue
            if required_model and not self._voice_supports_model(voice, required_model):
                continue
            results.append(voice)
            self._save_voice_to_db(voice)
        return results

    def _fetch_additional_shared_voice_pages(
        self,
        *,
        start_page: int,
        has_more: bool,
        gender: Optional[str],
        age: Optional[str],
        language: str,
        use_case: Optional[str],
        category: Optional[str],
        required_model: Optional[str],
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        page = start_page
        more_flag = has_more
        while more_flag and page < 3:
            more_voices, more_flag = self.client.get_shared_voices(
                gender=gender,
                age=age,
                language=language,
                use_case=use_case,
                category=category,
                page=page,
            )
            if required_model:
                for v in more_voices:
                    if self._voice_supports_model(v, required_model):
                        results.append(v)
            else:
                results.extend(more_voices)
            page += 1
        return results

    def _voice_matches_filters(
        self,
        voice: Dict[str, Any],
        gender: Optional[str],
        age: Optional[str],
        language: Optional[str],
        use_case: Optional[str],
        category: Optional[str],
    ) -> bool:
        """Return True if the voice matches the provided filters."""
        if gender and voice.get("gender") != gender:
            return False
        if age and voice.get("age") != age:
            return False
        if language and voice.get("language") != language:
            return False
        if use_case and voice.get("use_case") != use_case:
            return False
        if category and voice.get("category") != category:
            return False
        return True

    def _voice_supports_model(self, voice: Dict[str, Any], required_model: str) -> bool:
        """Return True if the voice 'verified_languages' includes the required model."""
        verified = voice.get("verified_languages") or []
        models = {x.get("model_id") for x in verified if isinstance(x, dict)}
        # If models set is empty, treat as unknown support and allow
        return not models or required_model in models

    def fetch_and_store_premade_voices(self) -> int:
        """
        Fetch and store premade voices from the v2/voices endpoint.

        Returns:
            Number of premade voices stored
        """
        self.logger.info("Fetching premade voices from v2/voices endpoint")

        try:
            # Get premade voices from the API
            premade_voices = self.client.get_premade_voices()

            # Filter for premade category only
            count = 0
            for voice_data in premade_voices:
                if voice_data.get("category") == "premade":
                    self._save_voice_to_db(voice_data)
                    count += 1

            self.logger.info(f"Stored {count} premade voices to database")
            return count

        except Exception as e:
            self.logger.error(f"Error fetching premade voices: {e}")
            return 0

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
        self.logger.warning("No voices found with initial criteria, relaxing constraints")
        voices = []

        # Try with just gender if available
        if attributes.get("gender"):
            db_voices = self.repository_factory.voice.list(
                gender=attributes.get("gender"), language="en"
            )
            if db_voices:
                return [v.model_dump() for v in db_voices]

            # If DB search with gender failed, try API with gender only
            voices = self._fetch_voices_from_api(gender=attributes.get("gender"), language="en")
            if voices:
                return voices

        # If still no voices, get any voices with language='en'
        db_voices = self.repository_factory.voice.list(language="en")
        if db_voices:
            return [v.model_dump() for v in db_voices]

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
        voice_db = self.repository_factory.voice.get_by_elevenlabs_id(selected_voice["el_voice_id"])

        if not voice_db:
            # Create a new voice record
            voice = Voice(
                el_voice_id=selected_voice["el_voice_id"],
                name=selected_voice["name"],
                gender=selected_voice.get("gender"),
                accent=selected_voice.get("accent"),
                age=selected_voice.get("age"),
                descriptive=selected_voice.get("descriptive"),
                use_case=selected_voice.get("use_case"),
                category=selected_voice.get("category"),
            )
            voice_db = self.repository_factory.voice.upsert(voice)

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
        self.logger.info(
            f"=== Starting voice selection for professor: "
            f"{professor.name} (ID: {professor.id}) ==="
        )
        self.logger.info(f"Selection strategy: {selection_strategy}")

        # Extract professor attributes for voice matching
        self.logger.debug("Step 1: Extracting professor attributes for voice matching")
        attributes = self.mapper.extract_profile_attributes(professor)
        self.logger.info(f"Extracted attributes: {attributes}")

        # Warm catalog for the professor's language if needed
        self._ensure_language_population(attributes.get("language", "en"))

        # Step 1: Try to find suitable voices in database
        self.logger.debug("Step 2: Searching for voices in database with extracted attributes")
        voices = self._find_voices_in_db(attributes)
        self.logger.info(f"Found {len(voices)} voices in database")

        # Step 2: If no voices found in DB, fetch from API
        if not voices:
            self.logger.debug("Step 3: No voices found in DB, fetching from ElevenLabs API")
            voices = self._fetch_voices_from_api(
                gender=attributes.get("gender"),
                accent=attributes.get("accent"),
                age=attributes.get("age"),
                language=attributes.get("language", "en"),
                category=attributes.get("category"),
            )
            self.logger.info(f"Fetched {len(voices)} voices from API")
        else:
            self.logger.debug("Step 3: Skipping API fetch - sufficient voices found in database")

        # Step 3: If still no voices, try with relaxed criteria
        if not voices:
            self.logger.debug(
                "Step 4: No voices found with strict criteria, trying relaxed criteria"
            )
            voices = self._find_voices_with_relaxed_criteria(attributes)
            self.logger.info(f"Found {len(voices)} voices with relaxed criteria")
        else:
            self.logger.debug("Step 4: Skipping relaxed criteria - sufficient voices found")

        # Step 4: Get already-used voice IDs to avoid reuse
        self.logger.debug("Step 5: Getting list of already-used voice IDs")
        used_voice_ids = self._get_used_voice_ids()
        self.logger.info(f"Found {len(used_voice_ids)} voices already in use")

        # Step 5: Rank the voices based on match criteria
        self.logger.debug("Step 6: Ranking voices based on match criteria")
        ranked_voices = self.mapper.rank_voices(voices, attributes, used_voice_ids)
        self.logger.info(f"Ranked {len(ranked_voices)} voices")

        # Step 6: Select voice using the specified strategy
        self.logger.debug(f"Step 7: Selecting voice using strategy: {selection_strategy}")
        selected_voice = self.mapper.select_voice(ranked_voices, selection_strategy)

        if not selected_voice:
            self.logger.error("No suitable voice found for professor after all selection steps")
            raise ValueError("No suitable voice found for professor")

        selected_name = selected_voice.get("name", "Unknown")
        selected_id = selected_voice.get("el_voice_id", "Unknown")
        self.logger.info(f"Selected voice: {selected_name} (ID: {selected_id})")

        # Step 7: Add the db voice record
        self.logger.debug("Step 8: Finding or creating database voice record")
        voice_db = self._find_or_create_db_voice(selected_voice)
        self.logger.info(f"Database voice record ID: {voice_db.id}")

        # Update professor's voice_id if professor has an id
        if professor.id:
            self.logger.debug(
                f"Step 9: Updating professor {professor.id} with voice ID {voice_db.id}"
            )
            self.repository_factory.professor.update_field(professor.id, voice_id=voice_db.id)
            self.logger.info(f"Updated professor {professor.id} with voice ID {voice_db.id}")
        else:
            # For new professors without IDs, update the object in memory
            self.logger.debug(
                f"Step 9: Assigning voice ID {voice_db.id} to new professor {professor.name}"
            )
            professor.voice_id = voice_db.id
            self.logger.info(f"Assigned voice ID {voice_db.id} to new professor {professor.name}")

        # Add database voice ID to the returned data
        selected_voice["db_voice_id"] = voice_db.id
        self.logger.info(f"=== Voice selection completed for professor: {professor.name} ===")
        return selected_voice

    def _convert_verified_languages(self, verified_languages_raw: Any) -> List[Dict[str, Any]]:
        """Convert ElevenLabs verified_languages data to serializable format."""
        verified_languages = []

        if isinstance(verified_languages_raw, list):
            for lang_obj in verified_languages_raw:
                try:
                    if hasattr(lang_obj, "model_dump"):
                        # Convert Pydantic model to dict
                        verified_languages.append(lang_obj.model_dump())
                    elif hasattr(lang_obj, "dict"):
                        # Fallback for older Pydantic versions
                        verified_languages.append(lang_obj.dict())
                    elif isinstance(lang_obj, dict):
                        # Already a dict
                        verified_languages.append(lang_obj)
                    else:
                        # Convert any other object to dict via its attributes
                        verified_languages.append(dict(lang_obj.__dict__))
                except Exception as e:
                    self.logger.warning(f"Failed to convert verified_languages item: {e}")
                    continue

        return verified_languages

    def _save_voice_to_db(self, el_voice_data: Dict[str, Any]) -> None:
        """Save a voice to the database."""

        # Convert popularity score
        popularity_score = el_voice_data.get("cloned_by_count", 0)
        if not popularity_score:
            popularity_score = el_voice_data.get("usage_character_count_1y", 0)

        # Convert verified_languages from ElevenLabs API format to serializable format
        verified_languages = self._convert_verified_languages(
            el_voice_data.get("verified_languages", [])
        )

        # Create Voice model
        voice = Voice(
            el_voice_id=el_voice_data["el_voice_id"],
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
            verified_languages=verified_languages,
            popularity_score=popularity_score,
            last_updated=datetime.now(),
        )

        # Upsert to database
        try:
            self.repository_factory.voice.upsert(voice)
        except Exception as e:
            self.logger.error(f"Error saving voice to database: {e}")

    def get_voice_by_id(self, voice_id: int) -> Optional[Dict[str, Any]]:
        """
        Get voice data by database voice ID.

        Args:
            voice_id: Database voice ID to look up

        Returns:
            Voice data dictionary or None if not found
        """
        db_voice = self.repository_factory.voice.get(voice_id)
        if db_voice:
            return db_voice.model_dump()
        return None

    def get_voice_by_el_id(self, el_voice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get voice data by ElevenLabs voice ID.

        Args:
            el_voice_id: ElevenLabs voice ID to look up

        Returns:
            Voice data dictionary or None if not found
        """
        # Try to get from database first
        db_voice = self.repository_factory.voice.get_by_elevenlabs_id(el_voice_id)
        if db_voice:
            return db_voice.model_dump()

        # Fall back to API
        el_voice_data = self.client.get_el_voice(el_voice_id)
        if not el_voice_data:
            return None

        # Save to database and return the DB-backed record with id
        try:
            self._save_voice_to_db(el_voice_data)
            persisted = self.repository_factory.voice.get_by_elevenlabs_id(el_voice_id)
            if persisted:
                return persisted.model_dump()
        except Exception as e:
            self.logger.error(f"Failed to persist voice {el_voice_id}: {e}")
            # As a fallback, return the API data (may not include id)
            return el_voice_data

        # If persistence unexpectedly failed without exception
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
        voice = self.repository_factory.voice.get_by_elevenlabs_id(el_voice_id)
        if not voice:
            voice = Voice(
                el_voice_id=el_voice_id,
                name=voice_data["name"],
            )
            self.repository_factory.voice.upsert(voice)

        # Update professor with voice ID
        self.repository_factory.professor.update_field(professor_id, voice_id=voice.id)

        self.logger.info(f"Manually assigned voice {el_voice_id} to professor {professor_id}")

    def list_available_voices(
        self,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        language: Optional[str] = None,
        use_case: Optional[str] = None,
        category: Optional[str] = None,
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
            limit: Maximum number of results (for DB/API pagination)
            offset: Offset for pagination

        Returns:
            List of voice dictionaries
        """
        # Try database first
        voices = self.repository_factory.voice.list(
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
            return [v.model_dump() for v in voices]

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

    def count_available_voices(
        self,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        language: Optional[str] = None,
        use_case: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """
        Count available voices with optional filtering.

        Args:
            gender: Optional filter by gender
            accent: Optional filter by accent
            age: Optional filter by age
            language: Optional filter by language
            use_case: Optional filter by use case
            category: Optional filter by category

        Returns:
            Total count of matching voices in the database.
        """
        # This primarily counts from the database.
        # If the expectation is to count from API if DB is empty, logic would need to be added,
        # but for typical pagination, counting existing DB entries is standard.
        return self.repository_factory.voice.count(
            gender=gender,
            accent=accent,
            age=age,
            language=language,
            use_case=use_case,
            category=category,
        )
