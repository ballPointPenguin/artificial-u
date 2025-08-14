"""
Course management service for ArtificialU.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from artificial_u.models.converters import (
    course_model_to_dict,
    professor_model_to_dict,
)
from artificial_u.models.core import Course, Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.professor_service import ProfessorService
from artificial_u.utils import (
    CourseNotFoundError,
    DatabaseError,
    ProfessorNotFoundError,
)


class CourseService:
    """Service for managing course entities.

    Note: AI generation functionality is handled by CourseGeneratorService.
    """

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        professor_service: ProfessorService,
        logger=None,
    ):
        """
        Initialize the course service.

        Args:
            repository_factory: Repository factory instance
            professor_service: Service for professor operations
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.professor_service = professor_service  # Needed for create_course
        self.logger = logger or logging.getLogger(__name__)

    # --- CRUD Methods --- #

    def create_course(
        self,
        title: str,
        code: str,
        department_id: str,
        level: str,
        professor_id: Optional[str] = None,
        description: Optional[str] = None,
        credits: Optional[int] = 3,
        weeks: int = 14,
        lectures_per_week: int = 1,
    ) -> Tuple[Course, Professor]:
        """
        Create a new course without generating content.

        Args:
            title: Course title
            code: Course code (e.g., "CS101")
            department_id: ID of existing department
            level: Course level (Undergraduate, Graduate, etc.)
            professor_id: ID of existing professor
            description: Course description
            credits: Number of credits for the course (default: 3)
            weeks: Number of weeks in the course
            lectures_per_week: Number of lectures per week

        Returns:
            Tuple: (Course, Professor) - The created course and its professor
        """
        self.logger.info(f"Creating new course: {code} - {title}")

        try:
            professor = self.professor_service.get_professor(professor_id)
            if not professor:
                raise ProfessorNotFoundError(
                    f"Professor ID {professor_id} not found for course creation."
                )

        except ProfessorNotFoundError as e:
            self.logger.error(f"Professor not found: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting professor {professor_id}: {e}")
            raise DatabaseError(f"Error retrieving professor {professor_id}")

        # Create basic course model
        course = Course(
            code=code,
            title=title,
            department_id=department_id,
            level=level,
            professor_id=professor.id,
            description=description,
            credits=credits,
            total_weeks=weeks,
            lectures_per_week=lectures_per_week,
        )

        # Save using the repository factory
        try:
            # Use the course repository directly
            created_course = self.repository_factory.course.create(course)
            self.logger.info(f"Course created with ID: {created_course.id}")
            return created_course, professor
        except Exception as e:
            error_msg = f"Failed to save course {code}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def get_course(self, course_id: int) -> Course:
        """
        Get a course by ID.

        Args:
            course_id: ID of the course

        Returns:
            Course: The course object

        Raises:
            CourseNotFoundError: If course not found
        """
        course = self.repository_factory.course.get(course_id)
        if not course:
            error_msg = f"Course with ID {course_id} not found"
            self.logger.error(error_msg)
            raise CourseNotFoundError(error_msg)
        return course

    def get_course_by_code(self, course_code: str) -> Course:
        """
        Get a course by its code.

        Args:
            course_code: Course code to look up

        Returns:
            Course: The course object

        Raises:
            CourseNotFoundError: If course not found
        """
        course = self.repository_factory.course.get_by_code(course_code)
        if not course:
            error_msg = f"Course with code {course_code} not found"
            self.logger.error(error_msg)
            raise CourseNotFoundError(error_msg)
        return course

    def list_courses(self, department_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all courses with professor information, using repository factory.

        Args:
            department_id: Optional department ID to filter by.

        Returns:
            List[Dict]: List of courses with professor information.
        """
        self.logger.info(
            f"Listing courses{f' for department {department_id}' if department_id else ''}"
        )

        try:
            courses = self.repository_factory.course.list(department_id=department_id)
            result = []
            for course in courses:
                # Fetch professor using the repository directly
                professor = self.repository_factory.professor.get(course.professor_id)
                result.append(
                    {
                        # Convert models to dicts for consistent output?
                        "course": course_model_to_dict(course),
                        "professor": professor_model_to_dict(professor),
                    }
                )
            self.logger.debug(f"Found {len(result)} courses")
            return result
        except Exception as e:
            error_msg = f"Failed to list courses: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def update_course(self, course_id: int, update_data: Dict[str, Any]) -> Course:
        """
        Update a course.

        Args:
            course_id: ID of the course to update
            update_data: Dictionary of fields to update

        Returns:
            Course: The updated course

        Raises:
            CourseNotFoundError: If course not found
            DatabaseError: If there's an error updating the database
        """
        # Get existing course model
        course = self.get_course(course_id)
        # Update fields (simple approach)
        for key, value in update_data.items():
            if hasattr(course, key):
                setattr(course, key, value)
            else:
                self.logger.warning(f"Ignoring unknown field during update: {key}")

        # Save changes using repository
        try:
            updated_course = self.repository_factory.course.update(course)
            return updated_course
        except Exception as e:
            error_msg = f"Failed to update course {course_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def delete_course(self, course_id: int) -> bool:
        """
        Delete a course.

        Args:
            course_id: ID of the course to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            CourseNotFoundError: If course not found
            DatabaseError: If there's an error deleting from the database
        """
        # Check existence via get_course
        self.get_course(course_id)
        # Delete using repository
        try:
            result = self.repository_factory.course.delete(course_id)
            if result:
                self.logger.info(f"Course {course_id} deleted successfully")
            return result
        except Exception as e:
            error_msg = f"Failed to delete course {course_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e
