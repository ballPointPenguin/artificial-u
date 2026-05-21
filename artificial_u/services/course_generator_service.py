"""
Course generation service for ArtificialU.

This service handles all AI-powered course generation workflows,
separated from the core CRUD operations in CourseService.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from artificial_u.config import get_settings
from artificial_u.models.converters import (
    course_model_to_dict,
    department_model_to_dict,
    enrich_department_dict_with_faculty,
    extract_xml_content,
    parse_course_xml,
    professor_model_to_dict,
)
from artificial_u.models.core import Course, Department, Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts import (
    get_course_prompt,
    get_system_prompt,
)
from artificial_u.services.content_service import ContentService
from artificial_u.services.image_service import ImageService
from artificial_u.utils import (
    ContentGenerationError,
    DatabaseError,
    GenerationError,
    ProfessorNotFoundError,
)


class CourseGeneratorService:
    """Service for AI-powered course generation and related processing."""

    def __init__(
        self,
        course_service,
        professor_service,
        content_service: ContentService,
        image_service: ImageService,
        repository_factory: RepositoryFactory,
        job_enqueue_service,
        logger=None,
    ):
        """
        Initialize the course generator service.

        Args:
            course_service: Core course service for CRUD operations
            professor_service: Professor service for professor-related operations
            content_service: Content generation service
            repository_factory: Repository factory instance
            image_service: Image generation and storage service
            job_enqueue_service: Job enqueueing service for background tasks
            logger: Optional logger instance
        """
        self.course_service = course_service
        self.professor_service = professor_service
        self.content_service = content_service
        self.image_service = image_service
        self.repository_factory = repository_factory
        self.job_enqueue_service = job_enqueue_service
        self.logger = logger or logging.getLogger(__name__)

    async def generate_course(
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
        initial_partial_attributes = partial_attributes or {}
        self.logger.info(
            f"Generating course content with partial attributes: "
            f"{list(initial_partial_attributes.keys())}"
        )

        try:
            # 1. Process models and fetch existing courses
            (
                professor_model,
                department_model,
                existing_courses_dicts,
            ) = await self._process_models_for_generation(initial_partial_attributes)

            # 2. Prepare prompt arguments directly using models and initial attributes
            prompt_args = {
                # Convert models to dicts for XML generation within get_course_prompt
                "department_data": (
                    enrich_department_dict_with_faculty(
                        department_model_to_dict(department_model),
                        self.repository_factory,
                    )
                    if department_model
                    else {}
                ),
                "professor_data": (
                    professor_model_to_dict(professor_model) if professor_model else {}
                ),
                "existing_courses": existing_courses_dicts,
                "partial_course_attrs": initial_partial_attributes,  # Pass original partials
                "freeform_prompt": initial_partial_attributes.get("freeform_prompt"),
            }

            # 3. Generate and parse content
            generated_xml_output = await self._generate_and_parse_content(prompt_args)

            # 4. Parse XML response into a dictionary
            final_course_data = parse_course_xml(generated_xml_output)

            # 5. Add IDs from fetched models
            if professor_model:
                final_course_data["professor_id"] = professor_model.id
            if department_model:
                final_course_data["department_id"] = department_model.id

            # 6. Fill in missing values from initial partial attributes if they weren't generated
            for key, value in initial_partial_attributes.items():
                if key not in final_course_data or final_course_data[key] is None:
                    # Avoid re-adding 'topics' if it was in partial_attributes
                    if key != "topics":
                        final_course_data[key] = value

            # 7. Set created_with to the model used for generation
            settings = get_settings()
            final_course_data["created_with"] = settings.COURSE_GENERATION_MODEL

            # 8. Filter final dictionary to only include valid Course fields
            # Get valid fields from Course.__annotations__ or CourseModel.__table__.columns
            from artificial_u.models.database import CourseModel

            valid_course_keys = {c.name for c in CourseModel.__table__.columns}
            valid_course_keys.add("connected_course_ids")
            final_course_data = {
                k: v for k, v in final_course_data.items() if k in valid_course_keys
            }

            self.logger.info(
                f"Successfully generated course: "
                f"{final_course_data.get('code')} - {final_course_data.get('title')}"
            )
            return final_course_data

        except (DatabaseError, ContentGenerationError):
            # Let specific errors propagate up
            raise
        except ValueError as e:
            # Catch parsing errors etc. from converters
            self.logger.error(
                f"Error during course generation value processing: {e}", exc_info=True
            )
            raise ContentGenerationError(f"Error processing generated course data: {e}") from e
        except Exception as e:
            self.logger.error(f"Unexpected error during course generation: {e}", exc_info=True)
            raise ContentGenerationError(f"An unexpected error occurred: {e}") from e

    async def _generate_and_parse_content(self, prompt_args: Dict[str, Any]) -> str:
        """Generate course content and parse the XML response."""
        course_prompt = get_course_prompt(**prompt_args)
        system_prompt = get_system_prompt("course")
        settings = get_settings()

        self.logger.info("Calling content service to generate course...")
        raw_response = await self.content_service.generate_text(
            model=settings.COURSE_GENERATION_MODEL,
            prompt=course_prompt,
            system_prompt=system_prompt,
        )
        self.logger.info("Received response from content service.")

        # Simplified XML extraction logic
        generated_xml_output = None

        # First try to extract from <output> tags
        generated_xml_output = extract_xml_content(raw_response, "output")
        if generated_xml_output:
            self.logger.info("Successfully extracted content from <output> tags")
        else:
            self.logger.info("<output> tag not found, trying direct <course> extraction...")

            # Check if the response directly contains <course>...</course>
            if raw_response.strip().startswith("<course>") and raw_response.strip().endswith(
                "</course>"
            ):
                # Use the raw response directly
                generated_xml_output = raw_response.strip()
                self.logger.info("Using raw response as it contains valid <course> structure")
            else:
                # Try to extract inner content and wrap it
                inner_content = extract_xml_content(raw_response, "course")
                if inner_content:
                    generated_xml_output = f"<course>\n{inner_content}\n</course>"
                    self.logger.info("Extracted <course> inner content and wrapped it")

        if not generated_xml_output:
            error_msg = f"Could not extract <output> or <course> tag from response:\n{raw_response}"
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg)

        return generated_xml_output

    async def _process_models_for_generation(
        self, partial_attributes: Dict[str, Any]
    ) -> Tuple[Optional[Professor], Optional[Department], List[Dict[str, Any]]]:
        """Process professor, department, and existing courses for generation.

        Returns:
            Tuple: (Professor model, Department model, List of existing course dicts)
        """
        # 1. Get Professor
        professor_model = await self._get_professor(partial_attributes)

        # 2. Get Department
        department_model = await self._get_department(partial_attributes, professor_model)

        # 3. Get Existing Courses as dictionaries
        existing_courses_models = await self._get_existing_courses(department_model)
        existing_courses_dicts = [course_model_to_dict(c) for c in existing_courses_models]

        return (
            professor_model,
            department_model,
            existing_courses_dicts,
        )

    # --- Helper Methods for Fetching Data (using Repository) --- #

    async def _get_professor(self, partial_attributes: Dict[str, Any]) -> Optional[Professor]:
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
        professor: Optional[Professor] = None,
    ) -> Optional[Department]:
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

    async def _get_existing_courses(self, department: Optional[Department]) -> List[Course]:
        """Fetches existing courses for a given department using the repository.

        If no department is provided, returns the 20 most recent courses from any department
        (determined by highest course.id values).
        """
        try:
            if not department:
                # Return 20 most recent courses from any department
                self.logger.info(
                    "No department provided, fetching 20 most recent courses from any department"
                )
                return self.repository_factory.course.list_recent(limit=20)
            else:
                # Use the repository directly for department-specific courses
                return self.repository_factory.course.list(department_id=department.id)
        except Exception as e:
            if department:
                self.logger.error(
                    f"Repository error fetching courses for department {department.id}: {e}",
                    exc_info=True,
                )
                raise DatabaseError(
                    f"Error fetching courses for department {department.id} from repository."
                ) from e
            else:
                self.logger.error(
                    f"Repository error fetching recent courses: {e}",
                    exc_info=True,
                )
                raise DatabaseError("Error fetching recent courses from repository.") from e

    async def generate_and_set_course_image(
        self, course_id: int, aspect_ratio: str = "1:1"
    ) -> Course:
        """
        Generate album art for a course and persist image_url / image_created_with.

        Args:
            course_id: Course primary key
            aspect_ratio: Image aspect ratio (default 1:1 for MP3 / UI thumbnails)

        Returns:
            Updated Course model

        Raises:
            CourseNotFoundError: If the course does not exist
            GenerationError: If generation or persistence fails
        """
        self.logger.info(f"Generating album art for course ID: {course_id}")

        course = self.course_service.get_course(course_id)

        professor = None
        if course.professor_id:
            try:
                professor = self.professor_service.get_professor(course.professor_id)
            except ProfessorNotFoundError:
                self.logger.warning(
                    "Professor %s not found; course image prompt will omit optional credits",
                    course.professor_id,
                )

        try:
            result = await self.image_service.generate_course_image(
                course=course,
                professor=professor,
                aspect_ratio=aspect_ratio,
            )
        except Exception as e:
            self.logger.error(
                f"Image generation step failed for course {course_id}: {e}",
                exc_info=True,
            )
            raise GenerationError(f"Failed to generate image for course {course_id}") from e

        image_key = self._validate_course_image_result(result, course_id)
        image_url = self._get_course_image_url_from_key(image_key, course_id)

        settings = get_settings()
        try:
            updated = self.course_service.update_course(
                course_id,
                {
                    "image_url": image_url,
                    "image_created_with": settings.IMAGE_GENERATION_MODEL,
                },
            )
            self.logger.info(
                f"Course {course_id} updated with album art (model: {settings.IMAGE_GENERATION_MODEL})."
            )
            return updated
        except Exception as e:
            self.logger.error(f"Failed to update course {course_id} with image URL: {e}")
            raise

    def _validate_course_image_result(self, result, course_id: int) -> str:
        """Validate image generation result and return the storage key."""
        if not result.success:
            error_msg = f"Image generation failed for course {course_id}"
            if result.error:
                error_msg += f": {result.error.error_type.value} - {result.error}"
                if result.error.backend:
                    error_msg += f" (backend: {result.error.backend})"
            self.logger.error(error_msg)
            raise GenerationError(error_msg)

        if not result.image_keys:
            self.logger.error(
                f"Image generation succeeded but returned no keys for course {course_id}"
            )
            raise GenerationError(
                f"Image generation succeeded but yielded no result for course {course_id}"
            )

        return result.image_keys[0]

    def _get_course_image_url_from_key(self, image_key: str, course_id: int) -> str:
        """Build public URL for a stored image object key."""
        try:
            bucket = self.image_service.storage_service.images_bucket
            image_url = self.image_service.storage_service.get_file_url(
                bucket=bucket, object_name=image_key
            )
            self.logger.info(f"Image URL for course {course_id}: {image_url}")
            return image_url
        except Exception as e:
            self.logger.error(f"Failed to get image URL for key {image_key}: {e}", exc_info=True)
            raise GenerationError(f"Failed to construct image URL for course {course_id}") from e
