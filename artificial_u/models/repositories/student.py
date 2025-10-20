"""
Student repository for database operations.
"""

from typing import Dict, Optional

from artificial_u.models.core import Student
from artificial_u.models.database import StudentModel
from artificial_u.models.repositories.base import BaseRepository


class StudentRepository(BaseRepository):
    """Repository for Student operations."""

    def get(self, student_id: int) -> Optional[Student]:
        """
        Get a student by ID.

        Args:
            student_id: ID of the student to retrieve

        Returns:
            Student object if found, None otherwise
        """
        with self.get_session() as session:
            db_student = session.get(StudentModel, student_id)
            if not db_student:
                return None
            return Student(
                id=db_student.id,
                name=db_student.name,
                email=db_student.email,
                auth0_sub=db_student.auth0_sub,
            )

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

    def update(self, student: Student) -> Student:
        """
        Update an existing student.

        Args:
            student: Student object with updated values

        Returns:
            Updated Student object

        Raises:
            ValueError: If student not found
        """
        with self.get_session() as session:
            db_student = session.get(StudentModel, student.id)
            if not db_student:
                raise ValueError(f"Student with ID {student.id} not found")

            # Update fields
            db_student.name = student.name
            db_student.email = student.email
            db_student.auth0_sub = student.auth0_sub

            session.commit()
            session.refresh(db_student)
            return Student(
                id=db_student.id,
                name=db_student.name,
                email=db_student.email,
                auth0_sub=db_student.auth0_sub,
            )

    def update_fields(self, student_id: int, update_data: Dict[str, any]) -> Optional[Student]:
        """
        Partially update fields on an existing student.

        Only the fields provided in update_data will be modified.

        Args:
            student_id: ID of the student to update
            update_data: Mapping of column names to new values

        Returns:
            Student: The updated student model, or None if not found

        Raises:
            ValueError: If the student does not exist
        """
        with self.get_session() as session:
            db_student = session.get(StudentModel, student_id)
            if not db_student:
                return None

            # Apply only provided fields (whitelist approach)
            allowed_fields = {"name", "email"}
            for key, value in update_data.items():
                if key in allowed_fields:
                    setattr(db_student, key, value)

            session.commit()
            session.refresh(db_student)

            return Student(
                id=db_student.id,
                name=db_student.name,
                email=db_student.email,
                auth0_sub=db_student.auth0_sub,
            )
