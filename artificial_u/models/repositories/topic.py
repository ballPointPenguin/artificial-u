"""
Topic repository for database operations.
"""

from typing import List, Optional

from artificial_u.models.core import Topic
from artificial_u.models.database import TopicModel
from artificial_u.models.repositories.base import BaseRepository


class TopicRepository(BaseRepository):
    """Repository for Topic operations."""

    def create(self, topic: Topic) -> Topic:
        """Create a new topic."""
        with self.get_session() as session:
            db_topic = TopicModel(
                title=topic.title,
                order=topic.order,
                week=topic.week,
                course_id=topic.course_id,
            )

            session.add(db_topic)
            session.commit()
            session.refresh(db_topic)

            topic.id = db_topic.id
            return topic

    def create_batch(self, topics: List[Topic]) -> List[Topic]:
        """
        Create multiple topics in a single transaction.

        Args:
            topics: List of Topic models to create

        Returns:
            List of created Topic models with their IDs populated
        """
        with self.get_session() as session:
            db_topics = [
                TopicModel(
                    title=topic.title,
                    order=topic.order,
                    week=topic.week,
                    course_id=topic.course_id,
                )
                for topic in topics
            ]

            session.add_all(db_topics)
            session.commit()

            # Refresh all topics to get their IDs
            for db_topic in db_topics:
                session.refresh(db_topic)

            # Update the original topic objects with their new IDs
            for topic, db_topic in zip(topics, db_topics):
                topic.id = db_topic.id

            return topics

    def get(self, topic_id: int) -> Optional[Topic]:
        """Get a topic by ID."""
        with self.get_session() as session:
            db_topic = session.query(TopicModel).filter_by(id=topic_id).first()

            if not db_topic:
                return None

            return Topic(
                id=db_topic.id,
                title=db_topic.title,
                order=db_topic.order,
                week=db_topic.week,
                course_id=db_topic.course_id,
            )

    def get_by_course_week_order(self, course_id: int, week: int, order: int) -> Optional[Topic]:
        """Get a topic by course ID, week, and order."""
        with self.get_session() as session:
            db_topic = (
                session.query(TopicModel)
                .filter_by(course_id=course_id, week=week, order=order)
                .first()
            )

            if not db_topic:
                return None

            return Topic(
                id=db_topic.id,
                title=db_topic.title,
                order=db_topic.order,
                week=db_topic.week,
                course_id=db_topic.course_id,
            )

    def list_by_course(self, course_id: int) -> List[Topic]:
        """List all topics for a specific course."""
        with self.get_session() as session:
            db_topics = (
                session.query(TopicModel)
                .filter_by(course_id=course_id)
                .order_by(TopicModel.week, TopicModel.order)
                .all()
            )

            return [
                Topic(
                    id=t.id,
                    title=t.title,
                    order=t.order,
                    week=t.week,
                    course_id=t.course_id,
                )
                for t in db_topics
            ]

    def list_by_course_week(self, course_id: int, week: int) -> List[Topic]:
        """List all topics for a specific course and week."""
        with self.get_session() as session:
            db_topics = (
                session.query(TopicModel)
                .filter_by(course_id=course_id, week=week)
                .order_by(TopicModel.order)
                .all()
            )

            return [
                Topic(
                    id=t.id,
                    title=t.title,
                    order=t.order,
                    week=t.week,
                    course_id=t.course_id,
                )
                for t in db_topics
            ]

    def update(self, topic: Topic) -> Topic:
        """Update an existing topic."""
        with self.get_session() as session:
            db_topic = session.query(TopicModel).filter_by(id=topic.id).first()

            if not db_topic:
                raise ValueError(f"Topic with ID {topic.id} not found")

            # Update fields
            db_topic.title = topic.title
            db_topic.order = topic.order
            db_topic.week = topic.week
            db_topic.course_id = topic.course_id

            session.commit()
            return topic

    def delete(self, topic_id: int) -> bool:
        """
        Delete a topic by ID.

        Args:
            topic_id: ID of the topic to delete

        Returns:
            True if deleted successfully, False if topic not found
        """
        with self.get_session() as session:
            db_topic = session.query(TopicModel).filter_by(id=topic_id).first()

            if not db_topic:
                return False

            session.delete(db_topic)
            session.commit()
            return True

    def delete_by_course(self, course_id: int) -> int:
        """
        Delete all topics for a specific course.

        Args:
            course_id: ID of the course whose topics should be deleted

        Returns:
            Number of topics deleted
        """
        with self.get_session() as session:
            result = session.query(TopicModel).filter_by(course_id=course_id).delete()
            session.commit()
            return result
