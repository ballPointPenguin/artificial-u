"""
Topic management service for ArtificialU.
"""

import logging
from typing import List, Optional

from artificial_u.models.core import Topic
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.utils import DatabaseError


class TopicService:
    """Service for managing topic entities."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        logger=None,
    ):
        """
        Initialize the topic service.

        Args:
            repository_factory: Repository factory instance
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
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
