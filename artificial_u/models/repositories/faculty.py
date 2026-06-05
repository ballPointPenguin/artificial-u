"""
Faculty repository for database operations.
"""

from typing import List, Optional

from artificial_u.models.core import Faculty
from artificial_u.models.database import FacultyModel
from artificial_u.models.repositories.base import BaseRepository


class FacultyRepository(BaseRepository):
    """Repository for Faculty operations."""

    def create(self, faculty: Faculty) -> Faculty:
        """Create a new faculty."""
        with self.get_session() as session:
            db_faculty = FacultyModel(
                name=faculty.name,
                description=faculty.description,
                language=faculty.language,
            )

            session.add(db_faculty)
            session.commit()
            session.refresh(db_faculty)

            faculty.id = db_faculty.id
            faculty.created_at = db_faculty.created_at
            faculty.updated_at = db_faculty.updated_at
            return faculty

    def get(self, faculty_id: int) -> Optional[Faculty]:
        """Get a faculty by ID."""
        with self.get_session() as session:
            db_faculty = session.query(FacultyModel).filter_by(id=faculty_id).first()

            if not db_faculty:
                return None

            return Faculty(
                id=db_faculty.id,
                name=db_faculty.name,
                description=db_faculty.description,
                language=db_faculty.language,
                created_at=db_faculty.created_at,
                updated_at=db_faculty.updated_at,
            )

    def get_by_name(self, name: str) -> Optional[Faculty]:
        """Get a faculty by name."""
        with self.get_session() as session:
            db_faculty = session.query(FacultyModel).filter_by(name=name).first()

            if not db_faculty:
                return None

            return Faculty(
                id=db_faculty.id,
                name=db_faculty.name,
                description=db_faculty.description,
                language=db_faculty.language,
                created_at=db_faculty.created_at,
                updated_at=db_faculty.updated_at,
            )

    def get_by_name_and_language(self, name: str, language: str) -> Optional[Faculty]:
        """Get a faculty by name and language (for idempotent seeding)."""
        with self.get_session() as session:
            db_faculty = session.query(FacultyModel).filter_by(name=name, language=language).first()

            if not db_faculty:
                return None

            return Faculty(
                id=db_faculty.id,
                name=db_faculty.name,
                description=db_faculty.description,
                language=db_faculty.language,
                created_at=db_faculty.created_at,
                updated_at=db_faculty.updated_at,
            )

    def list(self, language: Optional[str] = None) -> List[Faculty]:
        """List faculties, optionally filtered by language."""
        with self.get_session() as session:
            query = session.query(FacultyModel)
            if language is not None:
                query = query.filter_by(language=language)
            db_faculties = query.all()

            return [
                Faculty(
                    id=f.id,
                    name=f.name,
                    description=f.description,
                    language=f.language,
                    created_at=f.created_at,
                    updated_at=f.updated_at,
                )
                for f in db_faculties
            ]

    def update(self, faculty: Faculty) -> Faculty:
        """Update a faculty."""
        with self.get_session() as session:
            db_faculty = session.query(FacultyModel).filter_by(id=faculty.id).first()

            if not db_faculty:
                raise ValueError(f"Faculty with ID {faculty.id} not found")

            # Update fields
            db_faculty.name = faculty.name
            db_faculty.description = faculty.description
            db_faculty.language = faculty.language

            session.commit()
            session.refresh(db_faculty)

            faculty.updated_at = db_faculty.updated_at
            return faculty

    def delete(self, faculty_id: int) -> bool:
        """
        Delete a faculty by ID.

        Args:
            faculty_id: ID of the faculty to delete

        Returns:
            True if deleted successfully, False if faculty not found
        """
        with self.get_session() as session:
            # Check if faculty exists
            db_faculty = session.query(FacultyModel).filter_by(id=faculty_id).first()

            if not db_faculty:
                return False

            # Delete the faculty
            session.delete(db_faculty)
            session.commit()
            return True
