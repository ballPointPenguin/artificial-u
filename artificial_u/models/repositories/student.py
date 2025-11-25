"""
Student repository for database operations.
"""

from typing import Dict, List, Optional

from sqlalchemy import func

from artificial_u.models.core import Student
from artificial_u.models.database import StudentModel
from artificial_u.models.repositories.base import BaseRepository


class StudentRepository(BaseRepository):
    """Repository for Student operations."""

    def _ensure_unique_email(
        self, session, email: Optional[str], exclude_student_id: Optional[int] = None
    ) -> None:
        if not email:
            return

        email_lower = email.lower()
        query = session.query(StudentModel).filter(func.lower(StudentModel.email) == email_lower)
        if exclude_student_id is not None:
            query = query.filter(StudentModel.id != exclude_student_id)

        if session.query(query.exists()).scalar():
            raise ValueError(f"Email '{email}' is already in use")

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
            self._ensure_unique_email(session, email)
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

    def get_by_email(self, email: str) -> Optional[Student]:
        """Get a student by email (case-insensitive)."""
        if not email:
            return None
        with self.get_session() as session:
            db_student = (
                session.query(StudentModel)
                .filter(func.lower(StudentModel.email) == email.lower())
                .first()
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

    def link_auth0_sub(self, student_id: int, auth0_sub: str) -> Student:
        """Link an Auth0 sub to an existing student account."""
        with self.get_session() as session:
            db_student = session.get(StudentModel, student_id)
            if not db_student:
                raise ValueError(f"Student with ID {student_id} not found")
            db_student.auth0_sub = auth0_sub
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
        self,
        *,
        auth0_sub: str,
        default_name: str,
        email: Optional[str],
        email_verified: bool = False,
    ) -> Student:
        # First, try to find by auth0_sub
        existing = self.get_by_auth0_sub(auth0_sub)
        if existing:
            return existing

        # If not found by auth0_sub, check if there's an existing account with this email
        # This handles account linking for users who existed before Auth0 integration
        # SECURITY: Only link by email if the email is verified by Auth0
        # This prevents attackers from hijacking accounts by registering with someone else's email
        if email and email_verified:
            existing_by_email = self.get_by_email(email)
            if existing_by_email:
                # Link the Auth0 sub to the existing account
                return self.link_auth0_sub(existing_by_email.id, auth0_sub)

        # No existing account found - create a new one
        # If email exists but isn't verified, create account without email to avoid conflicts
        # The user can add their email later once verified
        safe_email = email if email_verified else None
        return self.create(name=default_name, email=safe_email, auth0_sub=auth0_sub)

    def list_all(self) -> List[Student]:
        """
        List all students.

        Returns:
            List[Student]: List of all students
        """
        with self.get_session() as session:
            db_students = session.query(StudentModel).all()

            return [
                Student(
                    id=db_student.id,
                    name=db_student.name,
                    email=db_student.email,
                    auth0_sub=db_student.auth0_sub,
                    role=db_student.role,
                    coins=db_student.coins,
                    is_active=db_student.is_active,
                )
                for db_student in db_students
            ]

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

            self._ensure_unique_email(session, student.email, exclude_student_id=student.id)

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
            # Check email uniqueness before applying
            if "email" in update_data and update_data["email"] != db_student.email:
                self._ensure_unique_email(
                    session,
                    update_data["email"],
                    exclude_student_id=student_id,
                )

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

    def delete(self, student_id: int) -> bool:
        """
        Permanently delete a student.

        Args:
            student_id: ID of the student to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            ValueError: If the student does not exist
        """
        with self.get_session() as session:
            db_student = session.get(StudentModel, student_id)
            if not db_student:
                raise ValueError(f"Student with ID {student_id} not found")

            session.delete(db_student)
            session.commit()

            return True

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
