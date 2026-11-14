"""
Department repository for database operations.
"""

from typing import List, Optional

from artificial_u.models.core import Department
from artificial_u.models.database import CourseModel, DepartmentModel, ProfessorModel
from artificial_u.models.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository):
    """Repository for Department operations."""

    @staticmethod
    def _to_model(row: DepartmentModel) -> Department:
        """Convert a database row to a core Department."""
        return Department(
            id=row.id,
            name=row.name,
            code=row.code,
            faculty_id=row.faculty_id,
            description=row.description,
            language=row.language,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    def create(self, department: Department) -> Department:
        """Create a new department."""
        with self.get_session() as session:
            db_department = DepartmentModel(
                name=department.name,
                code=department.code,
                faculty_id=department.faculty_id,
                description=department.description,
                language=department.language,
            )

            session.add(db_department)
            session.commit()
            session.refresh(db_department)

            department.id = db_department.id
            department.created_at = db_department.created_at
            department.updated_at = db_department.updated_at
            return department

    def get(self, department_id: int) -> Optional[Department]:
        """Get a department by ID."""
        with self.get_session() as session:
            db_department = session.query(DepartmentModel).filter_by(id=department_id).first()

            if not db_department:
                return None

            return self._to_model(db_department)

    def get_by_code(self, code: str) -> Optional[Department]:
        """Get a department by code."""
        with self.get_session() as session:
            db_department = session.query(DepartmentModel).filter_by(code=code).first()

            if not db_department:
                return None

            return self._to_model(db_department)

    def list(
        self,
        faculty_id: Optional[int] = None,
        language: Optional[str] = None,
    ) -> List[Department]:
        """List departments with optional faculty_id and language filters."""
        with self.get_session() as session:
            query = session.query(DepartmentModel)

            if faculty_id:
                query = query.filter_by(faculty_id=faculty_id)
            if language is not None:
                query = query.filter_by(language=language)

            db_departments = query.all()

            return [self._to_model(d) for d in db_departments]

    def update(self, department: Department) -> Department:
        """Update a department."""
        with self.get_session() as session:
            db_department = session.query(DepartmentModel).filter_by(id=department.id).first()

            if not db_department:
                raise ValueError(f"Department with ID {department.id} not found")

            # Update fields
            db_department.name = department.name
            db_department.code = department.code
            db_department.faculty_id = department.faculty_id
            db_department.description = department.description
            db_department.language = department.language

            session.commit()
            session.refresh(db_department)

            department.updated_at = db_department.updated_at
            return department

    def delete(self, department_id: int) -> bool:
        """
        Delete a department by ID and set department_id to null for associated records.

        Args:
            department_id: ID of the department to delete

        Returns:
            True if deleted successfully, False if department not found
        """
        with self.get_session() as session:
            # Check if department exists
            db_department = session.query(DepartmentModel).filter_by(id=department_id).first()

            if not db_department:
                return False

            # Update associated professors to set department_id to null
            session.query(ProfessorModel).filter_by(department_id=department_id).update(
                {ProfessorModel.department_id: None}
            )

            # Update associated courses to set department_id to null
            session.query(CourseModel).filter_by(department_id=department_id).update(
                {CourseModel.department_id: None}
            )

            # Delete the department
            session.delete(db_department)
            session.commit()
            return True
