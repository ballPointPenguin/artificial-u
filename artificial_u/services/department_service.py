"""
Department management service for ArtificialU.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from artificial_u.config import get_settings
from artificial_u.models.core import Course, Department, Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts.department import get_department_prompt, get_open_department_prompt
from artificial_u.prompts.system import GENERIC_XML_SYSTEM_PROMPT
from artificial_u.services.content_service import ContentService
from artificial_u.utils.exceptions import DatabaseError, DepartmentNotFoundError, DependencyError


class DepartmentService:
    """Service for managing department entities."""

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

    def create_department(
        self,
        name: str,
        code: str,
        faculty: str,
        description: Optional[str] = None,
    ) -> Department:
        """
        Create a new department.

        Args:
            name: Department name
            code: Department code (e.g., "CS" for Computer Science)
            faculty: Faculty the department belongs to
            description: Optional department description

        Returns:
            Department: The created department

        Raises:
            DatabaseError: If there's an error saving to the database
        """

        # Create department object
        department = Department(
            name=name,
            code=code,
            faculty=faculty,
            description=description or f"The {name} department in the {faculty} faculty.",
        )

        # Save to database
        try:
            department = self.repository_factory.department.create(department)
            return department
        except Exception as e:
            error_msg = f"Failed to save department: {str(e)}"
            self.logger.error(error_msg)
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

    def list_departments(self, faculty: Optional[str] = None) -> List[Department]:
        """
        List all departments with optional faculty filter.

        Args:
            faculty: Optional faculty to filter by

        Returns:
            List[Department]: List of departments

        Raises:
            DatabaseError: If there's an error retrieving from the database
        """
        try:
            departments = self.repository_factory.department.list(faculty)
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
        # TODO: Check if department exists
        # department = self.get_department(department_id)

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

    async def generate_department(self, department_data: dict) -> dict:
        """
        Generate a department using AI based on the department name, course_name, or neither.
        If both name and course_name are supplied, name takes precedence.

        This function uses the content service with Ollama to generate a department
        based on the provided name, or invents a new department if no name is given.
        It uses the GENERIC_XML_SYSTEM_PROMPT and the appropriate prompt to guide the generation.

        Args:
            name: The name of the department to generate (optional)
            course_name: The name of the course to generate a department for (optional)
        Returns:
            dict: The generated department as a dictionary
        """

        name = department_data.get("name")
        course_name = department_data.get("course_name")

        if name:
            prompt = get_department_prompt(name)
        elif course_name:
            prompt = get_department_prompt(course_name=course_name)
        else:
            # Use the existing repository_factory instead of creating a new repository
            existing_departments = self.repository_factory.department.list_department_names()
            prompt = get_open_department_prompt(existing_departments=existing_departments)

        # Use the content service to generate the department
        content_service = ContentService(logger=self.logger)

        settings = get_settings()
        # Use the centrally defined setting
        model = settings.DEPARTMENT_GENERATION_MODEL

        # Generate the department using Ollama
        response = await content_service.generate_text(
            prompt=prompt,
            model=model,
            system_prompt=GENERIC_XML_SYSTEM_PROMPT,
        )

        return parse_department_xml(response)


def parse_department_xml(xml_str: str) -> dict:
    root = ET.fromstring(xml_str.strip())
    # Find the <department> element
    dept = root.find("department") if root.tag != "department" else root
    if dept is None:
        raise ValueError("No <department> element found in generated XML.")

    return {
        "name": dept.findtext("name"),
        "code": dept.findtext("code"),
        "faculty": dept.findtext("faculty"),
        "description": dept.findtext("description"),
    }
