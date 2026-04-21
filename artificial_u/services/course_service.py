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
        department_selector_service,
        professor_selector_service,
        job_enqueue_service=None,
        logger=None,
    ):
        """
        Initialize the course service.

        Args:
            repository_factory: Repository factory instance
            professor_service: Service for professor operations
            department_selector_service: Service for smart department selection
            professor_selector_service: Service for smart professor selection
            job_enqueue_service: Optional service for enqueueing background jobs (e.g. album art)
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.professor_service = professor_service
        self.department_selector_service = department_selector_service
        self.professor_selector_service = professor_selector_service
        self.job_enqueue_service = job_enqueue_service
        self.logger = logger or logging.getLogger(__name__)

    # --- CRUD Methods --- #

    async def create_course(
        self,
        title: str,
        code: str,
        level: str,
        weeks: int = 12,
        lectures_per_week: int = 1,
        department_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        description: Optional[str] = None,
        created_by: Optional[int] = None,
        created_with: Optional[str] = None,
    ) -> Tuple[Course, Professor]:
        """
        Create a new course with optional smart selection for department/professor.

        Args:
            title: Course title
            code: Course code (e.g., "CS101")
            level: Course level (Undergraduate, Graduate, etc.)
            weeks: Number of weeks in the course
            lectures_per_week: Number of lectures per week
            department_id: ID of existing department (will be selected if not provided)
            professor_id: ID of existing professor (will be selected if not provided)
            description: Course description

        Returns:
            Tuple: (Course, Professor) - The created course and its professor
        """
        self.logger.info(f"Creating new course: {code} - {title}")

        # Build course attributes for smart selection
        course_attributes = {
            "title": title,
            "code": code,
            "level": level,
            "description": description,
        }

        # Resolve department and professor IDs (with smart selection if needed)
        resolved_department_id = await self._resolve_department_id(department_id, course_attributes)
        resolved_professor_id = await self._resolve_professor_id(
            professor_id, course_attributes, resolved_department_id, created_by
        )

        # Get professor and create course
        professor = self._get_professor(resolved_professor_id)
        course = self._create_course_model(
            code,
            title,
            level,
            weeks,
            lectures_per_week,
            resolved_department_id,
            professor.id,
            description,
        )

        # Set attribution fields if provided
        course.created_by = created_by
        course.created_with = created_with

        # Save course
        return self._save_course(course, professor, code)

    async def _resolve_department_id(
        self, department_id: Optional[int], course_attributes: dict
    ) -> int:
        """Resolve department ID using smart selection if needed."""
        if department_id:
            return department_id

        self.logger.info("Department ID not provided, using smart selection")
        return await self.department_selector_service.resolve_department(course_attributes)

    async def _resolve_professor_id(
        self,
        professor_id: Optional[int],
        course_attributes: dict,
        department_id: int,
        created_by: Optional[int] = None,
    ) -> int:
        """Resolve professor ID using smart selection if needed."""
        if professor_id:
            return professor_id

        self.logger.info("Professor ID not provided, using smart selection")
        return await self.professor_selector_service.resolve_professor(
            course_attributes, department_id, created_by
        )

    def _get_professor(self, professor_id: int):
        """Get professor by ID with error handling."""
        try:
            professor = self.professor_service.get_professor(professor_id)
            if not professor:
                raise ProfessorNotFoundError(
                    f"Professor ID {professor_id} not found for course creation."
                )
            return professor
        except ProfessorNotFoundError as e:
            self.logger.error(f"Professor not found: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting professor {professor_id}: {e}")
            raise DatabaseError(f"Error retrieving professor {professor_id}")

    def _create_course_model(
        self,
        code: str,
        title: str,
        level: str,
        weeks: int,
        lectures_per_week: int,
        department_id: int,
        professor_id: int,
        description: Optional[str],
    ) -> Course:
        """Create Course model with given attributes."""
        return Course(
            code=code,
            title=title,
            department_id=department_id,
            level=level,
            professor_id=professor_id,
            description=description,
            total_weeks=weeks,
            lectures_per_week=lectures_per_week,
        )

    def _save_course(self, course: Course, professor, code: str) -> Tuple[Course, Any]:
        """Save course to database with error handling."""
        try:
            created_course = self.repository_factory.course.create(course)
            self.logger.info(f"Course created with ID: {created_course.id}")
            if self.job_enqueue_service:
                try:
                    if not getattr(created_course, "image_url", None):
                        self.job_enqueue_service.enqueue_course_image_generation(created_course.id)
                    else:
                        self.logger.debug(
                            "Skipping course image job on create: course %s already has image",
                            created_course.id,
                        )
                except Exception as bg_e:
                    self.logger.error(
                        "Failed to enqueue album art generation for course %s: %s",
                        created_course.id,
                        bg_e,
                        exc_info=True,
                    )
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
        List all courses with professor and student information, using repository factory.

        Args:
            department_id: Optional department ID to filter by.

        Returns:
            List[Dict]: List of courses with professor and student information.
        """
        self.logger.info(
            f"Listing courses{f' for department {department_id}' if department_id else ''}"
        )

        try:
            courses = self.repository_factory.course.list(department_id=department_id)
            result = []
            for course in courses:
                professor = None
                if course.professor_id:
                    professor = self.repository_factory.professor.get(course.professor_id)

                department = None
                if course.department_id:
                    department = self.repository_factory.department.get(course.department_id)

                student = None
                if course.created_by:
                    student = self.repository_factory.student.get(course.created_by)

                faculty_name = None
                if department and department.faculty_id:
                    faculty = self.repository_factory.faculty.get(department.faculty_id)
                    if faculty:
                        faculty_name = faculty.name

                result.append(
                    {
                        "course": course_model_to_dict(course),
                        "professor": professor_model_to_dict(professor) if professor else None,
                        "department": (
                            {
                                "id": department.id,
                                "name": department.name,
                                "code": department.code,
                                "faculty_id": department.faculty_id,
                                "faculty_name": faculty_name,
                            }
                            if department
                            else None
                        ),
                        "student": (
                            {
                                "id": student.id,
                                "name": student.name,
                                "email": student.email,
                            }
                            if student
                            else None
                        ),
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
