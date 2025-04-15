"""
Department management service for ArtificialU.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from artificial_u.models.core import Course, Department, Professor
from artificial_u.prompts.system import GENERIC_XML_SYSTEM_PROMPT
from artificial_u.utils.exceptions import (
    DatabaseError,
    DepartmentNotFoundError,
    DependencyError,
)


class DepartmentService:
    """Service for managing department entities."""

    def __init__(
        self,
        repository,
        professor_service,
        course_service,
        logger=None,
    ):
        """
        Initialize the department service.

        Args:
            repository: Data repository
            professor_service: Professor management service
            course_service: Course management service
            logger: Optional logger instance
        """
        self.repository = repository
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
        self.logger.info(f"Creating new department: {code} - {name}")

        # Create department object
        department = Department(
            name=name,
            code=code,
            faculty=faculty,
            description=description
            or f"The {name} department in the {faculty} faculty.",
        )

        # Save to database
        try:
            department = self.repository.department.create(department)
            self.logger.info(f"Department created with ID: {department.id}")
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
        department = self.repository.department.get(department_id)
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
        department = self.repository.department.get_by_code(code)
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
        self.logger.info(
            f"Listing departments{f' for faculty {faculty}' if faculty else ''}"
        )

        try:
            departments = self.repository.department.list(faculty)
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
        self.logger.info(f"Updating department {department_id}")

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
            updated_department = self.repository.department.update(department)
            self.logger.info(f"Department {department_id} updated successfully")
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
        self.logger.info(f"Deleting department {department_id}")

        # TODO: Check if department exists
        # department = self.get_department(department_id)

        # Check for dependencies
        professors = self.repository.professor.list(department_id=department_id)
        if professors:
            error_msg = f"Cannot delete department with {len(professors)} professors"
            self.logger.error(error_msg)
            raise DependencyError(error_msg)

        courses = self.repository.course.list(department_id=department_id)
        if courses:
            error_msg = f"Cannot delete department with {len(courses)} courses"
            self.logger.error(error_msg)
            raise DependencyError(error_msg)

        # Delete the department
        try:
            result = self.repository.department.delete(department_id)
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
        self.logger.info(f"Getting professors for department {department_id}")

        # Check if department exists
        self.get_department(department_id)

        try:
            professors = self.repository.professor.list(department_id=department_id)
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
        self.logger.info(f"Getting courses for department {department_id}")

        # Check if department exists
        self.get_department(department_id)

        try:
            courses = self.repository.course.list(department_id=department_id)
            self.logger.debug(f"Found {len(courses)} courses")
            return courses
        except Exception as e:
            error_msg = f"Failed to get department courses: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    async def generate_department(
        self, department_name: str = None, course_name: str = None
    ) -> dict:
        """
        Generate a department using AI based on the department name, course_name, or neither.
        If both department_name and course_name are supplied, department_name takes precedence.

        This function uses the content service with Ollama to generate a department
        based on the provided name, or invents a new department if no name is given.
        It uses the GENERIC_XML_SYSTEM_PROMPT and the appropriate prompt to guide the generation.

        Args:
            department_name: The name of the department to generate (optional)
            course_name: The name of the course to generate a department for (optional)
        Returns:
            dict: The generated department as a dictionary
        """
        if department_name:
            self.logger.info(f"Generating department for: {department_name}")
            from artificial_u.prompts.department import get_department_prompt

            prompt = get_department_prompt(department_name)
        elif course_name:
            self.logger.info(f"Generating department for course: {course_name}")
            from artificial_u.prompts.department import get_course_department_prompt

            prompt = get_course_department_prompt(course_name)
        else:
            self.logger.info(
                "Generating open-ended department (no name or course supplied)"
            )
            from artificial_u.prompts.department import get_open_department_prompt

            prompt = get_open_department_prompt()

        # Use the content service to generate the department
        from artificial_u.services.content_service import ContentService

        content_service = ContentService(logger=self.logger)

        from artificial_u.config import get_settings

        settings = get_settings()
        model = getattr(settings, "OPENAI_GPT_MODEL", "gpt-4.1-nano")

        # Generate the department using Ollama
        response = await content_service.generate_text(
            prompt=prompt,
            # model=DEFAULT_OLLAMA_MODEL,
            model=model,
            system_prompt=GENERIC_XML_SYSTEM_PROMPT,
        )

        # Log the response
        self.logger.info(f"Generated department response: {response[:100]}...")

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
