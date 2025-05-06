"""
Department repository for database operations.
"""

from typing import List, Optional

from artificial_u.models.core import Department
from artificial_u.models.database import CourseModel, DepartmentModel, ProfessorModel
from artificial_u.models.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository):
    """Repository for Department operations."""

    def create(self, department: Department) -> Department:
        """Create a new department."""
        with self.get_session() as session:
            db_department = DepartmentModel(
                name=department.name,
                code=department.code,
                faculty=department.faculty,
                description=department.description,
            )

            session.add(db_department)
            session.commit()
            session.refresh(db_department)

            department.id = db_department.id
            return department

    def get(self, department_id: int) -> Optional[Department]:
        """Get a department by ID."""
        with self.get_session() as session:
            db_department = session.query(DepartmentModel).filter_by(id=department_id).first()

            if not db_department:
                return None

            return Department(
                id=db_department.id,
                name=db_department.name,
                code=db_department.code,
                faculty=db_department.faculty,
                description=db_department.description,
            )

    def get_by_code(self, code: str) -> Optional[Department]:
        """Get a department by code."""
        with self.get_session() as session:
            db_department = session.query(DepartmentModel).filter_by(code=code).first()

            if not db_department:
                return None

            return Department(
                id=db_department.id,
                name=db_department.name,
                code=db_department.code,
                faculty=db_department.faculty,
                description=db_department.description,
            )

    def list(self, faculty: Optional[str] = None) -> List[Department]:
        """List departments with optional faculty filter."""
        with self.get_session() as session:
            query = session.query(DepartmentModel)

            if faculty:
                query = query.filter_by(faculty=faculty)

            db_departments = query.all()

            return [
                Department(
                    id=d.id,
                    name=d.name,
                    code=d.code,
                    faculty=d.faculty,
                    description=d.description,
                )
                for d in db_departments
            ]

    def update(self, department: Department) -> Department:
        """Update a department."""
        with self.get_session() as session:
            db_department = session.query(DepartmentModel).filter_by(id=department.id).first()

            if not db_department:
                raise ValueError(f"Department with ID {department.id} not found")

            # Update fields
            db_department.name = department.name
            db_department.code = department.code
            db_department.faculty = department.faculty
            db_department.description = department.description

            session.commit()
            session.refresh(db_department)

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
