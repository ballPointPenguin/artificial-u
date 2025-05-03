"""
Integration tests for ProfessorService.
"""

from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Professor
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import DepartmentService, ProfessorService
from artificial_u.utils import ProfessorNotFoundError


@pytest.fixture
def repository_factory():
    """Create a repository factory that uses the test database."""
    # The DATABASE_URL will be picked up from .env.test
    return RepositoryFactory()


@pytest.fixture
def department_service(repository_factory):
    """Create a DepartmentService with mocked dependent services."""
    professor_service_mock = MagicMock()
    course_service_mock = MagicMock()

    return DepartmentService(
        repository_factory=repository_factory,
        professor_service=professor_service_mock,
        course_service=course_service_mock,
    )


@pytest.fixture
def professor_service(repository_factory):
    """Create a ProfessorService with mocked dependent services."""
    content_service = MagicMock()
    image_service = MagicMock()
    voice_service = MagicMock()

    return ProfessorService(
        repository_factory=repository_factory,
        content_service=content_service,
        image_service=image_service,
        voice_service=voice_service,
    )


@pytest.mark.integration
class TestProfessorService:
    """Integration tests for ProfessorService."""

    def test_create_and_get_professor(self, professor_service):
        """Test creating and retrieving a professor."""
        # Create a new professor (without department)
        professor = professor_service.create_professor(
            Professor(
                name="Dr. John Doe",
                title="Associate Professor",
                specialization="Machine Learning",
                gender="Male",
                age=45,
                accent="American",
                description="Expert in AI and ML",
                background="Ph.D. from MIT",
                personality="Enthusiastic and patient",
                teaching_style="Interactive",
            )
        )

        # Verify it was created with an ID
        assert professor.id is not None
        assert professor.name == "Dr. John Doe"
        assert professor.specialization == "Machine Learning"

        # Retrieve the professor and verify
        retrieved = professor_service.get_professor(professor.id)
        assert retrieved.id == professor.id
        assert retrieved.name == "Dr. John Doe"
        assert retrieved.specialization == "Machine Learning"

    def test_update_professor(self, professor_service):
        """Test updating a professor."""
        # Create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Jane Smith",
                title="Assistant Professor",
                specialization="Quantum Computing",
                gender="Female",
                age=38,
                accent="British",
                description="Expert in quantum algorithms",
            )
        )

        # Update the professor
        updated = professor_service.update_professor(
            professor.id, {"name": "Dr. Jane A. Smith", "title": "Associate Professor"}
        )

        # Verify updates
        assert updated.name == "Dr. Jane A. Smith"
        assert updated.title == "Associate Professor"
        assert updated.specialization == "Quantum Computing"  # Unchanged field

        # Retrieve to confirm persistence
        retrieved = professor_service.get_professor(professor.id)
        assert retrieved.name == "Dr. Jane A. Smith"
        assert retrieved.title == "Associate Professor"

    def test_list_professors(self, professor_service, department_service):
        """Test listing professors with/without filters."""
        # First create departments for our professors
        dept1 = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        dept2 = department_service.create_department(
            name="Information Security",
            code="ISEC",
            faculty="Engineering",
        )

        # Create professors with the real department IDs
        professor_service.create_professor(
            Professor(
                name="Dr. Bob Johnson",
                title="Professor",
                specialization="Data Science",
                gender="Male",
                department_id=dept1.id,
            )
        )

        professor_service.create_professor(
            Professor(
                name="Dr. Sara Lee",
                title="Assistant Professor",
                specialization="Data Visualization",
                gender="Female",
                department_id=dept1.id,
            )
        )

        professor_service.create_professor(
            Professor(
                name="Dr. Mike Chen",
                title="Associate Professor",
                specialization="Systems Security",
                gender="Male",
                department_id=dept2.id,
            )
        )

        # List all professors
        all_profs = professor_service.list_professors()
        assert len(all_profs) >= 3  # At least our 3 (could be more if DB has existing data)

        # List by department_id
        dept1_profs = professor_service.list_professors(filters={"department_id": dept1.id})
        assert len(dept1_profs) >= 2
        names = [p.name for p in dept1_profs]
        assert "Dr. Bob Johnson" in names
        assert "Dr. Sara Lee" in names

        # List by partial name match
        data_profs = professor_service.list_professors(filters={"name": "Sara"})
        assert len(data_profs) >= 1
        assert any(p.name == "Dr. Sara Lee" for p in data_profs)

        # List by specialization
        data_profs = professor_service.list_professors(filters={"specialization": "Data"})
        assert len(data_profs) >= 2
        specs = [p.specialization for p in data_profs]
        assert "Data Science" in specs
        assert "Data Visualization" in specs

        # Test pagination
        page_profs = professor_service.list_professors(page=1, size=2)
        assert len(page_profs) == 2

    def test_get_professor_not_found(self, professor_service):
        """Test getting a non-existent professor raises appropriate error."""
        with pytest.raises(ProfessorNotFoundError):
            professor_service.get_professor(999999)

    def test_delete_professor(self, professor_service):
        """Test deleting a professor."""
        # Create a temporary professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Temp Delete",
                title="Adjunct Professor",
                specialization="To Be Deleted",
            )
        )

        # Delete it
        result = professor_service.delete_professor(professor.id)
        assert result is True

        # Verify it's gone
        with pytest.raises(ProfessorNotFoundError):
            professor_service.get_professor(professor.id)
