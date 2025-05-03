"""
Unit tests for DepartmentRepository.
"""

from unittest.mock import MagicMock, call, patch

import pytest

from artificial_u.models.core import Department
from artificial_u.models.database import CourseModel, DepartmentModel, ProfessorModel
from artificial_u.models.repositories.department import DepartmentRepository


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
class TestDepartmentRepository:
    """Test the DepartmentRepository class."""

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_create(self, mock_get_session):
        """Test creating a department."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock department model that will be returned after the commit
        mock_dept_model = MagicMock(spec=DepartmentModel)
        mock_dept_model.id = 1
        mock_dept_model.name = "Computer Science"
        mock_dept_model.code = "CS"
        mock_dept_model.faculty = "Engineering"
        mock_dept_model.description = "Study of computers"

        # Set up the refresh to set the ID
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
        repo = DepartmentRepository()
        result = repo.create(dept)

        # Verify
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called
        assert result.id == 1
        assert result.name == "Computer Science"
        assert result.code == "CS"
        assert result.faculty == "Engineering"
        assert result.description == "Study of computers"

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_get(self, mock_get_session):
        """Test getting a department by ID."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock department model
        mock_dept_model = MagicMock(spec=DepartmentModel)
        mock_dept_model.id = 1
        mock_dept_model.name = "Computer Science"
        mock_dept_model.code = "CS"
        mock_dept_model.faculty = "Engineering"
        mock_dept_model.description = "Study of computers"

        mock_session.first.return_value = mock_dept_model

        # Exercise
        repo = DepartmentRepository()
        result = repo.get(1)

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(id=1)
        assert result.id == 1
        assert result.name == "Computer Science"
        assert result.code == "CS"
        assert result.faculty == "Engineering"
        assert result.description == "Study of computers"

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_get_not_found(self, mock_get_session):
        """Test getting a non-existent department returns None."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        mock_session.first.return_value = None

        # Exercise
        repo = DepartmentRepository()
        result = repo.get(999)

        # Verify
        assert result is None

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_get_by_code(self, mock_get_session):
        """Test getting a department by code."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock department model
        mock_dept_model = MagicMock(spec=DepartmentModel)
        mock_dept_model.id = 1
        mock_dept_model.name = "Computer Science"
        mock_dept_model.code = "CS"
        mock_dept_model.faculty = "Engineering"
        mock_dept_model.description = "Study of computers"

        mock_session.first.return_value = mock_dept_model

        # Exercise
        repo = DepartmentRepository()
        result = repo.get_by_code("CS")

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(code="CS")
        assert result.id == 1
        assert result.name == "Computer Science"
        assert result.code == "CS"

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_list(self, mock_get_session):
        """Test listing departments."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create mock department models
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

        mock_session.all.return_value = [mock_dept1, mock_dept2]

        # Exercise
        repo = DepartmentRepository()
        result = repo.list()

        # Verify
        mock_session.query.assert_called_once()
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == "Computer Science"
        assert result[1].id == 2
        assert result[1].name == "Mathematics"

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_list_with_faculty_filter(self, mock_get_session):
        """Test listing departments with faculty filter."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create mock department model
        mock_dept = MagicMock(spec=DepartmentModel)
        mock_dept.id = 1
        mock_dept.name = "Computer Science"
        mock_dept.code = "CS"
        mock_dept.faculty = "Engineering"
        mock_dept.description = "Study of computers"

        mock_session.all.return_value = [mock_dept]

        # Exercise
        repo = DepartmentRepository()
        result = repo.list(faculty="Engineering")

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(faculty="Engineering")
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].faculty == "Engineering"

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_update(self, mock_get_session):
        """Test updating a department."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock department model
        mock_dept_model = MagicMock(spec=DepartmentModel)
        mock_dept_model.id = 1
        mock_session.first.return_value = mock_dept_model

        # Create department to update
        dept = Department(
            id=1,
            name="Updated Computer Science",
            code="CS-NEW",
            faculty="Updated Engineering",
            description="Updated description",
        )

        # Exercise
        repo = DepartmentRepository()
        result = repo.update(dept)

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(id=1)
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

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_update_not_found(self, mock_get_session):
        """Test updating a non-existent department raises an error."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        mock_session.first.return_value = None

        # Create department to update
        dept = Department(
            id=999,
            name="Updated Computer Science",
            code="CS-NEW",
            faculty="Updated Engineering",
            description="Updated description",
        )

        # Exercise & Verify
        repo = DepartmentRepository()
        with pytest.raises(ValueError, match="Department with ID 999 not found"):
            repo.update(dept)

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_delete(self, mock_get_session):
        """Test deleting a department."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock department model
        mock_dept_model = MagicMock(spec=DepartmentModel)
        mock_dept_model.id = 1
        mock_session.first.return_value = mock_dept_model

        # Exercise
        repo = DepartmentRepository()
        result = repo.delete(1)

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

        mock_session.filter_by.assert_has_calls(
            [call(id=1), call(department_id=1), call(department_id=1)], any_order=True
        )

        mock_session.delete.assert_called_once_with(mock_dept_model)
        mock_session.commit.assert_called_once()
        assert result is True

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_delete_not_found(self, mock_get_session):
        """Test deleting a non-existent department returns False."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        mock_session.first.return_value = None

        # Exercise
        repo = DepartmentRepository()
        result = repo.delete(999)

        # Verify
        assert result is False
        mock_session.delete.assert_not_called()

    @patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"})
    @patch("artificial_u.models.repositories.department.DepartmentRepository.get_session")
    def test_list_department_names(self, mock_get_session):
        """Test listing department names."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Mock the query result
        mock_session.all.return_value = [("Computer Science",), ("Mathematics",)]

        # Exercise
        repo = DepartmentRepository()
        result = repo.list_department_names()

        # Verify
        mock_session.query.assert_called_once()
        assert len(result) == 2
        assert result == ["Computer Science", "Mathematics"]
