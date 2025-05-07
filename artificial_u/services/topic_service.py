"""
Topic management service for ArtificialU.
"""

import logging
from typing import Any, Dict, List, Optional

from artificial_u.config import get_settings
from artificial_u.models.converters import (
    course_model_to_dict,
    extract_xml_content,
    parse_topics_xml,
)
from artificial_u.models.core import Topic
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts import get_system_prompt, get_topics_prompt
from artificial_u.services.content_service import ContentService
from artificial_u.services.course_service import CourseService
from artificial_u.utils import ContentGenerationError, CourseNotFoundError, DatabaseError


class TopicService:
    """Service for managing topic entities."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        content_service: ContentService,
        course_service: CourseService,
        logger=None,
    ):
        """
        Initialize the topic service.

        Args:
            repository_factory: Repository factory instance
            content_service: Content generation service
            course_service: Course management service
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.content_service = content_service
        self.course_service = course_service
        self.logger = logger or logging.getLogger(__name__)

    # --- CRUD Methods --- #

    def create_topic(
        self,
        title: str,
        course_id: int,
        week: int,
        order: int,
    ) -> Topic:
        """
        Create a new topic.

        Args:
            title: Topic title
            course_id: ID of the course this topic belongs to
            week: Week number of the topic
            order: Order of the topic within the week

        Returns:
            Topic: The created topic

        Raises:
            DatabaseError: If there's an error saving to the database
        """
        self.logger.info(f"Creating new topic: {title} for course {course_id}")

        # Create topic object
        topic = Topic(
            title=title,
            course_id=course_id,
            week=week,
            order=order,
        )

        # Save to database
        try:
            topic = self.repository_factory.topic.create(topic)
            self.logger.info(f"Topic created with ID: {topic.id}")
            return topic
        except Exception as e:
            error_msg = f"Failed to save topic: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def create_topics(self, topics: List[Topic]) -> List[Topic]:
        """
        Create multiple topics in a single transaction.

        Args:
            topics: List of Topic objects to create

        Returns:
            List[Topic]: List of created topics

        Raises:
            DatabaseError: If there's an error saving to the database
        """
        self.logger.info(f"Creating {len(topics)} new topics")

        try:
            topics = self.repository_factory.topic.create_batch(topics)
            self.logger.info(f"Successfully created {len(topics)} topics")
            return topics
        except Exception as e:
            error_msg = f"Failed to save topics: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def get_topic(self, topic_id: int) -> Optional[Topic]:
        """
        Get a topic by ID.

        Args:
            topic_id: ID of the topic

        Returns:
            Optional[Topic]: The topic object if found, None otherwise
        """
        return self.repository_factory.topic.get(topic_id)

    def get_topic_by_course_week_order(
        self,
        course_id: int,
        week: int,
        order: int,
    ) -> Optional[Topic]:
        """
        Get a topic by course ID, week, and order.

        Args:
            course_id: ID of the course
            week: Week number
            order: Order within the week

        Returns:
            Optional[Topic]: The topic object if found, None otherwise
        """
        return self.repository_factory.topic.get_by_course_week_order(
            course_id=course_id,
            week=week,
            order=order,
        )

    def list_topics_by_course(self, course_id: int) -> List[Topic]:
        """
        List all topics for a specific course.

        Args:
            course_id: ID of the course

        Returns:
            List[Topic]: List of topics for the course

        Raises:
            DatabaseError: If there's an error retrieving from the database
        """
        try:
            topics = self.repository_factory.topic.list_by_course(course_id)
            self.logger.debug(f"Found {len(topics)} topics for course {course_id}")
            return topics
        except Exception as e:
            error_msg = f"Failed to list topics: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def list_topics_by_course_week(self, course_id: int, week: int) -> List[Topic]:
        """
        List all topics for a specific course and week.

        Args:
            course_id: ID of the course
            week: Week number

        Returns:
            List[Topic]: List of topics for the course and week

        Raises:
            DatabaseError: If there's an error retrieving from the database
        """
        try:
            topics = self.repository_factory.topic.list_by_course_week(course_id, week)
            self.logger.debug(f"Found {len(topics)} topics for course {course_id}, week {week}")
            return topics
        except Exception as e:
            error_msg = f"Failed to list topics: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def update_topic(self, topic: Topic) -> Topic:
        """
        Update a topic.

        Args:
            topic: Topic object with updated fields

        Returns:
            Topic: The updated topic

        Raises:
            DatabaseError: If there's an error updating the database
        """
        try:
            updated_topic = self.repository_factory.topic.update(topic)
            self.logger.info(f"Topic {topic.id} updated successfully")
            return updated_topic
        except Exception as e:
            error_msg = f"Failed to update topic: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_topic(self, topic_id: int) -> bool:
        """
        Delete a topic.

        Args:
            topic_id: ID of the topic to delete

        Returns:
            bool: True if deleted successfully, False if topic not found

        Raises:
            DatabaseError: If there's an error deleting from the database
        """
        try:
            result = self.repository_factory.topic.delete(topic_id)
            if result:
                self.logger.info(f"Topic {topic_id} deleted successfully")
            return result
        except Exception as e:
            error_msg = f"Failed to delete topic: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_topics_by_course(self, course_id: int) -> int:
        """
        Delete all topics for a specific course.

        Args:
            course_id: ID of the course whose topics should be deleted

        Returns:
            int: Number of topics deleted

        Raises:
            DatabaseError: If there's an error deleting from the database
        """
        try:
            count = self.repository_factory.topic.delete_by_course(course_id)
            self.logger.info(f"Deleted {count} topics for course {course_id}")
            return count
        except Exception as e:
            error_msg = f"Failed to delete topics: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    # --- Generation Methods --- #

    async def _generate_and_parse_topic_content(
        self, course_data: Dict[str, Any], freeform_prompt: Optional[str]
    ) -> str:
        """Generate topic content and parse the XML response."""
        topics_prompt = get_topics_prompt(course_data=course_data, freeform_prompt=freeform_prompt)
        system_prompt = get_system_prompt("topics")
        settings = get_settings()

        self.logger.info(
            f"Calling content service to generate topics for course ID: {course_data.get('id')}"
        )
        raw_response = await self.content_service.generate_text(
            model=settings.TOPICS_GENERATION_MODEL,
            prompt=topics_prompt,
            system_prompt=system_prompt,
        )
        self.logger.info("Received response from content service for topics.")

        # Extract XML content, trying <output> then <topics>
        generated_xml_output = extract_xml_content(raw_response, "output")
        if not generated_xml_output:
            self.logger.info("<output> tag not found, trying to extract <topics> tag directly...")
            # If <topics> is the root, extract_xml_content will get its *inner* content.
            # However, parse_topics_xml expects the full <topics>...</topics> string.
            # So we try to find <topics>, and if it's the root, we need to reconstruct it.
            # A simpler approach: if LLM returns <topics>...</topics> directly, use the raw_response
            # if it starts appropriately, or extract <topics> content and wrap.
            if "<topics>" in raw_response and "</topics>" in raw_response:
                # Attempt to extract the full <topics> block if it's not inside <output>
                # This assumes <topics> is a top-level or easily extractable block.
                start_index = raw_response.find("<topics>")
                end_index = raw_response.rfind("</topics>") + len("</topics>")
                if start_index != -1 and end_index != -1 and start_index < end_index:
                    generated_xml_output = raw_response[start_index:end_index]
                else:  # Fallback to trying to extract content and wrap
                    extracted_content = extract_xml_content(raw_response, "topics")
                    if extracted_content:
                        generated_xml_output = f"<topics>\n{extracted_content}\n</topics>"
            else:  # Final fallback: try to extract inner content and wrap it
                extracted_content = extract_xml_content(raw_response, "topics")
                if extracted_content:
                    generated_xml_output = f"<topics>\n{extracted_content}\n</topics>"

        if not generated_xml_output:
            error_msg = (
                f"Could not extract <output> or <topics> tag from response:\n"
                f"{raw_response[:500]}..."
            )
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg)

        # Ensure the extracted/formed content is properly wrapped for the parser
        if not generated_xml_output.strip().startswith("<topics>"):
            self.logger.warning(
                "Manually wrapping extracted content in <topics> tags as it was missing."
            )
            generated_xml_output = f"<topics>\n{generated_xml_output}\n</topics>"

        return generated_xml_output

    def _parse_convert_and_save_topics(
        self, generated_xml_output: str, course_id: int
    ) -> List[Topic]:
        """
        Parses XML topic data, converts to Topic models, and saves them to the DB.

        Args:
            generated_xml_output: The XML string containing topic data.
            course_id: The ID of the course these topics belong to.

        Returns:
            A list of created Topic objects.

        Raises:
            ContentGenerationError: If XML parsing fails.
            DatabaseError: If there's an error saving topics to the database.
        """
        try:
            parsed_topic_dicts = parse_topics_xml(generated_xml_output)
        except ValueError as e:  # Catch parsing errors specifically
            self.logger.error(f"XML parsing error for topics: {e}", exc_info=True)
            raise ContentGenerationError(f"Error parsing generated topic XML: {e}") from e

        if not parsed_topic_dicts:
            self.logger.warning(
                f"No topics were parsed from the generated XML for course {course_id}."
            )
            return []

        topic_models_to_create = []
        for topic_dict in parsed_topic_dicts:
            title = topic_dict.get("title")
            week = topic_dict.get("week")
            order = topic_dict.get("order")

            if not title or week is None or order is None:
                self.logger.warning(f"Skipping incomplete topic data: {topic_dict}")
                continue

            new_topic = Topic(
                title=title,
                course_id=course_id,
                week=week,
                order=order,
            )
            topic_models_to_create.append(new_topic)

        if not topic_models_to_create:
            self.logger.warning(f"No valid topics to create for course {course_id} after parsing.")
            return []

        # Batch create topics in the database (can raise DatabaseError)
        created_topics = self.repository_factory.topic.create_batch(topic_models_to_create)
        self.logger.info(
            f"Successfully saved {len(created_topics)} topics to DB for course {course_id}"
        )
        return created_topics

    async def generate_topics_for_course(
        self, course_id: int, freeform_prompt: Optional[str] = None
    ) -> List[Topic]:
        """
        Generate a list of topics for a course using AI.

        Args:
            course_id: ID of the course for which to generate topics.
            freeform_prompt: Optional freeform text to guide topic generation.

        Returns:
            List[Topic]: A list of created Topic objects.

        Raises:
            CourseNotFoundError: If the course with the given ID is not found.
            ContentGenerationError: If content generation or parsing fails.
            DatabaseError: If there's an error saving topics to the database.
        """
        self.logger.info(
            f"Generating topics for course ID: {course_id}, freeform: {bool(freeform_prompt)}"
        )

        try:
            # 1. Fetch Course data
            course_model = self.course_service.get_course(course_id)
            # get_course raises CourseNotFoundError if not found, so direct check not essential here
            course_data = course_model_to_dict(course_model)

            # 2. Generate XML content
            generated_xml_output = await self._generate_and_parse_topic_content(
                course_data, freeform_prompt
            )
            self.logger.debug(f"Generated XML for topics: {generated_xml_output[:500]}...")

            # 3. Parse XML, convert to Topic models, and save to DB
            created_topics = self._parse_convert_and_save_topics(generated_xml_output, course_id)

            self.logger.info(
                f"Overall success: generated and saved {len(created_topics)} topics for course "
                f"{course_id}"
            )
            return created_topics

        except CourseNotFoundError as e:
            self.logger.error(f"Error generating topics - course not found: {e}")
            raise
        except ContentGenerationError as e:
            self.logger.error(f"Content generation or parsing error for topics: {e}")
            raise
        # ValueError from parsing is now handled inside _parse_convert_and_save_topics
        # and raised as ContentGenerationError, so it's caught by the above.
        except DatabaseError as e:
            self.logger.error(f"Database error during topic generation: {e}")
            raise
        except Exception as e:
            log_message = f"Unexpected error during topic generation for course {course_id}: {e}"
            self.logger.error(log_message, exc_info=True)
            raise ContentGenerationError(
                f"An unexpected error occurred during topic generation: {e}"
            ) from e
