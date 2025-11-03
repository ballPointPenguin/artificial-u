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
                role=db_student.role,
                coins=db_student.coins,
                is_active=db_student.is_active,
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
                role=db_student.role,
                coins=db_student.coins,
                is_active=db_student.is_active,
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
                role=db_student.role,
                coins=db_student.coins,
                is_active=db_student.is_active,
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
            db_student.role = student.role
            db_student.coins = student.coins
            db_student.is_active = student.is_active

            session.commit()
            session.refresh(db_student)
            return Student(
                id=db_student.id,
                name=db_student.name,
                email=db_student.email,
                auth0_sub=db_student.auth0_sub,
                role=db_student.role,
                coins=db_student.coins,
                is_active=db_student.is_active,
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
                role=db_student.role,
                coins=db_student.coins,
                is_active=db_student.is_active,
            )

    def deduct_coins(self, student_id: int, amount: int) -> Student:
        """
        Atomically deduct coins from a student's account.

        Args:
            student_id: ID of the student
            amount: Number of coins to deduct

        Returns:
            Updated Student object

        Raises:
            ValueError: If student not found or insufficient coins
        """
        with self.get_session() as session:
            db_student = session.get(StudentModel, student_id)
            if not db_student:
                raise ValueError(f"Student with ID {student_id} not found")

            if db_student.coins < amount:
                raise ValueError(
                    f"Insufficient coins. Required: {amount}, Available: {db_student.coins}"
                )

            db_student.coins -= amount
            session.commit()
            session.refresh(db_student)

            return Student(
                id=db_student.id,
                name=db_student.name,
                email=db_student.email,
                auth0_sub=db_student.auth0_sub,
                role=db_student.role,
                coins=db_student.coins,
                is_active=db_student.is_active,
            )

    def add_coins(self, student_id: int, amount: int) -> Student:
        """
        Add coins to a student's account.

        Args:
            student_id: ID of the student
            amount: Number of coins to add

        Returns:
            Updated Student object

        Raises:
            ValueError: If student not found
        """
        with self.get_session() as session:
            db_student = session.get(StudentModel, student_id)
            if not db_student:
                raise ValueError(f"Student with ID {student_id} not found")

            db_student.coins += amount
            session.commit()
            session.refresh(db_student)

            return Student(
                id=db_student.id,
                name=db_student.name,
                email=db_student.email,
                auth0_sub=db_student.auth0_sub,
                role=db_student.role,
                coins=db_student.coins,
                is_active=db_student.is_active,
            )

    def update_role(self, student_id: int, role: str) -> Student:
        """
        Update a student's role.

        Args:
            student_id: ID of the student
            role: New role (viewer, creator, admin)

        Returns:
            Updated Student object

        Raises:
            ValueError: If student not found or invalid role
        """
        valid_roles = {"viewer", "creator", "admin"}
        if role not in valid_roles:
            raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")

        with self.get_session() as session:
            db_student = session.get(StudentModel, student_id)
            if not db_student:
                raise ValueError(f"Student with ID {student_id} not found")

            db_student.role = role
            session.commit()
            session.refresh(db_student)

            return Student(
                id=db_student.id,
                name=db_student.name,
                email=db_student.email,
                auth0_sub=db_student.auth0_sub,
                role=db_student.role,
                coins=db_student.coins,
                is_active=db_student.is_active,
            )
