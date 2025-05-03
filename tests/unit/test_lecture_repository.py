"""
Unit tests for the LectureRepository class.
"""

from unittest.mock import MagicMock, patch

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
            title="Test Lecture",
            course_id=1,
            week_number=1,
            order_in_week=1,
            description="Test Description",
            content="Test Content",
            audio_url="test_audio_url",
        )

    @pytest.fixture
    def sample_lecture_model(self):
        """Create a sample lecture model for testing."""
        lecture = MagicMock(spec=LectureModel)
        lecture.id = 1
        lecture.title = "Test Lecture"
        lecture.course_id = 1
        lecture.week_number = 1
        lecture.order_in_week = 1
        lecture.description = "Test Description"
        lecture.content = "Test Content"
        lecture.audio_url = "test_audio_url"
        return lecture

    @pytest.fixture
    def sample_course_model(self):
        """Create a sample course model for testing."""
        # Create professor mock first
        mock_professor = MagicMock()
        mock_professor.name = "Test Professor"

        # Then create course mock with professor property
        course = MagicMock(spec=CourseModel)
        course.id = 1
        course.title = "Test Course"
        course.professor_id = 1
        course.professor = mock_professor  # Set the professor as a proper mock object

        return course

    def test_create(self, lecture_repository, mock_session, sample_lecture):
        """Test creating a lecture."""
        # Configure mock behavior
        mock_session.refresh.side_effect = lambda lecture: setattr(lecture, "id", 1)

        # Call method
        result = lecture_repository.create(sample_lecture)

        # Verify
        assert result.id == 1
        assert result.title == sample_lecture.title
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_get_existing(self, lecture_repository, mock_session, sample_lecture_model):
        """Test getting an existing lecture."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = sample_lecture_model

        with patch(
            "artificial_u.models.repositories.lecture.lecture_model_to_entity",
            return_value=Lecture(
                id=1,
                title="Test Lecture",
                course_id=1,
                week_number=1,
                order_in_week=1,
                description="Test Description",
                content="Test Content",
                audio_url="test_audio_url",
            ),
        ):
            # Call method
            result = lecture_repository.get(1)

            # Verify
            assert result is not None
            assert result.id == 1
            assert result.title == "Test Lecture"
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

    def test_get_by_course_week_order(self, lecture_repository, mock_session, sample_lecture_model):
        """Test getting a lecture by course, week, and order."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = sample_lecture_model

        with patch(
            "artificial_u.models.repositories.lecture.lecture_model_to_entity",
            return_value=Lecture(
                id=1,
                title="Test Lecture",
                course_id=1,
                week_number=1,
                order_in_week=1,
                description="Test Description",
                content="Test Content",
                audio_url="test_audio_url",
            ),
        ):
            # Call method
            result = lecture_repository.get_by_course_week_order(1, 1, 1)

            # Verify
            assert result is not None
            assert result.id == 1
            assert result.title == "Test Lecture"
            mock_session.query.assert_called_once_with(LectureModel)
            query_mock.filter_by.assert_called_once_with(
                course_id=1, week_number=1, order_in_week=1
            )

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

    def test_list_by_course(self, lecture_repository, mock_session, sample_lecture_model):
        """Test listing lectures by course."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = [sample_lecture_model]

        with patch(
            "artificial_u.models.repositories.lecture.lecture_model_to_entity",
            return_value=Lecture(
                id=1,
                title="Test Lecture",
                course_id=1,
                week_number=1,
                order_in_week=1,
                description="Test Description",
                content="Test Content",
                audio_url="test_audio_url",
            ),
        ):
            # Call method
            result = lecture_repository.list_by_course(1)

            # Verify
            assert len(result) == 1
            assert result[0].id == 1
            assert result[0].title == "Test Lecture"
            mock_session.query.assert_called_once_with(LectureModel)
            query_mock.filter_by.assert_called_once_with(course_id=1)
            query_mock.order_by.assert_called_once()

    def test_list(self, lecture_repository, mock_session, sample_lecture_model):
        """Test listing all lectures."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.all.return_value = [sample_lecture_model]

        with patch(
            "artificial_u.models.repositories.lecture.lecture_model_to_entity",
            return_value=Lecture(
                id=1,
                title="Test Lecture",
                course_id=1,
                week_number=1,
                order_in_week=1,
                description="Test Description",
                content="Test Content",
                audio_url="test_audio_url",
            ),
        ):
            # Call method
            result = lecture_repository.list()

            # Verify
            assert len(result) == 1
            assert result[0].id == 1
            assert result[0].title == "Test Lecture"
            mock_session.query.assert_called_once_with(LectureModel)

    def test_list_with_filters(self, lecture_repository, mock_session, sample_lecture_model):
        """Test listing lectures with filters."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [sample_lecture_model]

        with patch(
            "artificial_u.models.repositories.lecture.lecture_model_to_entity",
            return_value=Lecture(
                id=1,
                title="Test Lecture",
                course_id=1,
                week_number=1,
                order_in_week=1,
                description="Test Description",
                content="Test Content",
                audio_url="test_audio_url",
            ),
        ):
            # Call method
            result = lecture_repository.list(course_id=1)

            # Verify
            assert len(result) == 1
            assert result[0].id == 1
            assert result[0].title == "Test Lecture"
            mock_session.query.assert_called_once_with(LectureModel)

            # Use ANY to match any parameter since we can't easily recreate the BinaryExpression
            from unittest.mock import ANY

            query_mock.filter.assert_called_once_with(ANY)

    def test_count(self, lecture_repository, mock_session):
        """Test counting lectures."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.scalar.return_value = 10

        # Call method
        result = lecture_repository.count()

        # Verify
        assert result == 10
        mock_session.query.assert_called_once()

    def test_update(self, lecture_repository, mock_session, sample_lecture, sample_lecture_model):
        """Test updating a lecture."""
        # Configure mock behavior
        mock_session.get.return_value = sample_lecture_model
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = sample_lecture_model

        # Call method
        updated_lecture = sample_lecture
        updated_lecture.title = "Updated Lecture"
        result = lecture_repository.update(updated_lecture)

        # Verify
        assert result.title == "Updated Lecture"
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

    def test_build_lecture_summary(
        self, lecture_repository, mock_session, sample_lecture, sample_course_model
    ):
        """Test building a lecture summary."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = sample_course_model

        # Call method
        result = lecture_repository.build_lecture_summary(sample_lecture)

        # Verify expected structure
        assert result["id"] == 1
        assert result["title"] == "Test Lecture"
        assert result["course_id"] == 1
        assert result["course_title"] == "Test Course"
        assert result["week_number"] == 1
        assert result["order_in_week"] == 1
        assert result["description"] == "Test Description"
        assert "content" not in result
        assert "audio_url" not in result

    def test_build_lecture_detail(
        self, lecture_repository, mock_session, sample_lecture, sample_course_model
    ):
        """Test building a lecture detail."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = sample_course_model

        # Create a proper professor mock for the nested query
        professor_result = MagicMock()
        professor_result.name = "Test Professor"

        # Mock the nested query for CourseModel.professor
        professor_query_mock = MagicMock()
        professor_query_mock.filter_by.return_value.first.return_value = professor_result
        mock_session.query.side_effect = [query_mock, professor_query_mock]

        # Call method
        result = lecture_repository.build_lecture_detail(sample_lecture)

        # Verify expected structure
        assert result["id"] == 1
        assert result["title"] == "Test Lecture"
        assert result["course_id"] == 1
        assert result["course_title"] == "Test Course"
        assert result["week_number"] == 1
        assert result["order_in_week"] == 1
        assert result["description"] == "Test Description"
        assert result["content"] == "Test Content"
        assert result["audio_url"] == "test_audio_url"
        assert result["professor_name"] == "Test Professor"
