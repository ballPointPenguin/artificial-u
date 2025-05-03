"""
Course management service for ArtificialU.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from artificial_u.config import settings
from artificial_u.config.defaults import DEFAULT_COURSE_WEEKS, DEFAULT_LECTURES_PER_WEEK
from artificial_u.models.converters import (
    course_model_to_dict,
    department_model_to_dict,
    department_to_xml,
    parse_course_xml,
    professor_model_to_dict,
    professor_to_xml,
)
from artificial_u.models.database import CourseModel, DepartmentModel, ProfessorModel

# Import RepositoryFactory directly instead of legacy Repository wrapper
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts.base import extract_xml_content
from artificial_u.prompts.courses import get_course_prompt
from artificial_u.prompts.system import get_system_prompt
from artificial_u.services.content_service import ContentService
from artificial_u.services.professor_service import ProfessorService
from artificial_u.utils.exceptions import (
    ContentGenerationError,
    CourseNotFoundError,
    DatabaseError,
    ProfessorNotFoundError,
)


class CourseService:
    """Service for managing course entities."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        professor_service: ProfessorService,
        content_service: ContentService,
        logger=None,
    ):
        """
        Initialize the course service.

        Args:
            repository_factory: Repository factory instance
            professor_service: Service for professor operations
            content_service: Service for content generation
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.professor_service = professor_service  # Needed for create_course
        self.content_service = content_service
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
        weeks: int = DEFAULT_COURSE_WEEKS,
        lectures_per_week: int = DEFAULT_LECTURES_PER_WEEK,
        topics: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[CourseModel, ProfessorModel]:
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
            topics: Optional pre-defined topics structure

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
        course = CourseModel(
            code=code,
            title=title,
            department_id=department_id,
            level=level,
            professor_id=professor.id,
            description=description,
            credits=credits,
            total_weeks=weeks,
            lectures_per_week=lectures_per_week,
            topics=topics,
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

    def get_course(self, course_id: int) -> CourseModel:
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

    def get_course_by_code(self, course_code: str) -> CourseModel:
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

    def update_course(self, course_id: int, update_data: Dict[str, Any]) -> CourseModel:
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

    # --- Generation Methods --- #

    async def _prepare_prompt_arguments(
        self,
        partial_attributes: Dict[str, Any],
        professor_xml: str,
        department_xml: str,
        existing_courses_dicts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Prepare arguments for the course generation prompt."""
        return {
            "course_title": partial_attributes.get("title", "[GENERATE]"),
            "course_code": partial_attributes.get("code", "[GENERATE]"),
            "course_description": partial_attributes.get("description", "[GENERATE]"),
            "course_level": partial_attributes.get("level", "[GENERATE]"),
            "course_credits": partial_attributes.get("credits", "[GENERATE]"),
            "lectures_per_week": partial_attributes.get(
                "lectures_per_week", DEFAULT_LECTURES_PER_WEEK
            ),
            "total_weeks": partial_attributes.get("total_weeks", DEFAULT_COURSE_WEEKS),
            "department_xml": department_xml,
            "professor_xml": professor_xml,
            "existing_courses": existing_courses_dicts,
            "topics": partial_attributes.get("topics"),
            "freeform_prompt": partial_attributes.get("freeform_prompt"),
        }

    async def _generate_and_parse_content(self, prompt_args: Dict[str, Any]) -> str:
        """Generate course content and parse the XML response."""
        course_prompt = get_course_prompt(**prompt_args)
        system_prompt = get_system_prompt("course")

        self.logger.info("Calling content service to generate course...")
        raw_response = await self.content_service.generate_text(
            model=settings.COURSE_GENERATION_MODEL,
            prompt=course_prompt,
            system_prompt=system_prompt,
        )
        self.logger.info("Received response from content service.")

        # Extract XML content
        generated_xml_output = extract_xml_content(raw_response, "output")
        if not generated_xml_output:
            generated_xml_output = extract_xml_content(raw_response, "course")
            if not generated_xml_output:
                self.logger.error(
                    f"Could not extract <output> or <course> tag from response:\n{raw_response}"
                )
                raise ContentGenerationError(
                    "AI response missing expected <output> or <course> tag."
                )
            else:
                self.logger.warning("Extracted <course> tag directly as <output> was missing.")

        return generated_xml_output

    async def _process_models_for_generation(
        self, partial_attributes: Dict[str, Any]
    ) -> Tuple[Optional[ProfessorModel], Optional[DepartmentModel], List[Dict[str, Any]]]:
        """Process professor, department, and existing courses for generation."""
        # 1. Get Professor
        professor_model = await self._get_professor(partial_attributes)
        professor_dict = professor_model_to_dict(professor_model) if professor_model else {}
        professor_xml = professor_to_xml(professor_dict)

        # 2. Get Department
        department_model = await self._get_department(partial_attributes, professor_model)
        department_dict = department_model_to_dict(department_model) if department_model else {}
        department_xml = department_to_xml(department_dict)
        if department_model:
            partial_attributes.setdefault("department_id", department_model.id)

        # 3. Get Existing Courses
        existing_courses_models = await self._get_existing_courses(department_model)
        existing_courses_dicts = []
        for c in existing_courses_models:
            course_dict = course_model_to_dict(c)
            # Extract topic titles for the XML converter's current format
            course_dict["topics"] = [t.title for t in c.lectures] if c.lectures else []
            existing_courses_dicts.append(course_dict)

        return (
            professor_model,
            department_model,
            professor_xml,
            department_xml,
            existing_courses_dicts,
        )

    async def generate_course_content(
        self,
        partial_attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a course using centralized converters and repository.

        Args:
            partial_attributes: Optional dictionary of known attributes to guide generation
                                or fill in the blanks.

        Returns:
            Dict[str, Any]: The generated course attributes (including topics).

        Raises:
            DatabaseError: If there's an error fetching prerequisites.
            ContentGenerationError: If content generation or parsing fails.
        """
        partial_attributes = partial_attributes or {}
        self.logger.info(
            f"Generating course content with partial attributes: {list(partial_attributes.keys())}"
        )

        try:
            # Process models and prepare data for generation
            (
                professor_model,
                department_model,
                professor_xml,
                department_xml,
                existing_courses_dicts,
            ) = await self._process_models_for_generation(partial_attributes)

            # Prepare prompt arguments
            prompt_args = self._prepare_prompt_arguments(
                partial_attributes,
                professor_xml,
                department_xml,
                existing_courses_dicts,
            )

            # Generate and parse content
            generated_xml_output = await self._generate_and_parse_content(prompt_args)

            # Parse XML and combine with partial attributes
            parsed_course_data = parse_course_xml(generated_xml_output)
            final_course_data = {**parsed_course_data, **partial_attributes}

            # Add IDs from models
            if professor_model:
                final_course_data["professor_id"] = professor_model.id
            if department_model:
                final_course_data["department_id"] = department_model.id

            # Remove non-course fields
            final_course_data.pop("freeform_prompt", None)

            self.logger.info(
                f"Successfully generated course: "
                f"{final_course_data.get('code')} - {final_course_data.get('title')}"
            )
            return final_course_data

        except DatabaseError:
            # Let database errors propagate up
            raise
        except ContentGenerationError:
            # Let content generation errors propagate up
            raise
        except ValueError as e:
            raise ContentGenerationError(f"Error generating/parsing course: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during course generation: {e}", exc_info=True)
            raise ContentGenerationError(f"An unexpected error occurred: {e}")

    # --- Helper Methods for Fetching Data (using Repository) --- #

    async def _get_professor(self, partial_attributes: Dict[str, Any]) -> Optional[ProfessorModel]:
        """Fetches professor DB model based on ID if provided, using repository."""
        professor_id = partial_attributes.get("professor_id")
        if not professor_id:
            self.logger.warning("No professor_id provided for course generation.")
            return None
        try:
            # Use the repository directly
            professor = self.repository_factory.professor.get(professor_id)
            if not professor:
                self.logger.error(f"Professor with ID {professor_id} not found via repository.")
                # Raise DatabaseError or ProfessorNotFound? Let's stick to DatabaseError
                # for lookup failures.
                raise DatabaseError(f"Professor with ID {professor_id} not found.")
            return professor
        except Exception as e:
            self.logger.error(
                f"Repository error fetching professor {professor_id}: {e}",
                exc_info=True,
            )
            # Propagate as DatabaseError
            raise DatabaseError(f"Error fetching professor {professor_id} from repository.") from e

    async def _get_department(
        self,
        partial_attributes: Dict[str, Any],
        professor: Optional[ProfessorModel] = None,
    ) -> Optional[DepartmentModel]:
        """Fetches department DB model based on ID or professor's department, using repository."""
        department_id = partial_attributes.get("department_id")

        if not department_id and professor and professor.department_id:
            department_id = professor.department_id
            self.logger.info(f"Using department ID {department_id} from professor {professor.id}")
        elif not department_id:
            self.logger.warning("No department_id provided or derivable for course generation.")
            return None

        try:
            # Use the repository directly
            department = self.repository_factory.department.get(department_id)
            if not department:
                self.logger.error(f"Department with ID {department_id} not found via repository.")
                raise DatabaseError(f"Department with ID {department_id} not found.")
            return department
        except Exception as e:
            self.logger.error(
                f"Repository error fetching department {department_id}: {e}",
                exc_info=True,
            )
            raise DatabaseError(
                f"Error fetching department {department_id} from repository."
            ) from e

    async def _get_existing_courses(
        self, department: Optional[DepartmentModel]
    ) -> List[CourseModel]:
        """Fetches existing courses for a given department using the repository."""
        if not department:
            return []
        try:
            # Use the repository directly
            # Assumes CourseRepository.list handles potential None department_id
            # if department is None and eager loads lectures as needed
            return self.repository_factory.course.list(department_id=department.id)
        except Exception as e:
            self.logger.error(
                f"Repository error fetching courses for department {department.id}: {e}",
                exc_info=True,
            )
            raise DatabaseError(
                f"Error fetching courses for department {department.id} from repository."
            ) from e
