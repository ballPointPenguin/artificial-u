"""
Unit tests for CourseRepository.
"""

from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Course
from artificial_u.models.database import CourseModel
from artificial_u.models.repositories.course import CourseRepository


@pytest.mark.unit
class TestCourseRepository:
    """Test the CourseRepository class."""

    @pytest.fixture
    def course_repository(self, repository_with_session):
        """Create a CourseRepository with a mock session."""
        return repository_with_session(CourseRepository)

    @pytest.fixture
    def mock_course_model(self):
        """Create a mock course model for testing."""
        mock_course = MagicMock(spec=CourseModel)
        mock_course.id = 1
        mock_course.code = "CS101"
        mock_course.title = "Introduction to Programming"
        mock_course.credits = 3
        mock_course.description = "Basic programming concepts"
        mock_course.lectures_per_week = 2
        mock_course.level = "Undergraduate"
        mock_course.total_weeks = 14
        mock_course.department_id = 1
        mock_course.professor_id = 1
        return mock_course

    def test_create(self, course_repository, mock_session):
        """Test creating a course."""

        # Configure mock behaviors
        def mock_refresh(model):
            model.id = 1

        mock_session.refresh.side_effect = mock_refresh

        # Create course to test
        course = Course(
            code="CS101",
            title="Introduction to Programming",
            credits=3,
            description="Basic programming concepts",
            lectures_per_week=2,
            level="Undergraduate",
            total_weeks=14,
            department_id=1,
            professor_id=1,
        )

        # Exercise
        result = course_repository.create(course)

        # Verify
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called
        assert result.id == 1
        assert result.code == "CS101"
        assert result.title == "Introduction to Programming"
        assert result.credits == 3
        assert result.description == "Basic programming concepts"
        assert result.lectures_per_week == 2
        assert result.level == "Undergraduate"
        assert result.total_weeks == 14
        assert result.department_id == 1
        assert result.professor_id == 1

    def test_get(self, course_repository, mock_session, mock_course_model):
        """Test getting a course by ID."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_course_model

        # Exercise
        result = course_repository.get(1)

        # Verify
        mock_session.query.assert_called_once_with(CourseModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        assert result.id == 1
        assert result.code == "CS101"
        assert result.title == "Introduction to Programming"
        assert result.credits == 3
        assert result.description == "Basic programming concepts"
        assert result.lectures_per_week == 2
        assert result.level == "Undergraduate"
        assert result.total_weeks == 14
        assert result.department_id == 1
        assert result.professor_id == 1

    def test_get_not_found(self, course_repository, mock_session):
        """Test getting a non-existent course returns None."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Exercise
        result = course_repository.get(999)

        # Verify
        assert result is None

    def test_get_by_code(self, course_repository, mock_session, mock_course_model):
        """Test getting a course by code."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_course_model

        # Exercise
        result = course_repository.get_by_code("CS101")

        # Verify
        mock_session.query.assert_called_once_with(CourseModel)
        query_mock.filter_by.assert_called_once_with(code="CS101")
        assert result.id == 1
        assert result.code == "CS101"

    def test_list(self, course_repository, mock_session):
        """Test listing courses."""
        # Configure mock behavior
        mock_course1 = MagicMock(spec=CourseModel)
        mock_course1.id = 1
        mock_course1.code = "CS101"
        mock_course1.title = "Introduction to Programming"
        mock_course1.credits = 3
        mock_course1.description = "Basic programming concepts"
        mock_course1.lectures_per_week = 2
        mock_course1.level = "Undergraduate"
        mock_course1.total_weeks = 14
        mock_course1.department_id = 1
        mock_course1.professor_id = 1

        mock_course2 = MagicMock(spec=CourseModel)
        mock_course2.id = 2
        mock_course2.code = "CS102"
        mock_course2.title = "Advanced Programming"
        mock_course2.credits = 4
        mock_course2.description = "Advanced programming concepts"
        mock_course2.lectures_per_week = 3
        mock_course2.level = "Graduate"
        mock_course2.total_weeks = 14
        mock_course2.department_id = 1
        mock_course2.professor_id = 2

        query_mock = mock_session.query.return_value
        query_mock.all.return_value = [mock_course1, mock_course2]

        # Exercise
        result = course_repository.list()

        # Verify
        mock_session.query.assert_called_once_with(CourseModel)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].code == "CS101"
        assert result[1].id == 2
        assert result[1].code == "CS102"

    def test_list_with_department_filter(self, course_repository, mock_session):
        """Test listing courses with department filter."""
        # Configure mock behavior
        mock_course = MagicMock(spec=CourseModel)
        mock_course.id = 1
        mock_course.code = "CS101"
        mock_course.title = "Introduction to Programming"
        mock_course.credits = 3
        mock_course.description = "Basic programming concepts"
        mock_course.lectures_per_week = 2
        mock_course.level = "Undergraduate"
        mock_course.total_weeks = 14
        mock_course.department_id = 1
        mock_course.professor_id = 1

        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.all.return_value = [mock_course]

        # Exercise
        result = course_repository.list(department_id=1)

        # Verify
        mock_session.query.assert_called_once_with(CourseModel)
        query_mock.filter_by.assert_called_once_with(department_id=1)
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].department_id == 1

    def test_update(self, course_repository, mock_session, mock_course_model):
        """Test updating a course."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_course_model

        # Create course to update
        course = Course(
            id=1,
            code="CS101-NEW",
            title="Updated Introduction to Programming",
            credits=4,
            description="Updated programming concepts",
            lectures_per_week=3,
            level="Graduate",
            total_weeks=15,
            department_id=2,
            professor_id=2,
        )

        # Exercise
        result = course_repository.update(course)

        # Verify
        mock_session.query.assert_called_once_with(CourseModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        mock_session.commit.assert_called_once()

        # Check that the model was updated with new values
        assert mock_course_model.code == "CS101-NEW"
        assert mock_course_model.title == "Updated Introduction to Programming"
        assert mock_course_model.credits == 4
        assert mock_course_model.description == "Updated programming concepts"
        assert mock_course_model.lectures_per_week == 3
        assert mock_course_model.level == "Graduate"
        assert mock_course_model.total_weeks == 15
        assert mock_course_model.department_id == 2
        assert mock_course_model.professor_id == 2

        # Check that the returned course has the updated values
        assert result.id == 1
        assert result.code == "CS101-NEW"
        assert result.title == "Updated Introduction to Programming"
        assert result.credits == 4
        assert result.description == "Updated programming concepts"
        assert result.lectures_per_week == 3
        assert result.level == "Graduate"
        assert result.total_weeks == 15
        assert result.department_id == 2
        assert result.professor_id == 2

    def test_update_not_found(self, course_repository, mock_session):
        """Test updating a non-existent course raises an error."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Create course to update
        course = Course(
            id=999,
            code="CS999",
            title="Non-existent Course",
            credits=3,
            description="This course doesn't exist",
            lectures_per_week=2,
            level="Undergraduate",
            total_weeks=14,
            department_id=1,
            professor_id=1,
        )

        # Exercise & Verify
        with pytest.raises(ValueError, match="Course with ID 999 not found"):
            course_repository.update(course)

    def test_delete(self, course_repository, mock_session, mock_course_model):
        """Test deleting a course."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_course_model

        # Exercise
        result = course_repository.delete(1)

        # Verify
        mock_session.query.assert_called_once_with(CourseModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        mock_session.delete.assert_called_once_with(mock_course_model)
        mock_session.commit.assert_called_once()
        assert result is True

    def test_delete_not_found(self, course_repository, mock_session):
        """Test deleting a non-existent course returns False."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Exercise
        result = course_repository.delete(999)

        # Verify
        assert result is False
