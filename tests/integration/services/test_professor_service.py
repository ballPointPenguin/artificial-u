"""
Integration tests for ProfessorService.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.config import get_settings
from artificial_u.models.core import Professor
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import DepartmentService, ProfessorService
from artificial_u.utils import GenerationError, ProfessorNotFoundError

# Example AI-generated XML response for professor
MOCK_PROFESSOR_XML = """
<output>
  <professor>
    <name>Dr. Maria Garcia</name>
    <title>Associate Professor</title>
    <specialization>Artificial Intelligence</specialization>
    <gender>Female</gender>
    <age>42</age>
    <accent>Spanish</accent>
    <description>Expert in AI and cognitive computing</description>
    <background>Ph.D. from Stanford University</background>
    <personality>Enthusiastic and engaging</personality>
    <teaching_style>Interactive and hands-on</teaching_style>
  </professor>
</output>
"""


@pytest.fixture
def repository_factory():
    """Create a repository factory that uses the test database."""
    # The DATABASE_URL will be picked up from .env.test
    return RepositoryFactory()


@pytest.fixture
def department_service(repository_factory, content_service):
    """Create a DepartmentService with mocked dependent services."""
    professor_service_mock = MagicMock()
    course_service_mock = MagicMock()

    return DepartmentService(
        repository_factory=repository_factory,
        professor_service=professor_service_mock,
        course_service=course_service_mock,
        content_service=content_service,
    )


@pytest.fixture
def professor_service(repository_factory, content_service, image_service, voice_service):
    """Create a ProfessorService with mocked dependent services."""
    return ProfessorService(
        repository_factory=repository_factory,
        content_service=content_service,
        image_service=image_service,
        voice_service=voice_service,
    )


@pytest.fixture
def content_service():
    """Create a mock ContentService with async support."""
    mock = MagicMock()
    mock.generate_text = AsyncMock(return_value=MOCK_PROFESSOR_XML)
    return mock


@pytest.fixture
def image_service():
    """Create a mock ImageService with async support."""
    mock = MagicMock()
    mock.generate_professor_image = AsyncMock(return_value="professors/test-image-key.jpg")
    mock.storage_service = MagicMock()
    mock.storage_service.get_file_url = MagicMock(
        return_value="https://storage.example.com/professors/test-image-key.jpg"
    )
    mock.storage_service.images_bucket = "test-bucket"
    return mock


@pytest.fixture
def voice_service():
    """Create a mock VoiceService."""
    return MagicMock()


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

    @pytest.mark.asyncio
    async def test_generate_professor_profile(self, professor_service, department_service):
        """Test generating professor profile with mocked AI response."""
        # Create a department first
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        # Mock the content service's generate_text method
        professor_service.content_service.generate_text.return_value = MOCK_PROFESSOR_XML

        # Generate professor profile
        professor_data = await professor_service.generate_professor(
            {"department_id": department.id, "freeform_prompt": "Focus on AI expertise"}
        )

        # Verify the generated content
        assert professor_data["name"] == "Dr. Maria Garcia"
        assert professor_data["title"] == "Associate Professor"
        assert professor_data["specialization"] == "Artificial Intelligence"
        assert professor_data["gender"] == "Female"
        assert professor_data["age"] == 42
        assert professor_data["accent"] == "Spanish"
        assert "AI" in professor_data["description"]

        # Verify content service was called with correct arguments
        professor_service.content_service.generate_text.assert_called_once()
        call_args = professor_service.content_service.generate_text.call_args
        assert call_args.kwargs["model"] == get_settings().PROFESSOR_GENERATION_MODEL
        assert "system_prompt" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_generate_professor_profile_error_handling(self, professor_service):
        """Test error handling in professor profile generation."""
        # Test invalid XML response
        professor_service.content_service.generate_text = AsyncMock(
            return_value="<invalid>XML</invalid>"
        )

        with pytest.raises(GenerationError) as exc_info:
            await professor_service.generate_professor({})
        assert "Failed to parse AI-generated professor profile." in str(exc_info.value)

        # Test empty response
        professor_service.content_service.generate_text = AsyncMock(return_value="")

        with pytest.raises(GenerationError) as exc_info:
            await professor_service.generate_professor({})
        assert "AI generation returned empty content" in str(exc_info.value)

        # Test exception in content service
        professor_service.content_service.generate_text = AsyncMock(
            side_effect=Exception("API Error")
        )

        with pytest.raises(GenerationError) as exc_info:
            await professor_service.generate_professor({})
        assert "AI content generation call failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_and_set_professor_image(self, professor_service, department_service):
        """Test generating and setting professor image."""
        # Create a department and professor first
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        professor = professor_service.create_professor(
            Professor(
                name="Dr. Test Image",
                title="Professor",
                department_id=department.id,
                specialization="Image Processing",
                gender="Other",
            )
        )

        # Generate and set image
        updated_professor = await professor_service.generate_and_set_professor_image(
            professor_id=professor.id, aspect_ratio="1:1"
        )

        # Verify the image was set
        assert (
            updated_professor.image_url
            == "https://storage.example.com/professors/test-image-key.jpg"
        )

        # Verify service calls
        professor_service.image_service.generate_professor_image.assert_called_once_with(
            professor=professor, aspect_ratio="1:1"
        )
        professor_service.image_service.storage_service.get_file_url.assert_called_once_with(
            bucket="test-bucket", object_name="professors/test-image-key.jpg"
        )
