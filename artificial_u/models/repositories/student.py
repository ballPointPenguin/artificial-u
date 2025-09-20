"""
Student repository for database operations.
"""

from typing import Optional

from artificial_u.models.core import Student
from artificial_u.models.database import StudentModel
from artificial_u.models.repositories.base import BaseRepository


class StudentRepository(BaseRepository):
    """Repository for Student operations."""

    def get_by_auth0_sub(self, auth0_sub: str) -> Optional[Student]:
        with self.get_session() as session:
            db_student = (
                session.query(StudentModel).filter(StudentModel.auth0_sub == auth0_sub).first()
            )
            if not db_student:
                return None
            return Student(
                id=db_student.id,
                name=db_student.name,
                email=db_student.email,
                auth0_sub=db_student.auth0_sub,
            )

    def create(self, *, name: str, email: Optional[str], auth0_sub: Optional[str]) -> Student:
        with self.get_session() as session:
            db_student = StudentModel(name=name, email=email, auth0_sub=auth0_sub)
            session.add(db_student)
            session.commit()
            session.refresh(db_student)
            return Student(
                id=db_student.id,
                name=db_student.name,
                email=db_student.email,
                auth0_sub=db_student.auth0_sub,
            )

    def get_or_create_by_auth0(
        self, *, auth0_sub: str, default_name: str, email: Optional[str]
    ) -> Student:
        existing = self.get_by_auth0_sub(auth0_sub)
        if existing:
            return existing
        return self.create(name=default_name, email=email, auth0_sub=auth0_sub)
