"""
Unit tests for ProfessorRepository.
"""

from unittest.mock import MagicMock, patch

import pytest

from artificial_u.models.core import Professor
from artificial_u.models.database import ProfessorModel
from artificial_u.models.repositories.professor import ProfessorRepository


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
class TestProfessorRepository:
    """Test the ProfessorRepository class."""

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_create(self, mock_get_session):
        """Test creating a professor."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Set up the refresh to set the ID
        def mock_refresh(model):
            model.id = 1

        mock_session.refresh.side_effect = mock_refresh

        # Create professor to test
        professor = Professor(
            name="Dr. Jane Smith",
            title="Associate Professor",
            department_id=1,
            specialization="Machine Learning",
            background="PhD from Stanford",
            personality="Engaging and enthusiastic",
            teaching_style="Interactive with hands-on examples",
            gender="Female",
            accent="American",
            description="Expert in machine learning",
            age=35,
            voice_id=1,
            image_url="https://example.com/smith.jpg",
        )

        # Exercise
        repo = ProfessorRepository()
        result = repo.create(professor)

        # Verify
        assert mock_session.add.called
        assert mock_session.commit.called
        assert mock_session.refresh.called
        assert result.id == 1
        assert result.name == "Dr. Jane Smith"
        assert result.title == "Associate Professor"
        assert result.department_id == 1
        assert result.specialization == "Machine Learning"
        assert result.background == "PhD from Stanford"
        assert result.personality == "Engaging and enthusiastic"
        assert result.teaching_style == "Interactive with hands-on examples"
        assert result.gender == "Female"
        assert result.accent == "American"
        assert result.description == "Expert in machine learning"
        assert result.age == 35
        assert result.voice_id == 1
        assert result.image_url == "https://example.com/smith.jpg"

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_get(self, mock_get_session):
        """Test getting a professor by ID."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock professor model
        mock_prof_model = MagicMock(spec=ProfessorModel)
        mock_prof_model.id = 1
        mock_prof_model.name = "Dr. Jane Smith"
        mock_prof_model.title = "Associate Professor"
        mock_prof_model.department_id = 1
        mock_prof_model.specialization = "Machine Learning"
        mock_prof_model.background = "PhD from Stanford"
        mock_prof_model.personality = "Engaging and enthusiastic"
        mock_prof_model.teaching_style = "Interactive with hands-on examples"
        mock_prof_model.gender = "Female"
        mock_prof_model.accent = "American"
        mock_prof_model.description = "Expert in machine learning"
        mock_prof_model.age = 35
        mock_prof_model.voice_id = 1
        mock_prof_model.image_url = "https://example.com/smith.jpg"

        mock_session.first.return_value = mock_prof_model

        # Exercise
        repo = ProfessorRepository()
        result = repo.get(1)

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(id=1)
        assert result.id == 1
        assert result.name == "Dr. Jane Smith"
        assert result.title == "Associate Professor"
        assert result.department_id == 1
        assert result.specialization == "Machine Learning"
        assert result.background == "PhD from Stanford"
        assert result.personality == "Engaging and enthusiastic"
        assert result.teaching_style == "Interactive with hands-on examples"
        assert result.gender == "Female"
        assert result.accent == "American"
        assert result.description == "Expert in machine learning"
        assert result.age == 35
        assert result.voice_id == 1
        assert result.image_url == "https://example.com/smith.jpg"

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_get_not_found(self, mock_get_session):
        """Test getting a non-existent professor returns None."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        mock_session.first.return_value = None

        # Exercise
        repo = ProfessorRepository()
        result = repo.get(999)

        # Verify
        assert result is None

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_list(self, mock_get_session):
        """Test listing professors."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create mock professor models
        mock_prof1 = MagicMock(spec=ProfessorModel)
        mock_prof1.id = 1
        mock_prof1.name = "Dr. Jane Smith"
        mock_prof1.title = "Associate Professor"
        mock_prof1.department_id = 1
        mock_prof1.specialization = "Machine Learning"
        mock_prof1.background = "PhD from Stanford"
        mock_prof1.personality = "Engaging and enthusiastic"
        mock_prof1.teaching_style = "Interactive with hands-on examples"
        mock_prof1.gender = "Female"
        mock_prof1.accent = "American"
        mock_prof1.description = "Expert in machine learning"
        mock_prof1.age = 35
        mock_prof1.voice_id = 1
        mock_prof1.image_url = "https://example.com/smith.jpg"

        mock_prof2 = MagicMock(spec=ProfessorModel)
        mock_prof2.id = 2
        mock_prof2.name = "Dr. John Doe"
        mock_prof2.title = "Professor"
        mock_prof2.department_id = 2
        mock_prof2.specialization = "Databases"
        mock_prof2.background = "20 years in industry"
        mock_prof2.personality = "Methodical and precise"
        mock_prof2.teaching_style = "Lecture-based with frequent examples"
        mock_prof2.gender = "Male"
        mock_prof2.accent = "British"
        mock_prof2.description = "Database expert"
        mock_prof2.age = 45
        mock_prof2.voice_id = 2
        mock_prof2.image_url = "https://example.com/doe.jpg"

        mock_session.all.return_value = [mock_prof1, mock_prof2]

        # Exercise
        repo = ProfessorRepository()
        result = repo.list()

        # Verify
        mock_session.query.assert_called_once()
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == "Dr. Jane Smith"
        assert result[1].id == 2
        assert result[1].name == "Dr. John Doe"

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_update(self, mock_get_session):
        """Test updating a professor."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock professor model
        mock_prof_model = MagicMock(spec=ProfessorModel)
        mock_prof_model.id = 1
        mock_session.first.return_value = mock_prof_model

        # Create professor to update
        professor = Professor(
            id=1,
            name="Dr. Jane Smith-Updated",
            title="Full Professor",
            department_id=2,
            specialization="Deep Learning",
            background="Updated background",
            personality="Updated personality",
            teaching_style="Updated teaching style",
            gender="Female",
            accent="British",
            description="Updated description",
            age=36,
            voice_id=2,
            image_url="https://example.com/smith-updated.jpg",
        )

        # Exercise
        repo = ProfessorRepository()
        result = repo.update(professor)

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(id=1)
        mock_session.commit.assert_called_once()

        # Check that the model was updated with new values
        assert mock_prof_model.name == "Dr. Jane Smith-Updated"
        assert mock_prof_model.title == "Full Professor"
        assert mock_prof_model.department_id == 2
        assert mock_prof_model.specialization == "Deep Learning"
        assert mock_prof_model.background == "Updated background"
        assert mock_prof_model.personality == "Updated personality"
        assert mock_prof_model.teaching_style == "Updated teaching style"
        assert mock_prof_model.gender == "Female"
        assert mock_prof_model.accent == "British"
        assert mock_prof_model.description == "Updated description"
        assert mock_prof_model.age == 36
        assert mock_prof_model.voice_id == 2
        assert mock_prof_model.image_url == "https://example.com/smith-updated.jpg"

        # Check that the returned professor has the updated values
        assert result.id == 1
        assert result.name == "Dr. Jane Smith-Updated"
        assert result.title == "Full Professor"
        assert result.department_id == 2
        assert result.specialization == "Deep Learning"
        assert result.background == "Updated background"
        assert result.personality == "Updated personality"
        assert result.teaching_style == "Updated teaching style"
        assert result.gender == "Female"
        assert result.accent == "British"
        assert result.description == "Updated description"
        assert result.age == 36
        assert result.voice_id == 2
        assert result.image_url == "https://example.com/smith-updated.jpg"

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_update_not_found(self, mock_get_session):
        """Test updating a non-existent professor raises an error."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        mock_session.first.return_value = None

        # Create professor to update
        professor = Professor(
            id=999,
            name="Dr. Nonexistent",
            title="Professor",
            department_id=1,
            specialization="Nonexistent",
            background="Nonexistent",
            personality="Nonexistent",
            teaching_style="Nonexistent",
        )

        # Exercise & Verify
        repo = ProfessorRepository()
        with pytest.raises(ValueError, match="Professor with ID 999 not found"):
            repo.update(professor)

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_update_field(self, mock_get_session):
        """Test updating specific fields of a professor."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock professor model
        mock_prof_model = MagicMock(spec=ProfessorModel)
        mock_prof_model.id = 1
        mock_prof_model.name = "Dr. Jane Smith"
        mock_prof_model.title = "Associate Professor"
        mock_prof_model.department_id = 1
        mock_prof_model.specialization = "Machine Learning"
        mock_prof_model.background = "PhD from Stanford"
        mock_prof_model.personality = "Engaging and enthusiastic"
        mock_prof_model.teaching_style = "Interactive with hands-on examples"
        mock_prof_model.gender = "Female"
        mock_prof_model.accent = "American"
        mock_prof_model.description = "Expert in machine learning"
        mock_prof_model.age = 35
        mock_prof_model.voice_id = 1
        mock_prof_model.image_url = "https://example.com/smith.jpg"

        mock_session.first.return_value = mock_prof_model

        # Exercise
        repo = ProfessorRepository()
        result = repo.update_field(1, title="Full Professor", specialization="Deep Learning")

        # Verify
        mock_session.query.assert_called_once()
        mock_session.filter_by.assert_called_once_with(id=1)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

        # Check that only specified fields were updated
        assert mock_prof_model.title == "Full Professor"
        assert mock_prof_model.specialization == "Deep Learning"

        # Other fields should remain unchanged
        assert mock_prof_model.name == "Dr. Jane Smith"
        assert mock_prof_model.department_id == 1

        # Check returned professor
        assert result.id == 1
        assert result.title == "Full Professor"
        assert result.specialization == "Deep Learning"

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_update_field_not_found(self, mock_get_session):
        """Test updating fields of a non-existent professor returns None."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        mock_session.first.return_value = None

        # Exercise
        repo = ProfessorRepository()
        result = repo.update_field(999, title="Full Professor")

        # Verify
        assert result is None
        mock_session.commit.assert_not_called()

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_delete(self, mock_get_session):
        """Test deleting a professor."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create a mock professor model
        mock_prof_model = MagicMock(spec=ProfessorModel)
        mock_prof_model.id = 1
        mock_session.first.return_value = mock_prof_model

        # Exercise
        repo = ProfessorRepository()
        result = repo.delete(1)

        # Verify
        mock_session.query.assert_called_once_with(ProfessorModel)
        mock_session.filter_by.assert_called_once_with(id=1)
        mock_session.delete.assert_called_once_with(mock_prof_model)
        mock_session.commit.assert_called_once()
        assert result is True

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_delete_not_found(self, mock_get_session):
        """Test deleting a non-existent professor returns False."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session
        mock_session.first.return_value = None

        # Exercise
        repo = ProfessorRepository()
        result = repo.delete(999)

        # Verify
        assert result is False
        mock_session.delete.assert_not_called()

    @patch("artificial_u.models.repositories.professor.ProfessorRepository.get_session")
    def test_list_by_department(self, mock_get_session):
        """Test listing professors by department."""
        # Setup
        mock_session = MockSession()
        mock_get_session.return_value = mock_session

        # Create mock professor models
        mock_prof1 = MagicMock(spec=ProfessorModel)
        mock_prof1.id = 1
        mock_prof1.name = "Dr. Jane Smith"
        mock_prof1.title = "Associate Professor"
        mock_prof1.department_id = 1
        mock_prof1.specialization = "Machine Learning"
        mock_prof1.background = "PhD from Stanford"
        mock_prof1.personality = "Engaging and enthusiastic"
        mock_prof1.teaching_style = "Interactive with hands-on examples"
        mock_prof1.gender = "Female"
        mock_prof1.accent = "American"
        mock_prof1.description = "Expert in machine learning"
        mock_prof1.age = 35
        mock_prof1.voice_id = 1
        mock_prof1.image_url = "https://example.com/smith.jpg"

        mock_session.all.return_value = [mock_prof1]

        # Exercise
        repo = ProfessorRepository()
        result = repo.list_by_department(department_id=1)

        # Verify
        mock_session.query.assert_called_once_with(ProfessorModel)
        mock_session.filter_by.assert_called_once_with(department_id=1)
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].name == "Dr. Jane Smith"
        assert result[0].department_id == 1
