"""
Unit tests for the LectureRepository class.
"""

from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Lecture
from artificial_u.models.database import CourseModel, LectureModel
from artificial_u.models.repositories.lecture import LectureRepository


@pytest.mark.unit
class TestLectureRepository:
    """Tests for the LectureRepository class."""

    @pytest.fixture
    def lecture_repository(self, repository_with_session):
        """Create a LectureRepository with a mock session."""
        return repository_with_session(LectureRepository)

    @pytest.fixture
    def sample_lecture(self):
        """Create a sample lecture for testing."""
        return Lecture(
            id=1,
            revision=1,
            content="Test Content",
            summary="Test Summary",
            title="Test Title",
            audio_url="test_audio_url",
            transcript_url="test_transcript_url",
            course_id=1,
            topic_id=1,
        )

    @pytest.fixture
    def sample_lecture_model(self):
        """Create a sample lecture model for testing."""
        lecture = MagicMock(spec=LectureModel)
        lecture.id = 1
        lecture.revision = 1
        lecture.content = "Test Content"
        lecture.summary = "Test Summary"
        lecture.title = "Test Title"
        lecture.audio_url = "test_audio_url"
        lecture.transcript_url = "test_transcript_url"
        lecture.course_id = 1
        lecture.topic_id = 1
        return lecture

    @pytest.fixture
    def sample_course_model(self):
        """Create a sample course model for testing."""
        course = MagicMock(spec=CourseModel)
        course.id = 1
        course.professor_id = 1
        return course

    def test_create(self, lecture_repository, mock_session, sample_lecture):
        """Test creating a lecture."""
        # Configure mock behavior
        mock_session.refresh.side_effect = lambda lecture: setattr(lecture, "id", 1)

        # Call method
        result = lecture_repository.create(sample_lecture)

        # Verify
        assert result.id == 1
        assert result.revision == sample_lecture.revision
        assert result.content == sample_lecture.content
        assert result.summary == sample_lecture.summary
        assert result.title == sample_lecture.title
        assert result.audio_url == sample_lecture.audio_url
        assert result.transcript_url == sample_lecture.transcript_url
        assert result.course_id == sample_lecture.course_id
        assert result.topic_id == sample_lecture.topic_id
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_get_existing(self, lecture_repository, mock_session, sample_lecture_model):
        """Test getting an existing lecture."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = sample_lecture_model

        # Call method
        result = lecture_repository.get(1)

        # Verify
        assert result is not None
        assert result.id == 1
        assert result.revision == 1
        assert result.content == "Test Content"
        assert result.summary == "Test Summary"
        assert result.title == "Test Title"
        assert result.audio_url == "test_audio_url"
        assert result.transcript_url == "test_transcript_url"
        assert result.course_id == 1
        assert result.topic_id == 1
        mock_session.query.assert_called_once_with(LectureModel)
        query_mock.filter_by.assert_called_once_with(id=1)

    def test_get_nonexistent(self, lecture_repository, mock_session):
        """Test getting a non-existent lecture."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Call method
        result = lecture_repository.get(999)

        # Verify
        assert result is None
        mock_session.query.assert_called_once_with(LectureModel)
        query_mock.filter_by.assert_called_once_with(id=999)

    def test_get_content(self, lecture_repository, mock_session, sample_lecture_model):
        """Test getting lecture content."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = sample_lecture_model

        # Call method
        result = lecture_repository.get_content(1)

        # Verify
        assert result == "Test Content"
        mock_session.query.assert_called_once_with(LectureModel)
        query_mock.filter_by.assert_called_once_with(id=1)

    def test_get_audio_url(self, lecture_repository, mock_session, sample_lecture_model):
        """Test getting lecture audio URL."""
        # Configure mock behavior
        mock_session.get.return_value = sample_lecture_model

        # Call method
        result = lecture_repository.get_audio_url(1)

        # Verify
        assert result == "test_audio_url"
        mock_session.get.assert_called_once_with(LectureModel, 1)

    def test_get_transcript_url(self, lecture_repository, mock_session, sample_lecture_model):
        """Test getting lecture transcript URL."""
        # Configure mock behavior
        mock_session.get.return_value = sample_lecture_model

        # Call method
        result = lecture_repository.get_transcript_url(1)

        # Verify
        assert result == "test_transcript_url"
        mock_session.get.assert_called_once_with(LectureModel, 1)

    def test_list_by_course(self, lecture_repository, mock_session, sample_lecture_model):
        """Test listing lectures by course."""
        # Configure mock behavior for subquery
        subquery_mock = MagicMock()
        subquery_mock.c.topic_id = MagicMock()
        subquery_mock.c.max_revision = MagicMock()

        # Configure mock behavior for main query
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.subquery.return_value = subquery_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = [sample_lecture_model]

        # Call method
        result = lecture_repository.list_by_course(1)

        # Verify
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].revision == 1
        assert result[0].content == "Test Content"
        assert result[0].summary == "Test Summary"
        assert result[0].title == "Test Title"
        assert result[0].audio_url == "test_audio_url"
        assert result[0].transcript_url == "test_transcript_url"
        assert result[0].course_id == 1
        assert result[0].topic_id == 1
        # Verify that query was called multiple times (for subquery and main query)
        assert mock_session.query.call_count >= 2

    def test_list_by_topic(self, lecture_repository, mock_session, sample_lecture_model):
        """Test listing lectures by topic."""
        # Configure mock behavior for max revision query
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.scalar.return_value = 1  # Latest revision is 1
        query_mock.first.return_value = sample_lecture_model

        # Call method
        result = lecture_repository.list_by_topic(1)

        # Verify
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].revision == 1
        assert result[0].content == "Test Content"
        assert result[0].summary == "Test Summary"
        assert result[0].title == "Test Title"
        assert result[0].audio_url == "test_audio_url"
        assert result[0].transcript_url == "test_transcript_url"
        assert result[0].course_id == 1
        assert result[0].topic_id == 1
        # Verify that query was called multiple times (for max revision and main query)
        assert mock_session.query.call_count >= 2

    def test_list(self, lecture_repository, mock_session, sample_lecture_model):
        """Test listing all lectures."""
        # Configure mock behavior for subquery
        subquery_mock = MagicMock()
        subquery_mock.c.topic_id = MagicMock()
        subquery_mock.c.max_revision = MagicMock()

        # Configure mock behavior for main query
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.subquery.return_value = subquery_mock
        query_mock.join.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [sample_lecture_model]

        # Call method
        result = lecture_repository.list()

        # Verify
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].revision == 1
        assert result[0].content == "Test Content"
        assert result[0].summary == "Test Summary"
        assert result[0].title == "Test Title"
        assert result[0].audio_url == "test_audio_url"
        assert result[0].transcript_url == "test_transcript_url"
        assert result[0].course_id == 1
        assert result[0].topic_id == 1
        # Verify that query was called multiple times (for subquery and main query)
        assert mock_session.query.call_count >= 2

    def test_list_with_filters(self, lecture_repository, mock_session, sample_lecture_model):
        """Test listing lectures with filters."""
        # Configure mock behavior for subquery
        subquery_mock = MagicMock()
        subquery_mock.c.topic_id = MagicMock()
        subquery_mock.c.max_revision = MagicMock()

        # Configure mock behavior for main query
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.subquery.return_value = subquery_mock
        query_mock.join.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [sample_lecture_model]

        # Call method
        result = lecture_repository.list(course_id=1)

        # Verify
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].revision == 1
        assert result[0].content == "Test Content"
        assert result[0].summary == "Test Summary"
        assert result[0].title == "Test Title"
        assert result[0].audio_url == "test_audio_url"
        assert result[0].transcript_url == "test_transcript_url"
        assert result[0].course_id == 1
        assert result[0].topic_id == 1
        # Verify that query was called multiple times (for subquery and main query)
        assert mock_session.query.call_count >= 2

    def test_update(self, lecture_repository, mock_session, sample_lecture, sample_lecture_model):
        """Test updating a lecture."""
        # Configure mock behavior
        mock_session.get.return_value = sample_lecture_model
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = sample_lecture_model

        # Call method
        updated_lecture = sample_lecture
        updated_lecture.content = "Updated Content"
        result = lecture_repository.update(updated_lecture)

        # Verify
        assert result.content == "Updated Content"
        mock_session.commit.assert_called_once()

    def test_update_not_found(self, lecture_repository, mock_session, sample_lecture):
        """Test updating a non-existent lecture."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Call method & verify
        with pytest.raises(ValueError, match="Lecture with ID 1 not found"):
            lecture_repository.update(sample_lecture)

    def test_delete_existing(self, lecture_repository, mock_session, sample_lecture_model):
        """Test deleting an existing lecture."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = sample_lecture_model

        # Call method
        result = lecture_repository.delete(1)

        # Verify
        assert result is True
        mock_session.delete.assert_called_once_with(sample_lecture_model)
        mock_session.commit.assert_called_once()

    def test_delete_nonexistent(self, lecture_repository, mock_session):
        """Test deleting a non-existent lecture."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Call method
        result = lecture_repository.delete(999)

        # Verify
        assert result is False
        mock_session.delete.assert_not_called()

    def test_delete_by_course(self, lecture_repository, mock_session):
        """Test deleting lectures by course."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.delete.return_value = 2

        # Call method
        result = lecture_repository.delete_by_course(1)

        # Verify
        assert result == 2
        mock_session.query.assert_called_once_with(LectureModel)
        query_mock.filter_by.assert_called_once_with(course_id=1)
        mock_session.commit.assert_called_once()

    def test_delete_by_topic(self, lecture_repository, mock_session):
        """Test deleting lectures by topic."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.delete.return_value = 2

        # Call method
        result = lecture_repository.delete_by_topic(1)

        # Verify
        assert result == 2
        mock_session.query.assert_called_once_with(LectureModel)
        query_mock.filter_by.assert_called_once_with(topic_id=1)
        mock_session.commit.assert_called_once()

    def test_count_with_filters(self, lecture_repository, mock_session):
        """Test counting lectures with various filters."""
        # Mock the query chain
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.count.return_value = 5

        # Test count with course_id filter
        result = lecture_repository.count(course_id=1)
        assert result == 5
        mock_query.filter.assert_called()
        mock_query.count.assert_called_once()

        # Reset mock for next test
        mock_query.reset_mock()
        mock_query.count.return_value = 3

        # Test count with professor_id filter
        result = lecture_repository.count(professor_id=2)
        assert result == 3
        mock_query.join.assert_called()
        mock_query.filter.assert_called()
        mock_query.count.assert_called_once()

        # Reset mock for next test
        mock_query.reset_mock()
        mock_query.count.return_value = 2

        # Test count with search query
        result = lecture_repository.count(search_query="test")
        assert result == 2
        mock_query.filter.assert_called()
        mock_query.count.assert_called_once()

    def test_list_by_course_only_latest_revision(self, lecture_repository, mock_session):
        """Test that list_by_course only returns the latest revision for each topic."""
        # Create mock lectures with different revisions for the same topic
        lecture1 = MagicMock()
        lecture1.id = 1
        lecture1.revision = 1
        lecture1.content = "Old Content"
        lecture1.summary = "Old Summary"
        lecture1.title = "Old Title"
        lecture1.audio_url = "old_audio_url"
        lecture1.transcript_url = "old_transcript_url"
        lecture1.course_id = 1
        lecture1.topic_id = 1

        lecture2 = MagicMock()
        lecture2.id = 2
        lecture2.revision = 2
        lecture2.content = "New Content"
        lecture2.summary = "New Summary"
        lecture2.title = "New Title"
        lecture2.audio_url = "new_audio_url"
        lecture2.transcript_url = "new_transcript_url"
        lecture2.course_id = 1
        lecture2.topic_id = 1

        # Configure mock behavior for subquery
        subquery_mock = MagicMock()
        subquery_mock.c.topic_id = MagicMock()
        subquery_mock.c.max_revision = MagicMock()

        # Configure mock behavior for main query
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.subquery.return_value = subquery_mock
        query_mock.join.return_value = query_mock
        query_mock.all.return_value = [lecture2]  # Only return the latest revision

        # Call method
        result = lecture_repository.list_by_course(1)

        # Verify
        assert len(result) == 1
        assert result[0].id == 2  # Should be the latest revision
        assert result[0].revision == 2
        assert result[0].content == "New Content"
        assert result[0].title == "New Title"
        assert result[0].topic_id == 1

    def test_list_by_topic_only_latest_revision(self, lecture_repository, mock_session):
        """Test that list_by_topic only returns the latest revision."""
        # Create mock lecture with latest revision
        latest_lecture = MagicMock()
        latest_lecture.id = 2
        latest_lecture.revision = 2
        latest_lecture.content = "Latest Content"
        latest_lecture.summary = "Latest Summary"
        latest_lecture.title = "Latest Title"
        latest_lecture.audio_url = "latest_audio_url"
        latest_lecture.transcript_url = "latest_transcript_url"
        latest_lecture.course_id = 1
        latest_lecture.topic_id = 1

        # Configure mock behavior for max revision query
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.scalar.return_value = 2  # Latest revision is 2
        query_mock.first.return_value = latest_lecture

        # Call method
        result = lecture_repository.list_by_topic(1)

        # Verify
        assert len(result) == 1
        assert result[0].id == 2
        assert result[0].revision == 2
        assert result[0].content == "Latest Content"
        assert result[0].title == "Latest Title"
        assert result[0].topic_id == 1

    def test_list_with_topic_id_filter(
        self, lecture_repository, mock_session, sample_lecture_model
    ):
        """Test listing lectures with topic_id filter."""
        # Configure mock behavior for subquery
        subquery_mock = MagicMock()
        subquery_mock.c.topic_id = MagicMock()
        subquery_mock.c.max_revision = MagicMock()

        # Configure mock behavior for main query
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.group_by.return_value = query_mock
        query_mock.subquery.return_value = subquery_mock
        query_mock.join.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.all.return_value = [sample_lecture_model]

        # Call method with topic_id filter
        result = lecture_repository.list(topic_id=20)

        # Verify
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].topic_id == 1  # This is the sample lecture's topic_id
        # Verify that query was called multiple times (for subquery and main query)
        assert mock_session.query.call_count >= 2
        # Verify that filter was called for topic_id
        query_mock.filter.assert_called()
