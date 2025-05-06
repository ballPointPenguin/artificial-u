"""
Lecture management service for ArtificialU.
"""

import logging
from typing import Any, Dict, List, Optional

from artificial_u.config import get_settings
from artificial_u.models.converters import (
    extract_xml_content,
    parse_lecture_xml,
    professor_model_to_dict,
)
from artificial_u.models.core import Lecture
from artificial_u.prompts import (
    get_lecture_prompt,
    get_system_prompt,
)
from artificial_u.utils import (
    ContentGenerationError,
    DatabaseError,
    LectureNotFoundError,
)


class LectureService:
    """Service for managing lecture entities."""

    def __init__(
        self,
        content_service,
        course_service,
        professor_service,
        repository_factory,
        logger=None,
    ):
        """
        Initialize the lecture service.

        Args:
            content_service: Content generation service
            course_service: Course management service
            professor_service: Professor management service
            repository_factory: Repository factory instance
            logger: Optional logger instance
        """
        self.content_service = content_service
        self.course_service = course_service
        self.professor_service = professor_service
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)

    # --- CRUD Methods --- #

    def create_lecture(
        self,
        title: str,
        course_id: int,
        week_number: int,
        order_in_week: int = 1,
        description: Optional[str] = None,
        content: Optional[str] = None,
        audio_url: Optional[str] = None,
        transcript_url: Optional[str] = None,
    ) -> Lecture:
        """
        Create a new lecture.

        Args:
            title: Lecture title
            course_id: ID of the course this lecture belongs to
            week_number: Week number in the course
            order_in_week: Order of the lecture within the week (default: 1)
            description: Optional lecture description
            content: Optional lecture content
            audio_url: Optional URL to audio content
            transcript_url: Optional URL to transcript content

        Returns:
            Lecture: The created lecture

        Raises:
            DatabaseError: If there's an error saving to the database
        """
        # Create lecture object
        lecture = Lecture(
            title=title,
            course_id=course_id,
            week_number=week_number,
            order_in_week=order_in_week,
            description=description,
            content=content,
            audio_url=audio_url,
            transcript_url=transcript_url,
        )

        try:
            # Save to database using repository
            created_lecture = self.repository_factory.lecture.create(lecture)
            self.logger.info(f"Created lecture: {title} for course {course_id}")
            return created_lecture
        except Exception as e:
            error_msg = f"Failed to create lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_lecture(self, lecture_id: int) -> Lecture:
        """
        Get a lecture by ID.

        Args:
            lecture_id: ID of the lecture

        Returns:
            Lecture: The lecture object

        Raises:
            LectureNotFoundError: If lecture not found
        """
        lecture = self.repository_factory.lecture.get(lecture_id)
        if not lecture:
            error_msg = f"Lecture with ID {lecture_id} not found"
            self.logger.error(error_msg)
            raise LectureNotFoundError(error_msg)
        return lecture

    def get_lecture_by_course_week_order(
        self, course_id: int, week_number: int, order_in_week: int
    ) -> Lecture:
        """
        Get a specific lecture by its position in a course.

        Args:
            course_id: ID of the course
            week_number: Week number in the course
            order_in_week: Order of the lecture within the week

        Returns:
            Lecture: The lecture object

        Raises:
            LectureNotFoundError: If lecture not found
        """
        lecture = self.repository_factory.lecture.get_by_course_week_order(
            course_id=course_id,
            week_number=week_number,
            order_in_week=order_in_week,
        )
        if not lecture:
            error_msg = (
                f"Lecture not found for course {course_id}, "
                f"week {week_number}, order {order_in_week}"
            )
            self.logger.error(error_msg)
            raise LectureNotFoundError(error_msg)
        return lecture

    def list_lectures(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List[Lecture]:
        """
        List lectures with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            course_id: Optional filter by course ID
            professor_id: Optional filter by professor ID
            search_query: Optional search in title/description

        Returns:
            List[Lecture]: List of lectures

        Raises:
            DatabaseError: If there's an error retrieving from the database
        """
        try:
            lectures = self.repository_factory.lecture.list(
                page=page,
                size=size,
                course_id=course_id,
                professor_id=professor_id,
                search_query=search_query,
            )
            self.logger.debug(f"Found {len(lectures)} lectures")
            return lectures
        except Exception as e:
            error_msg = f"Failed to list lectures: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def update_lecture(self, lecture_id: int, update_data: Dict[str, Any]) -> Lecture:
        """
        Update a lecture.

        Args:
            lecture_id: ID of the lecture to update
            update_data: Dictionary of fields to update

        Returns:
            Lecture: The updated lecture

        Raises:
            LectureNotFoundError: If lecture not found
            DatabaseError: If there's an error updating the database
        """
        # Get existing lecture
        lecture = self.get_lecture(lecture_id)

        # Update fields
        for key, value in update_data.items():
            if hasattr(lecture, key):
                setattr(lecture, key, value)
            else:
                self.logger.warning(f"Ignoring unknown field: {key}")

        try:
            # Save changes
            updated_lecture = self.repository_factory.lecture.update(lecture)
            self.logger.info(f"Updated lecture {lecture_id}")
            return updated_lecture
        except Exception as e:
            error_msg = f"Failed to update lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_lecture(self, lecture_id: int) -> bool:
        """
        Delete a lecture.

        Args:
            lecture_id: ID of the lecture to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            LectureNotFoundError: If lecture not found
            DatabaseError: If there's an error deleting from the database
        """
        # Check if lecture exists
        self.get_lecture(lecture_id)

        try:
            # Delete the lecture
            result = self.repository_factory.lecture.delete(lecture_id)
            if result:
                self.logger.info(f"Lecture {lecture_id} deleted successfully")
            return result
        except Exception as e:
            error_msg = f"Failed to delete lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    # --- Generation Methods --- #

    async def _prepare_prompt_arguments(
        self,
        partial_attributes: Dict[str, Any],
        professor_data: Dict[str, Any],
        existing_lectures: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Prepare arguments for the lecture generation prompt."""
        return {
            "professor_data": professor_data,
            "existing_lectures": existing_lectures,
            "partial_lecture_attrs": partial_attributes,
            "freeform_prompt": partial_attributes.get("freeform_prompt"),
            "word_count": partial_attributes.get("word_count", 2500),
        }

    async def _generate_and_parse_content(self, prompt_args: Dict[str, Any]) -> str:
        """Generate lecture content and parse the XML response."""
        lecture_prompt = get_lecture_prompt(**prompt_args)
        system_prompt = get_system_prompt("lecture")

        self.logger.info("Calling content service to generate lecture...")
        raw_response = await self.content_service.generate_text(
            model=get_settings().LECTURE_GENERATION_MODEL,
            prompt=lecture_prompt,
            system_prompt=system_prompt,
        )
        self.logger.info("Received response from content service.")

        # Extract XML content
        generated_xml_output = extract_xml_content(raw_response, "output")
        if not generated_xml_output:
            # Try to extract just the lecture tag content
            self.logger.info("Trying to extract <lecture> tag...")
            generated_xml_output = extract_xml_content(raw_response, "lecture")
            if not generated_xml_output:
                error_msg = (
                    f"Could not extract <output> or <lecture> tag from response:\n{raw_response}"
                )
                self.logger.error(error_msg)
                raise ContentGenerationError(error_msg)
            else:
                self.logger.warning("Extracted <lecture> tag directly as <output> was missing.")

        # Wrap the content in lecture tags if it's not already wrapped
        if not generated_xml_output.strip().startswith("<lecture>"):
            generated_xml_output = f"<lecture>\n{generated_xml_output}\n</lecture>"

        return generated_xml_output

    async def _process_models_for_generation(
        self, partial_attributes: Dict[str, Any]
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Process professor and existing lectures for generation."""
        # Get Professor
        professor_model = None
        course_id = partial_attributes.get("course_id")
        if course_id:
            try:
                course = self.course_service.get_course(course_id)
                if course and course.professor_id:
                    professor_model = self.professor_service.get_professor(course.professor_id)
            except Exception as e:
                self.logger.warning(f"Error fetching professor for course {course_id}: {e}")

        professor_dict = professor_model_to_dict(professor_model) if professor_model else {}

        # Get Existing Lectures for the course
        existing_lectures = []
        if course_id:
            try:
                lectures = self.repository_factory.lecture.list_by_course(course_id)
                existing_lectures = [
                    {
                        "title": lecture.title,
                        "description": lecture.description,
                        "week_number": lecture.week_number,
                        "order_in_week": lecture.order_in_week,
                    }
                    for lecture in lectures
                ]
            except Exception as e:
                self.logger.warning(f"Error fetching existing lectures for course {course_id}: {e}")

        return professor_dict, existing_lectures

    async def generate_lecture(
        self,
        partial_attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a lecture using AI based on partial attributes.

        Args:
            partial_attributes: Optional dictionary of known attributes to guide generation
                              or fill in the blanks.

        Returns:
            Dict[str, Any]: The generated lecture attributes.

        Raises:
            ContentGenerationError: If content generation or parsing fails.
        """
        partial_attributes = partial_attributes or {}
        self.logger.info(
            f"Generating lecture content with partial attributes: {list(partial_attributes.keys())}"
        )

        try:
            # Process models and prepare data for generation
            professor_dict, existing_lectures = await self._process_models_for_generation(
                partial_attributes
            )

            # Prepare prompt arguments
            prompt_args = await self._prepare_prompt_arguments(
                partial_attributes,
                professor_dict,
                existing_lectures,
            )

            # Generate and parse content
            generated_xml_output = await self._generate_and_parse_content(prompt_args)
            print(generated_xml_output)

            # Parse XML and combine with partial attributes
            parsed_lecture_data = parse_lecture_xml(generated_xml_output)
            final_lecture_data = {**parsed_lecture_data, **partial_attributes}

            # Remove non-lecture fields
            final_lecture_data.pop("freeform_prompt", None)
            final_lecture_data.pop("word_count", None)

            self.logger.info(f"Successfully generated lecture: {final_lecture_data.get('title')}")
            return final_lecture_data

        except ContentGenerationError:
            # Let content generation errors propagate up
            raise
        except ValueError as e:
            raise ContentGenerationError(f"Error generating/parsing lecture: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during lecture generation: {e}", exc_info=True)
            raise ContentGenerationError(f"An unexpected error occurred: {e}")
