"""
Unit tests for TopicRepository.
"""

from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Topic
from artificial_u.models.database import TopicModel
from artificial_u.models.repositories.topic import TopicRepository


@pytest.mark.unit
class TestTopicRepository:
    """Test the TopicRepository class."""

    @pytest.fixture
    def topic_repository(self, repository_with_session):
        """Create a TopicRepository with a mock session."""
        return repository_with_session(TopicRepository)

    @pytest.fixture
    def mock_topic_model(self):
        """Create a mock topic model for testing."""
        mock_topic = MagicMock(spec=TopicModel)
        mock_topic.id = 1
        mock_topic.title = "Introduction to Python"
        mock_topic.order = 1
        mock_topic.week = 1
        mock_topic.course_id = 1
        return mock_topic

    def test_create(self, topic_repository, mock_session):
        """Test creating a topic."""

        # Configure mock behaviors
        def mock_refresh(model):
            model.id = 1

        mock_session.refresh.side_effect = mock_refresh

        # Create topic to test
        topic = Topic(
            title="Introduction to Python",
            order=1,
            week=1,
            course_id=1,
        )

        # Exercise
        result = topic_repository.create(topic)

        # Verify
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called
        assert result.id == 1
        assert result.title == "Introduction to Python"
        assert result.order == 1
        assert result.week == 1
        assert result.course_id == 1

    def test_create_batch(self, topic_repository, mock_session):
        """Test creating multiple topics in a batch."""

        # Configure mock behaviors
        def mock_refresh(model):
            model.id = 1 if model.title == "Topic 1" else 2

        mock_session.refresh.side_effect = mock_refresh

        # Create topics to test
        topics = [
            Topic(title="Topic 1", order=1, week=1, course_id=1),
            Topic(title="Topic 2", order=2, week=1, course_id=1),
        ]

        # Exercise
        result = topic_repository.create_batch(topics)

        # Verify
        assert mock_session.add_all.called
        assert mock_session.commit.called
        assert mock_session.refresh.call_count == 2
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        assert result[0].title == "Topic 1"
        assert result[1].title == "Topic 2"

    def test_get(self, topic_repository, mock_session, mock_topic_model):
        """Test getting a topic by ID."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_topic_model

        # Exercise
        result = topic_repository.get(1)

        # Verify
        mock_session.query.assert_called_once_with(TopicModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        assert result.id == 1
        assert result.title == "Introduction to Python"
        assert result.order == 1
        assert result.week == 1
        assert result.course_id == 1

    def test_get_not_found(self, topic_repository, mock_session):
        """Test getting a non-existent topic returns None."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Exercise
        result = topic_repository.get(999)

        # Verify
        assert result is None

    def test_get_by_course_week_order(self, topic_repository, mock_session, mock_topic_model):
        """Test getting a topic by course ID, week, and order."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_topic_model

        # Exercise
        result = topic_repository.get_by_course_week_order(1, 1, 1)

        # Verify
        mock_session.query.assert_called_once_with(TopicModel)
        query_mock.filter_by.assert_called_once_with(course_id=1, week=1, order=1)
        assert result.id == 1
        assert result.title == "Introduction to Python"
        assert result.order == 1
        assert result.week == 1
        assert result.course_id == 1

    def test_list_by_course(self, topic_repository, mock_session):
        """Test listing topics by course."""
        # Configure mock behavior
        mock_topic1 = MagicMock(spec=TopicModel)
        mock_topic1.id = 1
        mock_topic1.title = "Topic 1"
        mock_topic1.order = 1
        mock_topic1.week = 1
        mock_topic1.course_id = 1

        mock_topic2 = MagicMock(spec=TopicModel)
        mock_topic2.id = 2
        mock_topic2.title = "Topic 2"
        mock_topic2.order = 2
        mock_topic2.week = 1
        mock_topic2.course_id = 1

        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.order_by.return_value.all.return_value = [
            mock_topic1,
            mock_topic2,
        ]

        # Exercise
        result = topic_repository.list_by_course(1)

        # Verify
        mock_session.query.assert_called_once_with(TopicModel)
        query_mock.filter_by.assert_called_once_with(course_id=1)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].title == "Topic 1"
        assert result[1].id == 2
        assert result[1].title == "Topic 2"

    def test_list_by_course_week(self, topic_repository, mock_session):
        """Test listing topics by course and week."""
        # Configure mock behavior
        mock_topic1 = MagicMock(spec=TopicModel)
        mock_topic1.id = 1
        mock_topic1.title = "Topic 1"
        mock_topic1.order = 1
        mock_topic1.week = 1
        mock_topic1.course_id = 1

        mock_topic2 = MagicMock(spec=TopicModel)
        mock_topic2.id = 2
        mock_topic2.title = "Topic 2"
        mock_topic2.order = 2
        mock_topic2.week = 1
        mock_topic2.course_id = 1

        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.order_by.return_value.all.return_value = [
            mock_topic1,
            mock_topic2,
        ]

        # Exercise
        result = topic_repository.list_by_course_week(1, 1)

        # Verify
        mock_session.query.assert_called_once_with(TopicModel)
        query_mock.filter_by.assert_called_once_with(course_id=1, week=1)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].title == "Topic 1"
        assert result[1].id == 2
        assert result[1].title == "Topic 2"

    def test_update(self, topic_repository, mock_session, mock_topic_model):
        """Test updating a topic."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_topic_model

        # Create topic to update
        topic = Topic(
            id=1,
            title="Updated Topic",
            order=2,
            week=2,
            course_id=2,
        )

        # Exercise
        result = topic_repository.update(topic)

        # Verify
        mock_session.query.assert_called_once_with(TopicModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        mock_session.commit.assert_called_once()

        # Check that the model was updated with new values
        assert mock_topic_model.title == "Updated Topic"
        assert mock_topic_model.order == 2
        assert mock_topic_model.week == 2
        assert mock_topic_model.course_id == 2

        # Check that the returned topic has the updated values
        assert result.id == 1
        assert result.title == "Updated Topic"
        assert result.order == 2
        assert result.week == 2
        assert result.course_id == 2

    def test_update_not_found(self, topic_repository, mock_session):
        """Test updating a non-existent topic raises an error."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Create topic to update
        topic = Topic(
            id=999,
            title="Updated Topic",
            order=2,
            week=2,
            course_id=2,
        )

        # Exercise & Verify
        with pytest.raises(ValueError, match="Topic with ID 999 not found"):
            topic_repository.update(topic)

    def test_delete(self, topic_repository, mock_session, mock_topic_model):
        """Test deleting a topic."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_topic_model

        # Exercise
        result = topic_repository.delete(1)

        # Verify
        mock_session.query.assert_called_once_with(TopicModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        mock_session.delete.assert_called_once_with(mock_topic_model)
        mock_session.commit.assert_called_once()
        assert result is True

    def test_delete_not_found(self, topic_repository, mock_session):
        """Test deleting a non-existent topic returns False."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Exercise
        result = topic_repository.delete(999)

        # Verify
        assert result is False
        mock_session.delete.assert_not_called()

    def test_delete_by_course(self, topic_repository, mock_session):
        """Test deleting topics by course."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.delete.return_value = 3

        # Exercise
        result = topic_repository.delete_by_course(1)

        # Verify
        mock_session.query.assert_called_once_with(TopicModel)
        query_mock.filter_by.assert_called_once_with(course_id=1)
        mock_session.commit.assert_called_once()
        assert result == 3
