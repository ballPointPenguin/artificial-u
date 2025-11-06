"""
Department management service for ArtificialU.
"""

import logging
from typing import Dict, List, Optional

from artificial_u.models.core import Course, Department, Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.utils import (
    DatabaseError,
    DepartmentNotFoundError,
    DependencyError,
)


class DepartmentService:
    """Service for managing department entities.

    Note: AI generation functionality is handled by DepartmentGeneratorService.
    """

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        professor_service,
        course_service,
        logger=None,
    ):
        """
        Initialize the department service.

        Args:
            repository_factory: Repository factory instance
            professor_service: Professor management service
            course_service: Course management service
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.professor_service = professor_service
        self.course_service = course_service
        self.logger = logger or logging.getLogger(__name__)

    # --- CRUD Methods --- #

    def create_department(
        self,
        name: str,
        code: str,
        faculty_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Department:
        """
        Create a new department.

        Args:
            name: Department name
            code: Department code (e.g., "CS" for Computer Science)
            faculty_id: ID of the faculty the department belongs to
            description: Optional department description

        Returns:
            Department: The created department

        Raises:
            DatabaseError: If there's an error saving to the database
        """
        self.logger.info(f"Creating new department: {code} - {name}")

        # Create department object
        department = Department(
            name=name,
            code=code,
            faculty_id=faculty_id,
            description=description or f"The {name} department.",
        )

        # Save to database
        try:
            department = self.repository_factory.department.create(department)
            self.logger.info(f"Department created with ID: {department.id}")
            return department
        except Exception as e:
            error_msg = f"Failed to save department: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def get_department(self, department_id: str) -> Department:
        """
        Get a department by ID.

        Args:
            department_id: ID of the department

        Returns:
            Department: The department object

        Raises:
            DepartmentNotFoundError: If department not found
        """
        department = self.repository_factory.department.get(department_id)
        if not department:
            error_msg = f"Department with ID {department_id} not found"
            self.logger.error(error_msg)
            raise DepartmentNotFoundError(error_msg)
        return department

    def get_department_by_code(self, code: str) -> Department:
        """
        Get a department by its code.

        Args:
            code: Department code to look up

        Returns:
            Department: The department object

        Raises:
            DepartmentNotFoundError: If department not found
        """
        department = self.repository_factory.department.get_by_code(code)
        if not department:
            error_msg = f"Department with code {code} not found"
            self.logger.error(error_msg)
            raise DepartmentNotFoundError(error_msg)
        return department

    def list_departments(self, faculty_id: Optional[int] = None) -> List[Department]:
        """
        List all departments with optional faculty_id filter.

        Args:
            faculty_id: Optional faculty ID to filter by

        Returns:
            List[Department]: List of departments

        Raises:
            DatabaseError: If there's an error retrieving from the database
        """
        try:
            departments = self.repository_factory.department.list(faculty_id)
            self.logger.debug(f"Found {len(departments)} departments")
            return departments
        except Exception as e:
            error_msg = f"Failed to list departments: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def update_department(self, department_id: str, update_data: Dict) -> Department:
        """
        Update a department.

        Args:
            department_id: ID of the department to update
            update_data: Dictionary of fields to update

        Returns:
            Department: The updated department

        Raises:
            DepartmentNotFoundError: If department not found
            DatabaseError: If there's an error updating the database
        """
        # Get existing department
        department = self.get_department(department_id)

        # Update fields
        for key, value in update_data.items():
            if hasattr(department, key):
                setattr(department, key, value)
            else:
                self.logger.warning(f"Ignoring unknown field: {key}")

        # Save changes
        try:
            updated_department = self.repository_factory.department.update(department)
            return updated_department
        except Exception as e:
            error_msg = f"Failed to update department: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_department(self, department_id: str) -> bool:
        """
        Delete a department.

        Args:
            department_id: ID of the department to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            DepartmentNotFoundError: If department not found
            DependencyError: If department has dependencies
            DatabaseError: If there's an error deleting from the database
        """
        # Check for dependencies
        professors = self.repository_factory.professor.list_by_department(department_id)
        if professors:
            error_msg = f"Cannot delete department with {len(professors)} professors"
            self.logger.error(error_msg)
            raise DependencyError(error_msg)

        courses = self.repository_factory.course.list(department_id=department_id)
        if courses:
            error_msg = f"Cannot delete department with {len(courses)} courses"
            self.logger.error(error_msg)
            raise DependencyError(error_msg)

        # Delete the department
        try:
            result = self.repository_factory.department.delete(department_id)
            if result:
                self.logger.info(f"Department {department_id} deleted successfully")
            return result
        except Exception as e:
            error_msg = f"Failed to delete department: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_department_professors(self, department_id: str) -> List[Professor]:
        """
        Get all professors in a department.

        Args:
            department_id: ID of the department

        Returns:
            List[Professor]: List of professors in the department

        Raises:
            DepartmentNotFoundError: If department not found
            DatabaseError: If there's an error retrieving from the database
        """
        # Check if department exists
        self.get_department(department_id)

        try:
            professors = self.repository_factory.professor.list_by_department(
                department_id=department_id
            )
            self.logger.debug(f"Found {len(professors)} professors")
            return professors
        except Exception as e:
            error_msg = f"Failed to get department professors: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_department_courses(self, department_id: str) -> List[Course]:
        """
        Get all courses in a department.

        Args:
            department_id: ID of the department

        Returns:
            List[Course]: List of courses in the department

        Raises:
            DepartmentNotFoundError: If department not found
            DatabaseError: If there's an error retrieving from the database
        """
        # Check if department exists
        self.get_department(department_id)

        try:
            courses = self.repository_factory.course.list(department_id=department_id)
            self.logger.debug(f"Found {len(courses)} courses")
            return courses
        except Exception as e:
            error_msg = f"Failed to get department courses: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e
