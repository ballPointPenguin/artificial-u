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
                created_at=db_faculty.created_at,
                updated_at=db_faculty.updated_at,
            )

    def list(self) -> List[Faculty]:
        """List all faculties."""
        with self.get_session() as session:
            db_faculties = session.query(FacultyModel).all()

            return [
                Faculty(
                    id=f.id,
                    name=f.name,
                    description=f.description,
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
