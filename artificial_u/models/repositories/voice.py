"""
Voice repository for database operations.
"""

from datetime import datetime
from typing import List, Optional

from artificial_u.models.core import Voice
from artificial_u.models.database import VoiceModel
from artificial_u.models.repositories.base import BaseRepository


class VoiceRepository(BaseRepository):
    """Repository for Voice operations."""

    def _to_domain(self, db_voice: VoiceModel) -> Voice:
        """Convert a database model to a domain Voice object."""
        return Voice(
            id=db_voice.id,
            tts_backend=db_voice.tts_backend or "elevenlabs",
            external_id=db_voice.external_id,
            el_voice_id=db_voice.el_voice_id,
            name=db_voice.name,
            accent=db_voice.accent,
            age=db_voice.age,
            category=db_voice.category,
            description=db_voice.description,
            descriptive=db_voice.descriptive,
            gender=db_voice.gender,
            language=db_voice.language,
            locale=db_voice.locale,
            popularity_score=db_voice.popularity_score,
            preview_url=db_voice.preview_url,
            use_case=db_voice.use_case,
            verified_languages=db_voice.verified_languages or [],
            last_updated=db_voice.last_updated,
        )

    def create(self, voice: Voice) -> Voice:
        """Create a new voice record."""
        with self.get_session() as session:
            db_voice = VoiceModel(
                tts_backend=voice.tts_backend or "elevenlabs",
                external_id=voice.external_id,
                el_voice_id=voice.el_voice_id,
                name=voice.name,
                accent=voice.accent,
                age=voice.age,
                category=voice.category,
                description=voice.description,
                descriptive=voice.descriptive,
                gender=voice.gender,
                language=voice.language,
                locale=voice.locale,
                popularity_score=voice.popularity_score,
                preview_url=voice.preview_url,
                use_case=voice.use_case,
                verified_languages=voice.verified_languages,
                last_updated=datetime.now(),
            )

            session.add(db_voice)
            session.commit()
            session.refresh(db_voice)

            voice.id = db_voice.id
            return voice

    def get(self, voice_id: int) -> Optional[Voice]:
        """Get a voice by ID."""
        with self.get_session() as session:
            db_voice = session.query(VoiceModel).filter_by(id=voice_id).first()

            if not db_voice:
                return None

            return self._to_domain(db_voice)

    def get_by_elevenlabs_id(self, elevenlabs_id: str) -> Optional[Voice]:
        """Get a voice by ElevenLabs voice ID."""
        with self.get_session() as session:
            db_voice = session.query(VoiceModel).filter_by(el_voice_id=elevenlabs_id).first()

            if not db_voice:
                return None

            return self._to_domain(db_voice)

    def get_by_external_id(self, backend: str, external_id: str) -> Optional[Voice]:
        """Get a voice by TTS backend and external ID."""
        with self.get_session() as session:
            db_voice = (
                session.query(VoiceModel)
                .filter_by(tts_backend=backend, external_id=external_id)
                .first()
            )

            if not db_voice:
                return None

            return self._to_domain(db_voice)

    def list(
        self,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        language: Optional[str] = None,
        use_case: Optional[str] = None,
        tts_backend: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Voice]:
        """List voices with optional filters."""
        with self.get_session() as session:
            query = session.query(VoiceModel)

            # Apply filters - use exact matching instead of substring matching
            if accent:
                query = query.filter(VoiceModel.accent.ilike(accent))
            if age:
                query = query.filter(VoiceModel.age.ilike(age))
            if category:
                query = query.filter(VoiceModel.category.ilike(category))
            if gender:
                query = query.filter(VoiceModel.gender.ilike(gender))
            if language:
                query = query.filter(VoiceModel.language.ilike(language))
            if use_case:
                query = query.filter(VoiceModel.use_case.ilike(use_case))
            if tts_backend:
                query = query.filter(VoiceModel.tts_backend == tts_backend)

            # Apply pagination
            voices = (
                query.order_by(VoiceModel.popularity_score.desc()).limit(limit).offset(offset).all()
            )

            return [self._to_domain(v) for v in voices]

    def update(self, voice: Voice) -> Voice:
        """Update an existing voice."""
        with self.get_session() as session:
            db_voice = session.query(VoiceModel).filter_by(id=voice.id).first()

            if not db_voice:
                raise ValueError(f"Voice with ID {voice.id} not found")

            db_voice.tts_backend = voice.tts_backend or db_voice.tts_backend
            db_voice.external_id = voice.external_id
            db_voice.el_voice_id = voice.el_voice_id
            db_voice.name = voice.name
            db_voice.accent = voice.accent
            db_voice.age = voice.age
            db_voice.category = voice.category
            db_voice.description = voice.description
            db_voice.descriptive = voice.descriptive
            db_voice.gender = voice.gender
            db_voice.language = voice.language
            db_voice.locale = voice.locale
            db_voice.popularity_score = voice.popularity_score
            db_voice.preview_url = voice.preview_url
            db_voice.use_case = voice.use_case
            db_voice.verified_languages = voice.verified_languages
            db_voice.last_updated = datetime.now()

            session.commit()
            return voice

    def upsert(self, voice: Voice) -> Voice:
        """Create or update a voice based on its identity.

        For ElevenLabs voices: looks up by el_voice_id.
        For other backends: looks up by (tts_backend, external_id).
        """
        existing_voice = None

        # Try ElevenLabs lookup first (backward compatibility)
        if voice.el_voice_id:
            existing_voice = self.get_by_elevenlabs_id(voice.el_voice_id)

        # Try backend + external_id lookup for non-EL voices
        if not existing_voice and voice.external_id and voice.tts_backend:
            existing_voice = self.get_by_external_id(voice.tts_backend, voice.external_id)

        if existing_voice:
            voice.id = existing_voice.id
            return self.update(voice)
        return self.create(voice)

    def count(
        self,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        language: Optional[str] = None,
        use_case: Optional[str] = None,
        tts_backend: Optional[str] = None,
    ) -> int:
        """Count voices with optional filters."""
        with self.get_session() as session:
            query = session.query(VoiceModel)

            # Apply filters - use exact matching instead of substring matching
            if accent:
                query = query.filter(VoiceModel.accent.ilike(accent))
            if age:
                query = query.filter(VoiceModel.age.ilike(age))
            if category:
                query = query.filter(VoiceModel.category.ilike(category))
            if gender:
                query = query.filter(VoiceModel.gender.ilike(gender))
            if language:
                query = query.filter(VoiceModel.language.ilike(language))
            if use_case:
                query = query.filter(VoiceModel.use_case.ilike(use_case))
            if tts_backend:
                query = query.filter(VoiceModel.tts_backend == tts_backend)

            return query.count()
