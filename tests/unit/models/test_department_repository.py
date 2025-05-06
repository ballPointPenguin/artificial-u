"""
Unit tests for DepartmentRepository.
"""

from unittest.mock import MagicMock, call

import pytest

from artificial_u.models.core import Department
from artificial_u.models.database import CourseModel, DepartmentModel, ProfessorModel
from artificial_u.models.repositories.department import DepartmentRepository


@pytest.mark.unit
class TestDepartmentRepository:
    """Test the DepartmentRepository class."""

    @pytest.fixture
    def department_repository(self, repository_with_session):
        """Create a DepartmentRepository with a mock session."""
        return repository_with_session(DepartmentRepository)

    @pytest.fixture
    def mock_dept_model(self):
        """Create a mock department model for testing."""
        mock_dept = MagicMock(spec=DepartmentModel)
        mock_dept.id = 1
        mock_dept.name = "Computer Science"
        mock_dept.code = "CS"
        mock_dept.faculty = "Engineering"
        mock_dept.description = "Study of computers"
        return mock_dept

    def test_create(self, department_repository, mock_session):
        """Test creating a department."""

        # Configure mock behaviors
        def mock_refresh(model):
            model.id = 1

        mock_session.refresh.side_effect = mock_refresh

        # Create department to test
        dept = Department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
            description="Study of computers",
        )

        # Exercise
        result = department_repository.create(dept)

        # Verify
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called
        assert result.id == 1
        assert result.name == "Computer Science"
        assert result.code == "CS"
        assert result.faculty == "Engineering"
        assert result.description == "Study of computers"

    def test_get(self, department_repository, mock_session, mock_dept_model):
        """Test getting a department by ID."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_dept_model

        # Exercise
        result = department_repository.get(1)

        # Verify
        mock_session.query.assert_called_once_with(DepartmentModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        assert result.id == 1
        assert result.name == "Computer Science"
        assert result.code == "CS"
        assert result.faculty == "Engineering"
        assert result.description == "Study of computers"

    def test_get_not_found(self, department_repository, mock_session):
        """Test getting a non-existent department returns None."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Exercise
        result = department_repository.get(999)

        # Verify
        assert result is None

    def test_get_by_code(self, department_repository, mock_session, mock_dept_model):
        """Test getting a department by code."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_dept_model

        # Exercise
        result = department_repository.get_by_code("CS")

        # Verify
        mock_session.query.assert_called_once_with(DepartmentModel)
        query_mock.filter_by.assert_called_once_with(code="CS")
        assert result.id == 1
        assert result.name == "Computer Science"
        assert result.code == "CS"

    def test_list(self, department_repository, mock_session):
        """Test listing departments."""
        # Configure mock behavior
        mock_dept1 = MagicMock(spec=DepartmentModel)
        mock_dept1.id = 1
        mock_dept1.name = "Computer Science"
        mock_dept1.code = "CS"
        mock_dept1.faculty = "Engineering"
        mock_dept1.description = "Study of computers"

        mock_dept2 = MagicMock(spec=DepartmentModel)
        mock_dept2.id = 2
        mock_dept2.name = "Mathematics"
        mock_dept2.code = "MATH"
        mock_dept2.faculty = "Science"
        mock_dept2.description = "Study of numbers"

        query_mock = mock_session.query.return_value
        query_mock.all.return_value = [mock_dept1, mock_dept2]

        # Exercise
        result = department_repository.list()

        # Verify
        mock_session.query.assert_called_once_with(DepartmentModel)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == "Computer Science"
        assert result[1].id == 2
        assert result[1].name == "Mathematics"

    def test_list_with_faculty_filter(self, department_repository, mock_session):
        """Test listing departments with faculty filter."""
        # Configure mock behavior
        mock_dept = MagicMock(spec=DepartmentModel)
        mock_dept.id = 1
        mock_dept.name = "Computer Science"
        mock_dept.code = "CS"
        mock_dept.faculty = "Engineering"
        mock_dept.description = "Study of computers"

        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.all.return_value = [mock_dept]

        # Exercise
        result = department_repository.list(faculty="Engineering")

        # Verify
        mock_session.query.assert_called_once_with(DepartmentModel)
        query_mock.filter_by.assert_called_once_with(faculty="Engineering")
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].faculty == "Engineering"

    def test_update(self, department_repository, mock_session, mock_dept_model):
        """Test updating a department."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_dept_model

        # Create department to update
        dept = Department(
            id=1,
            name="Updated Computer Science",
            code="CS-NEW",
            faculty="Updated Engineering",
            description="Updated description",
        )

        # Exercise
        result = department_repository.update(dept)

        # Verify
        mock_session.query.assert_called_once_with(DepartmentModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        mock_session.commit.assert_called_once()

        # Check that the model was updated with new values
        assert mock_dept_model.name == "Updated Computer Science"
        assert mock_dept_model.code == "CS-NEW"
        assert mock_dept_model.faculty == "Updated Engineering"
        assert mock_dept_model.description == "Updated description"

        # Check that the returned department has the updated values
        assert result.id == 1
        assert result.name == "Updated Computer Science"
        assert result.code == "CS-NEW"
        assert result.faculty == "Updated Engineering"
        assert result.description == "Updated description"

    def test_update_not_found(self, department_repository, mock_session):
        """Test updating a non-existent department raises an error."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Create department to update
        dept = Department(
            id=999,
            name="Updated Computer Science",
            code="CS-NEW",
            faculty="Updated Engineering",
            description="Updated description",
        )

        # Exercise & Verify
        with pytest.raises(ValueError, match="Department with ID 999 not found"):
            department_repository.update(dept)

    def test_delete(self, department_repository, mock_session, mock_dept_model):
        """Test deleting a department."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_dept_model

        # Reset mock_session.query to track different calls
        mock_session.query.reset_mock()

        # Exercise
        result = department_repository.delete(1)

        # Verify
        mock_session.query.assert_has_calls(
            [
                # First call to check if department exists
                call(DepartmentModel),
                # Second call to update professors
                call(ProfessorModel),
                # Third call to update courses
                call(CourseModel),
            ],
            any_order=True,
        )

        # We can't easily check filter_by calls since we've reused the same mock
        # But we can check that delete and commit were called
        mock_session.delete.assert_called_once_with(mock_dept_model)
        mock_session.commit.assert_called_once()
        assert result is True

    def test_delete_not_found(self, department_repository, mock_session):
        """Test deleting a non-existent department returns False."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Exercise
        result = department_repository.delete(999)

        # Verify
        assert result is False
        mock_session.delete.assert_not_called()
