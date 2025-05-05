"""
Department management service for ArtificialU.
"""

import logging
from typing import Dict, List, Optional

from artificial_u.config import get_settings
from artificial_u.models.converters import (
    department_model_to_dict,
    extract_xml_content,
    parse_department_xml,
)
from artificial_u.models.core import Course, Department, Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts import (
    get_department_prompt,
    get_system_prompt,
)
from artificial_u.services.content_service import ContentService
from artificial_u.utils import (
    ContentGenerationError,
    DatabaseError,
    DepartmentNotFoundError,
    DependencyError,
)


class DepartmentService:
    """Service for managing department entities."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        professor_service,
        course_service,
        content_service: ContentService,
        logger=None,
    ):
        """
        Initialize the department service.

        Args:
            repository_factory: Repository factory instance
            professor_service: Professor management service
            course_service: Course management service
            content_service: Content generation service
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.professor_service = professor_service
        self.course_service = course_service
        self.content_service = content_service
        self.logger = logger or logging.getLogger(__name__)

    async def generate_department(self, partial_attributes: Optional[Dict] = None) -> dict:
        """
        Generate a department using AI based on provided partial attributes.

        Args:
            partial_attributes: Optional dictionary containing attributes to guide generation

        Returns:
            dict: The generated department attributes

        Raises:
            ContentGenerationError: If generation or parsing fails
            DatabaseError: If there's an error accessing the database
        """
        partial_attributes = partial_attributes or {}
        self.logger.info(
            f"Generating department with partial attributes: {list(partial_attributes.keys())}"
        )

        try:
            # Get existing departments for context
            # existing_courses_models = await self._get_existing_courses(department_model)
            # existing_courses_dicts = [course_model_to_dict(c) for c in existing_courses_models]
            existing_departments_models = self.repository_factory.department.list()
            existing_departments_dicts = [
                department_model_to_dict(d) for d in existing_departments_models
            ]

            # Extract freeform prompt if present
            freeform_prompt = partial_attributes.pop("freeform_prompt", None)

            # Get the prompt using the helper function
            prompt = get_department_prompt(
                existing_departments=existing_departments_dicts,
                partial_attributes=partial_attributes,
                freeform_prompt=freeform_prompt,
            )

            settings = get_settings()

            # Generate the department using content service
            self.logger.info("Calling content service to generate department...")
            response = await self.content_service.generate_text(
                prompt=prompt,
                model=settings.DEPARTMENT_GENERATION_MODEL,
                system_prompt=get_system_prompt("department"),
            )
            self.logger.info("Received response from content service.")

            if not response:
                raise ContentGenerationError("Content service returned empty response")

            # Extract XML content if wrapped in output tags
            xml_content = extract_xml_content(response, "output")
            if not xml_content:
                xml_content = response  # Use full response if no output tags

            # Parse the response using the converter function
            department_attrs = parse_department_xml(xml_content)
            self.logger.info(f"Successfully generated department: {department_attrs.get('name')}")
            return department_attrs

        except ContentGenerationError:
            # Re-raise content generation errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error during department generation: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ContentGenerationError(error_msg) from e

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
            description=description or f"The {name} department in the {faculty} faculty.",
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
