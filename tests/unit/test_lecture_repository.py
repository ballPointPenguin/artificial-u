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
    def mock_session(self):
        """Create a mock session."""
        session = MagicMock()
        session.__enter__.return_value = session
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create a repository with a mock session."""
        repo = LectureRepository()
        repo.get_session = MagicMock(return_value=mock_session)
        return repo

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
        course = MagicMock(spec=CourseModel)
        course.id = 1
        course.title = "Test Course"
        course.professor_id = 1
        course.professor = "Test Professor"
        return course

    def test_create(self, repository, mock_session, sample_lecture):
        """Test creating a lecture."""
        # Setup mock
        db_lecture = MagicMock()
        db_lecture.id = 1
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.side_effect = lambda lecture: setattr(lecture, "id", 1)

        # Call method
        result = repository.create(sample_lecture)

        # Check results
        assert result.id == 1
        assert result.title == sample_lecture.title
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_get_existing(self, repository, mock_session, sample_lecture_model):
        """Test getting an existing lecture."""
        # Setup mock
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_lecture_model
        )

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
            result = repository.get(1)

            # Check results
            assert result is not None
            assert result.id == 1
            assert result.title == "Test Lecture"
            mock_session.query.assert_called_once_with(LectureModel)
            mock_session.query.return_value.filter_by.assert_called_once_with(id=1)

    def test_get_nonexistent(self, repository, mock_session):
        """Test getting a non-existent lecture."""
        # Setup mock
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Call method
        result = repository.get(999)

        # Check results
        assert result is None
        mock_session.query.assert_called_once_with(LectureModel)
        mock_session.query.return_value.filter_by.assert_called_once_with(id=999)

    def test_get_by_course_week_order(self, repository, mock_session, sample_lecture_model):
        """Test getting a lecture by course, week, and order."""
        # Setup mock
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_lecture_model
        )

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
            result = repository.get_by_course_week_order(1, 1, 1)

            # Check results
            assert result is not None
            assert result.id == 1
            assert result.title == "Test Lecture"
            mock_session.query.assert_called_once_with(LectureModel)
            mock_session.query.return_value.filter_by.assert_called_once_with(
                course_id=1, week_number=1, order_in_week=1
            )

    def test_get_content(self, repository, mock_session, sample_lecture_model):
        """Test getting lecture content."""
        # Setup mock
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_lecture_model
        )

        # Call method
        result = repository.get_content(1)

        # Check results
        assert result == "Test Content"
        mock_session.query.assert_called_once_with(LectureModel)
        mock_session.query.return_value.filter_by.assert_called_once_with(id=1)

    def test_get_audio_url(self, repository, mock_session, sample_lecture_model):
        """Test getting lecture audio URL."""
        # Setup mock
        mock_session.get.return_value = sample_lecture_model

        # Call method
        result = repository.get_audio_url(1)

        # Check results
        assert result == "test_audio_url"
        mock_session.get.assert_called_once_with(LectureModel, 1)

    def test_list_by_course(self, repository, mock_session, sample_lecture_model):
        """Test listing lectures by course."""
        # Setup mock
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
            result = repository.list_by_course(1)

            # Check results
            assert len(result) == 1
            assert result[0].id == 1
            assert result[0].title == "Test Lecture"
            mock_session.query.assert_called_once_with(LectureModel)
            query_mock.filter_by.assert_called_once_with(course_id=1)

    def test_list(self, repository, mock_session, sample_lecture_model):
        """Test listing lectures with filters."""
        # Setup mock
        query_mock = mock_session.query.return_value
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
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
            # Call method with default parameters
            result = repository.list()

            # Check results
            assert len(result) == 1
            assert result[0].id == 1
            assert result[0].title == "Test Lecture"
            mock_session.query.assert_called_with(LectureModel)
            query_mock.order_by.assert_called_once()
            query_mock.offset.assert_called_once_with(0)
            query_mock.limit.assert_called_once_with(10)

    def test_list_with_filters(self, repository, mock_session, sample_lecture_model):
        """Test listing lectures with course_id, professor_id, and search filters."""
        # Setup mock
        query_mock = mock_session.query.return_value
        query_mock.filter.return_value = query_mock
        query_mock.join.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.offset.return_value = query_mock
        query_mock.limit.return_value = query_mock
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
            # Call method with filters
            result = repository.list(
                page=2, size=5, course_id=1, professor_id=1, search_query="test"
            )

            # Check results
            assert len(result) == 1
            assert result[0].id == 1
            mock_session.query.assert_called_with(LectureModel)

            # Since we're using complex query building, we can't easily assert the exact call chain
            # But we can verify the final operations
            query_mock.offset.assert_called_once_with(5)  # (page-1)*size = (2-1)*5 = 5
            query_mock.limit.assert_called_once_with(5)

    def test_count(self, repository, mock_session):
        """Test counting lectures."""
        # Setup mock
        mock_session.query.return_value.scalar.return_value = 10

        # Call method
        result = repository.count()

        # Check results
        assert result == 10
        # We can't directly compare the func.count() objects, so we just check that query was called
        assert mock_session.query.called
        mock_session.query.return_value.scalar.assert_called_once()

    def test_update(self, repository, mock_session, sample_lecture, sample_lecture_model):
        """Test updating a lecture."""
        # Setup mock
        mock_session.get.return_value = sample_lecture_model

        # Call method
        result = repository.update(sample_lecture)

        # Check results
        assert result.id == sample_lecture.id
        assert result.title == sample_lecture.title
        mock_session.get.assert_called_once_with(LectureModel, sample_lecture.id)
        mock_session.add.assert_called_once_with(sample_lecture_model)
        mock_session.commit.assert_called_once()

    def test_update_not_found(self, repository, mock_session, sample_lecture):
        """Test updating a non-existent lecture."""
        # Setup mock
        mock_session.get.return_value = None

        # Check that ValueError is raised
        with pytest.raises(ValueError):
            repository.update(sample_lecture)

        mock_session.get.assert_called_once_with(LectureModel, sample_lecture.id)
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_delete_existing(self, repository, mock_session, sample_lecture_model):
        """Test deleting an existing lecture."""
        # Setup mock
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_lecture_model
        )

        # Call method
        result = repository.delete(1)

        # Check results
        assert result is True
        mock_session.query.assert_called_once_with(LectureModel)
        mock_session.query.return_value.filter_by.assert_called_once_with(id=1)
        mock_session.delete.assert_called_once_with(sample_lecture_model)
        mock_session.commit.assert_called_once()

    def test_delete_nonexistent(self, repository, mock_session):
        """Test deleting a non-existent lecture."""
        # Setup mock
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        # Call method
        result = repository.delete(999)

        # Check results
        assert result is False
        mock_session.query.assert_called_once_with(LectureModel)
        mock_session.query.return_value.filter_by.assert_called_once_with(id=999)
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_build_lecture_summary(
        self, repository, mock_session, sample_lecture, sample_course_model
    ):
        """Test building a lecture summary."""
        # Setup mock
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_course_model
        )

        # Call method
        result = repository.build_lecture_summary(sample_lecture)

        # Check results
        assert result["id"] == sample_lecture.id
        assert result["title"] == sample_lecture.title
        assert result["course_id"] == sample_lecture.course_id
        assert result["course_title"] == sample_course_model.title
        assert result["professor_id"] == sample_course_model.professor_id
        assert result["week_number"] == sample_lecture.week_number
        assert result["order_in_week"] == sample_lecture.order_in_week
        assert result["description"] == sample_lecture.description
        assert result["has_audio"] is True
        mock_session.query.assert_called_once_with(CourseModel)
        mock_session.query.return_value.filter_by.assert_called_once_with(
            id=sample_lecture.course_id
        )

    def test_build_lecture_detail(
        self, repository, mock_session, sample_lecture, sample_course_model
    ):
        """Test building a lecture detail."""
        # Setup mocks for build_lecture_summary (which is called by build_lecture_detail)
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            sample_course_model
        )

        # Create a mock for build_lecture_summary to control its output
        summary = {
            "id": sample_lecture.id,
            "title": sample_lecture.title,
            "course_id": sample_lecture.course_id,
            "course_title": sample_course_model.title,
            "professor_id": sample_course_model.professor_id,
            "week_number": sample_lecture.week_number,
            "order_in_week": sample_lecture.order_in_week,
            "description": sample_lecture.description,
            "has_audio": True,
        }

        # Create a mock professor object with a name attribute for the second query
        professor_mock = MagicMock()
        professor_mock.name = "Test Professor Name"

        # Set up the session query to return this mock when querying for the professor
        mock_session.query.return_value.filter_by.return_value.first.return_value = professor_mock

        with patch.object(repository, "build_lecture_summary", return_value=summary):
            # Call method
            result = repository.build_lecture_detail(sample_lecture)

            # Check results
            assert result["id"] == sample_lecture.id
            assert result["title"] == sample_lecture.title
            assert result["course_id"] == sample_lecture.course_id
            assert result["content"] == sample_lecture.content
            assert result["audio_url"] == sample_lecture.audio_url
            assert "professor_name" in result
            assert result["professor_name"] == "Test Professor Name"

            # Verify build_lecture_summary was called
            repository.build_lecture_summary.assert_called_once_with(sample_lecture)
