"""
Unit tests for ProfessorRepository.
"""

from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Professor
from artificial_u.models.database import ProfessorModel
from artificial_u.models.repositories.professor import ProfessorRepository


@pytest.mark.unit
class TestProfessorRepository:
    """Test the ProfessorRepository class."""

    @pytest.fixture
    def professor_repository(self, repository_with_session):
        """Create a ProfessorRepository with a mock session."""
        return repository_with_session(ProfessorRepository)

    @pytest.fixture
    def mock_prof_model(self):
        """Create a mock professor model for testing."""
        mock_prof = MagicMock(spec=ProfessorModel)
        mock_prof.id = 1
        mock_prof.name = "Dr. Jane Smith"
        mock_prof.title = "Associate Professor"
        mock_prof.department_id = 1
        mock_prof.specialization = "Machine Learning"
        mock_prof.background = "PhD from Stanford"
        mock_prof.personality = "Engaging and enthusiastic"
        mock_prof.teaching_style = "Interactive with hands-on examples"
        mock_prof.gender = "Female"
        mock_prof.accent = "American"
        mock_prof.description = "Expert in machine learning"
        mock_prof.age = 35
        mock_prof.voice_id = 1
        mock_prof.image_url = "https://example.com/smith.jpg"
        return mock_prof

    def test_create(self, professor_repository, mock_session):
        """Test creating a professor."""

        # Configure mock behaviors
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
        result = professor_repository.create(professor)

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

    def test_get(self, professor_repository, mock_session, mock_prof_model):
        """Test getting a professor by ID."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_prof_model

        # Exercise
        result = professor_repository.get(1)

        # Verify
        mock_session.query.assert_called_once_with(ProfessorModel)
        query_mock.filter_by.assert_called_once_with(id=1)
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

    def test_get_not_found(self, professor_repository, mock_session):
        """Test getting a non-existent professor returns None."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Exercise
        result = professor_repository.get(999)

        # Verify
        assert result is None

    def test_list(self, professor_repository, mock_session):
        """Test listing professors."""
        # Configure mock behavior
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

        query_mock = mock_session.query.return_value
        query_mock.all.return_value = [mock_prof1, mock_prof2]

        # Exercise
        result = professor_repository.list()

        # Verify
        mock_session.query.assert_called_once_with(ProfessorModel)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == "Dr. Jane Smith"
        assert result[1].id == 2
        assert result[1].name == "Dr. John Doe"

    def test_list_by_department(self, professor_repository, mock_session):
        """Test listing professors by department."""
        # Configure mock behavior with proper string values
        mock_prof = MagicMock(spec=ProfessorModel)

        # Set required fields
        mock_prof.id = 1
        mock_prof.name = "Dr. Jane Smith"
        mock_prof.department_id = 1

        # Configure all string fields to return string values, not MagicMock objects
        mock_prof.title = "Associate Professor"
        mock_prof.specialization = "Machine Learning"
        mock_prof.background = "PhD from Stanford"
        mock_prof.personality = "Engaging"
        mock_prof.teaching_style = "Interactive"
        mock_prof.gender = "Female"
        mock_prof.accent = "American"
        mock_prof.description = "Expert"
        mock_prof.image_url = "https://example.com/image.jpg"
        mock_prof.age = 35
        mock_prof.voice_id = 1

        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.all.return_value = [mock_prof]

        # Exercise
        result = professor_repository.list_by_department(1)

        # Verify
        mock_session.query.assert_called_once_with(ProfessorModel)
        query_mock.filter_by.assert_called_once_with(department_id=1)
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].department_id == 1

    def test_update(self, professor_repository, mock_session, mock_prof_model):
        """Test updating a professor."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_prof_model

        # Create professor to update
        professor = Professor(
            id=1,
            name="Dr. Jane Smith Updated",
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
            image_url="https://example.com/smith_updated.jpg",
        )

        # Exercise
        result = professor_repository.update(professor)

        # Verify
        mock_session.query.assert_called_once_with(ProfessorModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        mock_session.commit.assert_called_once()

        # Check that the model was updated with new values
        assert mock_prof_model.name == "Dr. Jane Smith Updated"
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
        assert mock_prof_model.image_url == "https://example.com/smith_updated.jpg"

        # Check that the returned professor has the updated values
        assert result.id == 1
        assert result.name == "Dr. Jane Smith Updated"
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
        assert result.image_url == "https://example.com/smith_updated.jpg"

    def test_update_not_found(self, professor_repository, mock_session):
        """Test updating a non-existent professor raises an error."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Create professor to update
        professor = Professor(
            id=999,
            name="Dr. Jane Smith",
            title="Associate Professor",
            department_id=1,
        )

        # Exercise & Verify
        with pytest.raises(ValueError, match="Professor with ID 999 not found"):
            professor_repository.update(professor)

    def test_update_field(self, professor_repository, mock_session, mock_prof_model):
        """Test updating a single field of a professor."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_prof_model

        # Exercise
        result = professor_repository.update_field(1, title="Full Professor")

        # Verify
        mock_session.query.assert_called_once_with(ProfessorModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        mock_session.commit.assert_called_once()

        # Check that the model was updated with the new value
        assert mock_prof_model.title == "Full Professor"

        # Check that the returned professor has the updated value
        assert result.id == 1
        assert result.title == "Full Professor"

    def test_update_field_not_found(self, professor_repository, mock_session):
        """Test updating a field of a non-existent professor returns None."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Exercise & Verify
        result = professor_repository.update_field(999, title="Full Professor")
        assert result is None

    def test_delete(self, professor_repository, mock_session, mock_prof_model):
        """Test deleting a professor."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = mock_prof_model

        # Exercise
        result = professor_repository.delete(1)

        # Verify
        mock_session.query.assert_called_once_with(ProfessorModel)
        query_mock.filter_by.assert_called_once_with(id=1)
        mock_session.delete.assert_called_once_with(mock_prof_model)
        mock_session.commit.assert_called_once()
        assert result is True

    def test_delete_not_found(self, professor_repository, mock_session):
        """Test deleting a non-existent professor returns False."""
        # Configure mock behavior
        query_mock = mock_session.query.return_value
        query_mock.filter_by.return_value.first.return_value = None

        # Exercise
        result = professor_repository.delete(999)

        # Verify
        assert result is False
