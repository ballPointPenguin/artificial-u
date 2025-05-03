"""
Unit tests for CourseRepository.
"""

from unittest.mock import MagicMock, patch

import pytest

from artificial_u.models.core import Course
from artificial_u.models.database import CourseModel
from artificial_u.models.repositories.course import CourseRepository


class MockSession:
    """Mock SQLAlchemy session for testing."""

    def __init__(self):
        self.query_result = []
        self.query_filter = MagicMock(return_value=self)
        self.add = MagicMock()
        self.commit = MagicMock()
        self.refresh = MagicMock()
        self.delete = MagicMock()
        self.update = MagicMock()
        self.query = MagicMock(return_value=self)
        self.filter_by = MagicMock(return_value=self)
        self.all = MagicMock(return_value=[])
        self.first = MagicMock(return_value=None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.mark.unit
class TestCourseRepository:
    """Test the CourseRepository class."""

    @patch("artificial_u.models.repositories.course.CourseRepository.get_session")
    def test_create(self, mock_get_session):
        """Test creating a course."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Set up the refresh to set the ID
        def mock_refresh(model):
            model.id = 1
            model.topics = [{"name": "Topic 1"}, {"name": "Topic 2"}]

        mock_session.refresh.side_effect = mock_refresh

        # Create course to test
        course = Course(
            code="CS101",
            title="Introduction to Programming",
            department_id=1,
            level="Undergraduate",
            credits=3,
            professor_id=1,
            description="Basic programming concepts",
            lectures_per_week=2,
            total_weeks=14,
            topics=[{"name": "Topic 1"}, {"name": "Topic 2"}],
        )

        # Exercise
        repo = CourseRepository()
        result = repo.create(course)

        # Verify
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called
        assert result.id == 1
        assert result.code == "CS101"
        assert result.title == "Introduction to Programming"
        assert result.department_id == 1
        assert result.level == "Undergraduate"
        assert result.credits == 3
        assert result.professor_id == 1
        assert result.description == "Basic programming concepts"
        assert result.lectures_per_week == 2
        assert result.total_weeks == 14
        assert result.topics == [{"name": "Topic 1"}, {"name": "Topic 2"}]

    @patch("artificial_u.models.repositories.course.CourseRepository.get_session")
    def test_get(self, mock_get_session):
        """Test getting a course by ID."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock course model
        mock_course_model = MagicMock(spec=CourseModel)
        mock_course_model.id = 1
        mock_course_model.code = "CS101"
        mock_course_model.title = "Introduction to Programming"
        mock_course_model.department_id = 1
        mock_course_model.level = "Undergraduate"
        mock_course_model.credits = 3
        mock_course_model.professor_id = 1
        mock_course_model.description = "Basic programming concepts"
        mock_course_model.lectures_per_week = 2
        mock_course_model.total_weeks = 14
        mock_course_model.topics = [{"name": "Topic 1"}, {"name": "Topic 2"}]

        mock_session.first.return_value = mock_course_model

        # Exercise
        repo = CourseRepository()
        result = repo.get(1)

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(id=1)
        assert result.id == 1
        assert result.code == "CS101"
        assert result.title == "Introduction to Programming"
        assert result.department_id == 1
        assert result.level == "Undergraduate"
        assert result.credits == 3
        assert result.professor_id == 1
        assert result.description == "Basic programming concepts"
        assert result.lectures_per_week == 2
        assert result.total_weeks == 14
        assert result.topics == [{"name": "Topic 1"}, {"name": "Topic 2"}]

    @patch("artificial_u.models.repositories.course.CourseRepository.get_session")
    def test_get_not_found(self, mock_get_session):
        """Test getting a non-existent course returns None."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        mock_session.first.return_value = None

        # Exercise
        repo = CourseRepository()
        result = repo.get(999)

        # Verify
        assert result is None

    @patch("artificial_u.models.repositories.course.CourseRepository.get_session")
    def test_get_by_code(self, mock_get_session):
        """Test getting a course by code."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock course model
        mock_course_model = MagicMock(spec=CourseModel)
        mock_course_model.id = 1
        mock_course_model.code = "CS101"
        mock_course_model.title = "Introduction to Programming"
        mock_course_model.department_id = 1
        mock_course_model.level = "Undergraduate"
        mock_course_model.credits = 3
        mock_course_model.professor_id = 1
        mock_course_model.description = "Basic programming concepts"
        mock_course_model.lectures_per_week = 2
        mock_course_model.total_weeks = 14
        mock_course_model.topics = [{"name": "Topic 1"}, {"name": "Topic 2"}]

        mock_session.first.return_value = mock_course_model

        # Exercise
        repo = CourseRepository()
        result = repo.get_by_code("CS101")

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(code="CS101")
        assert result.id == 1
        assert result.code == "CS101"

    @patch("artificial_u.models.repositories.course.CourseRepository.get_session")
    def test_list(self, mock_get_session):
        """Test listing courses."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create mock course models
        mock_course1 = MagicMock(spec=CourseModel)
        mock_course1.id = 1
        mock_course1.code = "CS101"
        mock_course1.title = "Introduction to Programming"
        mock_course1.department_id = 1
        mock_course1.level = "Undergraduate"
        mock_course1.credits = 3
        mock_course1.professor_id = 1
        mock_course1.description = "Basic programming concepts"
        mock_course1.lectures_per_week = 2
        mock_course1.total_weeks = 14
        mock_course1.topics = [{"name": "Topic 1"}, {"name": "Topic 2"}]

        mock_course2 = MagicMock(spec=CourseModel)
        mock_course2.id = 2
        mock_course2.code = "CS201"
        mock_course2.title = "Data Structures"
        mock_course2.department_id = 1
        mock_course2.level = "Undergraduate"
        mock_course2.credits = 3
        mock_course2.professor_id = 2
        mock_course2.description = "Advanced data structures"
        mock_course2.lectures_per_week = 2
        mock_course2.total_weeks = 14
        mock_course2.topics = [{"name": "Arrays"}, {"name": "Linked Lists"}]

        mock_session.all.return_value = [mock_course1, mock_course2]

        # Exercise
        repo = CourseRepository()
        result = repo.list()

        # Verify
        mock_session.query.assert_called_once()
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].code == "CS101"
        assert result[1].id == 2
        assert result[1].code == "CS201"

    @patch("artificial_u.models.repositories.course.CourseRepository.get_session")
    def test_list_with_department_filter(self, mock_get_session):
        """Test listing courses with department filter."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create mock course model
        mock_course = MagicMock(spec=CourseModel)
        mock_course.id = 1
        mock_course.code = "CS101"
        mock_course.title = "Introduction to Programming"
        mock_course.department_id = 1
        mock_course.level = "Undergraduate"
        mock_course.credits = 3
        mock_course.professor_id = 1
        mock_course.description = "Basic programming concepts"
        mock_course.lectures_per_week = 2
        mock_course.total_weeks = 14
        mock_course.topics = [{"name": "Topic 1"}, {"name": "Topic 2"}]

        mock_session.all.return_value = [mock_course]

        # Exercise
        repo = CourseRepository()
        result = repo.list(department_id=1)

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(department_id=1)
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].department_id == 1

    @patch("artificial_u.models.repositories.course.CourseRepository.get_session")
    def test_update(self, mock_get_session):
        """Test updating a course."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock course model
        mock_course_model = MagicMock(spec=CourseModel)
        mock_course_model.id = 1
        mock_course_model.topics = [{"name": "Updated Topic 1"}, {"name": "Updated Topic 2"}]
        mock_session.first.return_value = mock_course_model

        # Create course to update
        course = Course(
            id=1,
            code="CS101-Updated",
            title="Introduction to Programming (Updated)",
            department_id=2,
            level="Graduate",
            credits=4,
            professor_id=2,
            description="Updated description",
            lectures_per_week=3,
            total_weeks=15,
            topics=[{"name": "Updated Topic 1"}, {"name": "Updated Topic 2"}],
        )

        # Exercise
        repo = CourseRepository()
        result = repo.update(course)

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(id=1)
        mock_session.commit.assert_called_once()

        # Check that the model was updated with new values
        assert mock_course_model.code == "CS101-Updated"
        assert mock_course_model.title == "Introduction to Programming (Updated)"
        assert mock_course_model.department_id == 2
        assert mock_course_model.level == "Graduate"
        assert mock_course_model.credits == 4
        assert mock_course_model.professor_id == 2
        assert mock_course_model.description == "Updated description"
        assert mock_course_model.lectures_per_week == 3
        assert mock_course_model.total_weeks == 15
        assert mock_course_model.topics == [
            {"name": "Updated Topic 1"},
            {"name": "Updated Topic 2"},
        ]

        # Check that the returned course has the updated values
        assert result.id == 1
        assert result.code == "CS101-Updated"
        assert result.title == "Introduction to Programming (Updated)"
        assert result.department_id == 2
        assert result.level == "Graduate"
        assert result.credits == 4
        assert result.professor_id == 2
        assert result.description == "Updated description"
        assert result.lectures_per_week == 3
        assert result.total_weeks == 15
        assert result.topics == [{"name": "Updated Topic 1"}, {"name": "Updated Topic 2"}]

    @patch("artificial_u.models.repositories.course.CourseRepository.get_session")
    def test_update_not_found(self, mock_get_session):
        """Test updating a non-existent course raises an error."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        mock_session.first.return_value = None

        # Create course to update
        course = Course(
            id=999,
            code="CS999",
            title="Nonexistent Course",
            department_id=1,
            level="Undergraduate",
            credits=3,
            professor_id=1,
            description="This course doesn't exist",
            lectures_per_week=2,
            total_weeks=14,
            topics=[{"name": "Nonexistent Topic"}],
        )

        # Exercise & Verify
        repo = CourseRepository()
        with pytest.raises(ValueError, match="Course with ID 999 not found"):
            repo.update(course)

    @patch("artificial_u.models.repositories.course.CourseRepository.get_session")
    def test_delete(self, mock_get_session):
        """Test deleting a course."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock course model
        mock_course_model = MagicMock(spec=CourseModel)
        mock_course_model.id = 1
        mock_session.first.return_value = mock_course_model

        # Exercise
        repo = CourseRepository()
        result = repo.delete(1)

        # Verify
        mock_session.query.assert_called_once_with(CourseModel)
        mock_session.filter_by.assert_called_once_with(id=1)
        mock_session.delete.assert_called_once_with(mock_course_model)
        mock_session.commit.assert_called_once()
        assert result is True

    @patch("artificial_u.models.repositories.course.CourseRepository.get_session")
    def test_delete_not_found(self, mock_get_session):
        """Test deleting a non-existent course returns False."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        mock_session.first.return_value = None

        # Exercise
        repo = CourseRepository()
        result = repo.delete(999)

        # Verify
        assert result is False
        mock_session.delete.assert_not_called()
