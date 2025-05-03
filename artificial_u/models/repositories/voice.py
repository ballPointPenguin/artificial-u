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

    def create(self, voice: Voice) -> Voice:
        """Create a new voice record."""
        with self.get_session() as session:
            db_voice = VoiceModel(
                el_voice_id=voice.el_voice_id,
                name=voice.name,
                accent=voice.accent,
                gender=voice.gender,
                age=voice.age,
                descriptive=voice.descriptive,
                use_case=voice.use_case,
                category=voice.category,
                language=voice.language,
                locale=voice.locale,
                description=voice.description,
                preview_url=voice.preview_url,
                verified_languages=voice.verified_languages,
                popularity_score=voice.popularity_score,
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

            return Voice(
                id=db_voice.id,
                el_voice_id=db_voice.el_voice_id,
                name=db_voice.name,
                accent=db_voice.accent,
                gender=db_voice.gender,
                age=db_voice.age,
                descriptive=db_voice.descriptive,
                use_case=db_voice.use_case,
                category=db_voice.category,
                language=db_voice.language,
                locale=db_voice.locale,
                description=db_voice.description,
                preview_url=db_voice.preview_url,
                verified_languages=db_voice.verified_languages or {},
                popularity_score=db_voice.popularity_score,
                last_updated=db_voice.last_updated,
            )

    def get_by_elevenlabs_id(self, elevenlabs_id: str) -> Optional[Voice]:
        """Get a voice by ElevenLabs voice ID."""
        with self.get_session() as session:
            db_voice = session.query(VoiceModel).filter_by(el_voice_id=elevenlabs_id).first()

            if not db_voice:
                return None

            return Voice(
                id=db_voice.id,
                el_voice_id=db_voice.el_voice_id,
                name=db_voice.name,
                accent=db_voice.accent,
                gender=db_voice.gender,
                age=db_voice.age,
                descriptive=db_voice.descriptive,
                use_case=db_voice.use_case,
                category=db_voice.category,
                language=db_voice.language,
                locale=db_voice.locale,
                description=db_voice.description,
                preview_url=db_voice.preview_url,
                verified_languages=db_voice.verified_languages or {},
                popularity_score=db_voice.popularity_score,
                last_updated=db_voice.last_updated,
            )

    def list(
        self,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        language: Optional[str] = None,
        use_case: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Voice]:
        """List voices with optional filters."""
        with self.get_session() as session:
            query = session.query(VoiceModel)

            # Apply filters
            if gender:
                query = query.filter(VoiceModel.gender == gender)
            if accent:
                query = query.filter(VoiceModel.accent == accent)
            if age:
                query = query.filter(VoiceModel.age == age)
            if language:
                query = query.filter(VoiceModel.language == language)
            if use_case:
                query = query.filter(VoiceModel.use_case == use_case)
            if category:
                query = query.filter(VoiceModel.category == category)

            # Apply pagination
            voices = (
                query.order_by(VoiceModel.popularity_score.desc()).limit(limit).offset(offset).all()
            )

            return [
                Voice(
                    id=v.id,
                    el_voice_id=v.el_voice_id,
                    name=v.name,
                    accent=v.accent,
                    gender=v.gender,
                    age=v.age,
                    descriptive=v.descriptive,
                    use_case=v.use_case,
                    category=v.category,
                    language=v.language,
                    locale=v.locale,
                    description=v.description,
                    preview_url=v.preview_url,
                    verified_languages=v.verified_languages or {},
                    popularity_score=v.popularity_score,
                    last_updated=v.last_updated,
                )
                for v in voices
            ]

    def update(self, voice: Voice) -> Voice:
        """Update an existing voice."""
        with self.get_session() as session:
            db_voice = session.query(VoiceModel).filter_by(id=voice.id).first()

            if not db_voice:
                raise ValueError(f"Voice with ID {voice.id} not found")

            db_voice.el_voice_id = voice.el_voice_id
            db_voice.name = voice.name
            db_voice.accent = voice.accent
            db_voice.gender = voice.gender
            db_voice.age = voice.age
            db_voice.descriptive = voice.descriptive
            db_voice.use_case = voice.use_case
            db_voice.category = voice.category
            db_voice.language = voice.language
            db_voice.locale = voice.locale
            db_voice.description = voice.description
            db_voice.preview_url = voice.preview_url
            db_voice.verified_languages = voice.verified_languages
            db_voice.popularity_score = voice.popularity_score
            db_voice.last_updated = datetime.now()

            session.commit()
            return voice

    def upsert(self, voice: Voice) -> Voice:
        """Create or update a voice based on ElevenLabs voice_id."""
        existing_voice = self.get_by_elevenlabs_id(voice.el_voice_id)
        if existing_voice:
            voice.id = existing_voice.id
            return self.update(voice)
        return self.create(voice)
