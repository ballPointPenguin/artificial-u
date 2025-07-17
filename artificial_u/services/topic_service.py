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
    topics_model_to_dict,
    topics_to_xml,
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
        content: Optional[Dict[str, Any]] = None,
    ) -> Topic:
        """
        Create a new topic.

        Args:
            title: Topic title
            course_id: ID of the course this topic belongs to
            week: Week number of the topic
            order: Order of the topic within the week
            content: Optional content dictionary for the topic

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
            content=content,
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
        self,
        course_data: Dict[str, Any],
        freeform_prompt: Optional[str],
        existing_topics_xml: Optional[str] = None,
    ) -> str:
        """Generate topic content and parse the XML response."""
        topics_prompt = get_topics_prompt(
            course_data=course_data,
            freeform_prompt=freeform_prompt,
            existing_topics_xml=existing_topics_xml,
        )
        system_prompt = get_system_prompt("topics")
        settings = get_settings()

        self.logger.info(
            f"Calling content service to generate topics for course ID: {course_data.get('id')}"
        )
        raw_response = await self.content_service.generate_text(
            model=settings.TOPICS_GENERATION_MODEL,
            prompt=topics_prompt,
            system_prompt=system_prompt,
            max_tokens=6144,  # Higher limit for topics generation to avoid truncation
        )
        self.logger.info("Received response from content service for topics.")

        # Simplified XML extraction logic
        generated_xml_output = None

        # First try to extract from <output> tags
        generated_xml_output = extract_xml_content(raw_response, "output")
        if generated_xml_output:
            self.logger.info("Successfully extracted content from <output> tags")
        else:
            self.logger.info("<output> tag not found, trying direct <topics> extraction...")

            # Check if the response directly contains <topics>...</topics>
            if raw_response.strip().startswith("<topics>") and raw_response.strip().endswith(
                "</topics>"
            ):
                # Use the raw response directly
                generated_xml_output = raw_response.strip()
                self.logger.info("Using raw response as it contains valid <topics> structure")
            else:
                # Try to extract inner content and wrap it
                inner_content = extract_xml_content(raw_response, "topics")
                if inner_content:
                    generated_xml_output = f"<topics>\n{inner_content}\n</topics>"
                    self.logger.info("Extracted <topics> inner content and wrapped it")

        if not generated_xml_output:
            error_msg = (
                f"Could not extract <output> or <topics> tag from response:\n"
                f"{raw_response[:500]}..."
            )
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg)

        # Ensure the extracted content has the proper <topics> wrapper
        if not generated_xml_output.strip().startswith("<topics>"):
            self.logger.warning("Wrapping extracted content in <topics> tags")
            generated_xml_output = f"<topics>\n{generated_xml_output}\n</topics>"

        return generated_xml_output

    def _parse_convert_and_save_topics(
        self, generated_xml_output: str, course_id: int
    ) -> List[Topic]:
        """
        Parses XML topic data, converts to Topic models, and saves them to the DB.
        If generated topics have the same course_id + week + order as existing topics,
        the existing topics will be replaced with the generated ones.

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
        replaced_topics_count = 0

        for topic_dict in parsed_topic_dicts:
            title = topic_dict.get("title")
            week = topic_dict.get("week")
            order = topic_dict.get("order")

            if not title or week is None or order is None:
                self.logger.warning(f"Skipping incomplete topic data: {topic_dict}")
                continue

            # Check if there's an existing topic with the same course_id + week + order
            existing_topic = self.repository_factory.topic.get_by_course_week_order(
                course_id=course_id, week=week, order=order
            )

            if existing_topic:
                # Delete the existing topic to avoid constraint violation
                self.logger.info(
                    f"Replacing existing topic '{existing_topic.title}' "
                    f"(course={course_id}, week={week}, order={order}) "
                    f"with new topic '{title}'"
                )
                self.repository_factory.topic.delete(existing_topic.id)
                replaced_topics_count += 1

            new_topic = Topic(
                title=title,
                course_id=course_id,
                week=week,
                order=order,
                content=topic_dict.get("content"),
            )
            topic_models_to_create.append(new_topic)

        if not topic_models_to_create:
            self.logger.warning(f"No valid topics to create for course {course_id} after parsing.")
            return []

        # Batch create topics in the database (can raise DatabaseError)
        created_topics = self.repository_factory.topic.create_batch(topic_models_to_create)

        if replaced_topics_count > 0:
            self.logger.info(
                f"Successfully replaced {replaced_topics_count} existing topics and "
                f"created {len(created_topics)} topics for course {course_id}"
            )
        else:
            self.logger.info(
                f"Successfully created {len(created_topics)} new topics for course {course_id}"
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

            # 2. Fetch existing topics for context
            existing_topics = self.list_topics_by_course(course_id)
            existing_topics_xml = None

            if existing_topics:
                self.logger.info(
                    f"Found {len(existing_topics)} existing topics for course {course_id}"
                )
                existing_topics_dicts = topics_model_to_dict(existing_topics)
                existing_topics_xml = topics_to_xml(existing_topics_dicts)
                self.logger.debug(f"Existing topics XML: {existing_topics_xml}")
            else:
                self.logger.info(f"No existing topics found for course {course_id}")

            # 3. Generate XML content
            generated_xml_output = await self._generate_and_parse_topic_content(
                course_data, freeform_prompt, existing_topics_xml
            )
            self.logger.debug(f"Generated XML for topics: {generated_xml_output[:500]}...")

            # 4. Parse XML, convert to Topic models, and save to DB
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
