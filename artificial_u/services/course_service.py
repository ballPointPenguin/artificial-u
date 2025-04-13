"""
Course management service for ArtificialU.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from artificial_u.config.defaults import (
    DEFAULT_COURSE_LEVEL,
    DEFAULT_COURSE_WEEKS,
    DEFAULT_LECTURES_PER_WEEK,
)
from artificial_u.models.core import Course, Department, Professor
from artificial_u.utils.exceptions import (
    ContentGenerationError,
    CourseNotFoundError,
    DatabaseError,
)


class CourseService:
    """Service for managing course entities."""

    def __init__(self, repository, content_generator, professor_service, logger=None):
        """
        Initialize the course service.

        Args:
            repository: Data repository
            content_generator: Content generation service
            professor_service: Professor management service
            logger: Optional logger instance
        """
        self.repository = repository
        self.content_generator = content_generator
        self.professor_service = professor_service
        self.logger = logger or logging.getLogger(__name__)

    def create_course(
        self,
        title: str,
        code: str,
        department: str,
        level: str = DEFAULT_COURSE_LEVEL,
        professor_id: Optional[str] = None,
        description: Optional[str] = None,
        weeks: int = DEFAULT_COURSE_WEEKS,
        lectures_per_week: int = DEFAULT_LECTURES_PER_WEEK,
    ) -> Tuple[Course, Professor]:
        """
        Create a new course with syllabus.

        Args:
            title: Course title
            code: Course code (e.g., "CS101")
            department: Academic department
            level: Course level (Undergraduate, Graduate, etc.)
            professor_id: ID of existing professor (if None, will create new)
            description: Course description (if None, will be generated)
            weeks: Number of weeks in the course
            lectures_per_week: Number of lectures per week

        Returns:
            Tuple: (Course, Professor) - The created course and its professor
        """
        self.logger.info(f"Creating new course: {code} - {title}")

        # Get or create professor
        professor = self.professor_service.get_or_create_professor(professor_id)

        # Generate description if not provided
        if not description:
            description = f"A {level} course on {title} in the {department} department."
            self.logger.debug(f"Generated description: {description}")

        # Create basic course
        course = Course(
            code=code,
            title=title,
            department=department,
            level=level,
            professor_id=professor.id,
            description=description,
            total_weeks=weeks,
            lectures_per_week=lectures_per_week,
        )

        # Generate syllabus
        self._generate_course_syllabus(course, professor)

        # Save to database
        try:
            course = self.repository.course.create(course)
            self.logger.info(f"Course created with ID: {course.id}")
            return course, professor
        except Exception as e:
            error_msg = f"Failed to save course: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _generate_course_syllabus(self, course: Course, professor: Professor) -> None:
        """
        Generate a syllabus for a course.

        Args:
            course: Course object
            professor: Professor object
        """
        try:
            self.logger.debug(f"Generating syllabus for course {course.code}")
            syllabus = self.content_generator.create_course_syllabus(course, professor)
            course.syllabus = syllabus
            self.logger.debug("Syllabus generation completed")
        except Exception as e:
            error_msg = f"Failed to generate syllabus: {str(e)}"
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg) from e

    def get_course(self, course_id: str) -> Course:
        """
        Get a course by ID.

        Args:
            course_id: ID of the course

        Returns:
            Course: The course object

        Raises:
            CourseNotFoundError: If course not found
        """
        course = self.repository.course.get(course_id)
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
        course = self.repository.course.get_by_code(course_code)
        if not course:
            error_msg = f"Course with code {course_code} not found"
            self.logger.error(error_msg)
            raise CourseNotFoundError(error_msg)
        return course

    def list_courses(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all courses with professor information.

        Args:
            department: Optional department to filter by

        Returns:
            List[Dict]: List of courses with professor information
        """
        self.logger.info(
            f"Listing courses{f' for department {department}' if department else ''}"
        )

        try:
            courses = self.repository.course.list(department)
            result = []

            for course in courses:
                professor = self.repository.professor.get(course.professor_id)
                result.append({"course": course, "professor": professor})

            self.logger.debug(f"Found {len(result)} courses")
            return result
        except Exception as e:
            error_msg = f"Failed to list courses: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def list_departments(self) -> List[Department]:
        """
        List all departments.

        Returns:
            List[Department]: List of departments
        """
        self.logger.debug("Listing departments")

        # In a complete implementation, would retrieve from database
        # For now, return placeholder data
        return [
            Department(
                id=1,
                name="Computer Science",
                code="CS",
                faculty="Science and Engineering",
                description="The Computer Science department focuses on the theory and practice of computation.",
            ),
            Department(
                id=2,
                name="Mathematics",
                code="MATH",
                faculty="Science and Engineering",
                description="The Mathematics department explores pure and applied mathematics.",
            ),
            Department(
                id=3,
                name="Statistics",
                code="STAT",
                faculty="Science and Engineering",
                description="Focuses on statistical theory and its applications to data analysis.",
            ),
        ]
