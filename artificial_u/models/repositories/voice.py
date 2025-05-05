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

            return Voice(
                id=db_voice.id,
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
                verified_languages=db_voice.verified_languages or {},
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
                verified_languages=db_voice.verified_languages or {},
                last_updated=db_voice.last_updated,
            )

    def list(
        self,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        language: Optional[str] = None,
        use_case: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Voice]:
        """List voices with optional filters."""
        with self.get_session() as session:
            query = session.query(VoiceModel)

            # Apply filters
            if accent:
                query = query.filter(VoiceModel.accent.ilike(f"%{accent}%"))
            if age:
                query = query.filter(VoiceModel.age.ilike(f"%{age}%"))
            if category:
                query = query.filter(VoiceModel.category.ilike(f"%{category}%"))
            if gender:
                query = query.filter(VoiceModel.gender.ilike(f"%{gender}%"))
            if language:
                query = query.filter(VoiceModel.language.ilike(f"%{language}%"))
            if use_case:
                query = query.filter(VoiceModel.use_case.ilike(f"%{use_case}%"))

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
                    age=v.age,
                    category=v.category,
                    description=v.description,
                    descriptive=v.descriptive,
                    gender=v.gender,
                    language=v.language,
                    locale=v.locale,
                    popularity_score=v.popularity_score,
                    preview_url=v.preview_url,
                    use_case=v.use_case,
                    verified_languages=v.verified_languages or {},
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
        """Create or update a voice based on ElevenLabs voice_id."""
        existing_voice = self.get_by_elevenlabs_id(voice.el_voice_id)
        if existing_voice:
            voice.id = existing_voice.id
            return self.update(voice)
        return self.create(voice)
