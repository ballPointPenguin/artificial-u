"""
Professor repository for database operations.
"""

from typing import List, Optional

from sqlalchemy.orm import joinedload

from artificial_u.models.core import Professor
from artificial_u.models.database import CourseModel, ProfessorModel
from artificial_u.models.repositories.base import BaseRepository
from artificial_u.utils import DependencyError


class ProfessorRepository(BaseRepository):
    """Repository for Professor operations."""

    @staticmethod
    def _to_model(db_professor: ProfessorModel, include_student: bool = False) -> Professor:
        """Convert a database row to a core Professor."""
        student = None
        if include_student and db_professor.student:
            student = {
                "id": db_professor.student.id,
                "name": db_professor.student.name,
                "email": db_professor.student.email,
            }
        return Professor(
            id=db_professor.id,
            name=db_professor.name or "",
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
            image_created_with=db_professor.image_created_with,
            department_id=db_professor.department_id,
            voice_id=db_professor.voice_id,
            tts_backend=db_professor.tts_backend,
            language=db_professor.language,
            created_by=db_professor.created_by,
            created_with=db_professor.created_with,
            created_at=db_professor.created_at,
            updated_at=db_professor.updated_at,
            student=student,
        )

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
                image_created_with=professor.image_created_with,
                department_id=professor.department_id,
                voice_id=professor.voice_id,
                tts_backend=professor.tts_backend,
                language=professor.language,
                created_by=professor.created_by,
                created_with=professor.created_with,
            )

            session.add(db_professor)
            session.commit()
            session.refresh(db_professor)

            professor.id = db_professor.id
            return professor

    def get(self, professor_id: int) -> Optional[Professor]:
        """Get a professor by ID."""
        with self.get_session() as session:
            db_professor = (
                session.query(ProfessorModel)
                .options(joinedload(ProfessorModel.student))
                .filter_by(id=professor_id)
                .first()
            )

            if not db_professor:
                return None

            return self._to_model(db_professor, include_student=True)

    def list(self, language: Optional[str] = None) -> List[Professor]:
        """List professors with optional language filter."""
        with self.get_session() as session:
            query = session.query(ProfessorModel)
            if language is not None:
                query = query.filter_by(language=language)
            db_professors = query.all()

            return [self._to_model(p) for p in db_professors]

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
            db_professor.image_created_with = professor.image_created_with
            db_professor.department_id = professor.department_id
            db_professor.voice_id = professor.voice_id
            db_professor.tts_backend = professor.tts_backend
            db_professor.language = professor.language

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

            return self._to_model(db_professor)

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

            has_courses = (
                session.query(CourseModel.id)
                .filter(CourseModel.professor_id == professor_id)
                .limit(1)
                .first()
            )
            if has_courses:
                raise DependencyError(
                    f"Cannot delete professor {professor_id}: associated courses exist."
                )

            session.delete(db_professor)
            session.commit()
            return True

    def list_by_department(self, department_id: int) -> List[Professor]:
        """List all professors in a specific department."""
        with self.get_session() as session:
            db_professors = (
                session.query(ProfessorModel).filter_by(department_id=department_id).all()
            )

            return [self._to_model(p) for p in db_professors]

    def list_by_faculty(self, faculty_id: int) -> List[Professor]:
        """List all professors in departments belonging to a specific faculty."""
        from artificial_u.models.database import DepartmentModel

        with self.get_session() as session:
            # Join professors with departments and filter by faculty_id
            db_professors = (
                session.query(ProfessorModel)
                .join(DepartmentModel, ProfessorModel.department_id == DepartmentModel.id)
                .filter(DepartmentModel.faculty_id == faculty_id)
                .distinct()
                .all()
            )

            return [self._to_model(p) for p in db_professors]
