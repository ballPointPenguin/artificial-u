"""
Professor repository for database operations.
"""

from typing import List, Optional

from artificial_u.models.core import Professor
from artificial_u.models.database import ProfessorModel
from artificial_u.models.repositories.base import BaseRepository


class ProfessorRepository(BaseRepository):
    """Repository for Professor operations."""

    def create(self, professor: Professor) -> Professor:
        """Create a new professor."""
        with self.get_session() as session:
            db_professor = ProfessorModel(
                name=professor.name,
                title=professor.title,
                accent=professor.accent,
                age=professor.age,
                background=professor.background,
                description=professor.description,
                gender=professor.gender,
                personality=professor.personality,
                specialization=professor.specialization,
                teaching_style=professor.teaching_style,
                image_url=professor.image_url,
                department_id=professor.department_id,
                voice_id=professor.voice_id,
            )

            session.add(db_professor)
            session.commit()
            session.refresh(db_professor)

            professor.id = db_professor.id
            return professor

    def get(self, professor_id: int) -> Optional[Professor]:
        """Get a professor by ID."""
        with self.get_session() as session:
            db_professor = session.query(ProfessorModel).filter_by(id=professor_id).first()

            if not db_professor:
                return None

            return Professor(
                id=db_professor.id,
                name=db_professor.name,
                title=db_professor.title,
                accent=db_professor.accent,
                age=db_professor.age,
                background=db_professor.background,
                description=db_professor.description,
                gender=db_professor.gender,
                personality=db_professor.personality,
                specialization=db_professor.specialization,
                teaching_style=db_professor.teaching_style,
                image_url=db_professor.image_url,
                department_id=db_professor.department_id,
                voice_id=db_professor.voice_id,
            )

    def list(self) -> List[Professor]:
        """List all professors."""
        with self.get_session() as session:
            db_professors = session.query(ProfessorModel).all()

            return [
                Professor(
                    id=p.id,
                    name=p.name,
                    title=p.title,
                    accent=p.accent,
                    age=p.age,
                    background=p.background,
                    description=p.description,
                    gender=p.gender,
                    personality=p.personality,
                    specialization=p.specialization,
                    teaching_style=p.teaching_style,
                    image_url=p.image_url,
                    department_id=p.department_id,
                    voice_id=p.voice_id,
                )
                for p in db_professors
            ]

    def update(self, professor: Professor) -> Professor:
        """Update an existing professor."""
        with self.get_session() as session:
            db_professor = session.query(ProfessorModel).filter_by(id=professor.id).first()

            if not db_professor:
                raise ValueError(f"Professor with ID {professor.id} not found")

            # Update fields
            db_professor.name = professor.name
            db_professor.title = professor.title
            db_professor.accent = professor.accent
            db_professor.age = professor.age
            db_professor.background = professor.background
            db_professor.description = professor.description
            db_professor.gender = professor.gender
            db_professor.personality = professor.personality
            db_professor.specialization = professor.specialization
            db_professor.teaching_style = professor.teaching_style
            db_professor.image_url = professor.image_url
            db_professor.department_id = professor.department_id
            db_professor.voice_id = professor.voice_id

            session.commit()
            session.refresh(db_professor)

            return professor

    def update_field(self, professor_id: int, **fields) -> Optional[Professor]:
        """
        Update specific fields of a professor.

        Args:
            professor_id: ID of the professor to update
            **fields: Field name-value pairs to update

        Returns:
            Updated professor or None if not found
        """
        with self.get_session() as session:
            db_professor = session.query(ProfessorModel).filter_by(id=professor_id).first()

            if not db_professor:
                return None

            # Update only the specified fields
            for field, value in fields.items():
                if hasattr(db_professor, field):
                    setattr(db_professor, field, value)

            session.commit()
            session.refresh(db_professor)

            # Convert to core model and return
            return Professor(
                id=db_professor.id,
                name=db_professor.name,
                title=db_professor.title,
                accent=db_professor.accent,
                age=db_professor.age,
                background=db_professor.background,
                description=db_professor.description,
                gender=db_professor.gender,
                personality=db_professor.personality,
                specialization=db_professor.specialization,
                teaching_style=db_professor.teaching_style,
                image_url=db_professor.image_url,
                department_id=db_professor.department_id,
                voice_id=db_professor.voice_id,
            )

    def delete(self, professor_id: int) -> bool:
        """
        Delete a professor by ID.

        Args:
            professor_id: ID of the professor to delete

        Returns:
            True if deleted successfully, False if professor not found
        """
        with self.get_session() as session:
            db_professor = session.query(ProfessorModel).filter_by(id=professor_id).first()

            if not db_professor:
                return False

            session.delete(db_professor)
            session.commit()
            return True

    def list_by_department(self, department_id: int) -> List[Professor]:
        """List all professors in a specific department."""
        with self.get_session() as session:
            db_professors = (
                session.query(ProfessorModel).filter_by(department_id=department_id).all()
            )

            return [
                Professor(
                    **{
                        # Required fields
                        "id": p.id,
                        "name": p.name or "",
                        # Optional fields with defaults
                        "title": getattr(p, "title", None),
                        "accent": getattr(p, "accent", None),
                        "age": getattr(p, "age", None),
                        "background": getattr(p, "background", None),
                        "description": getattr(p, "description", None),
                        "gender": getattr(p, "gender", None),
                        "personality": getattr(p, "personality", None),
                        "specialization": getattr(p, "specialization", None),
                        "teaching_style": getattr(p, "teaching_style", None),
                        "image_url": getattr(p, "image_url", None),
                        "department_id": getattr(p, "department_id", None),
                        "voice_id": getattr(p, "voice_id", None),
                    }
                )
                for p in db_professors
            ]
