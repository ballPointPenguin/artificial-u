"""
Integration tests for LectureService.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.config import get_settings
from artificial_u.models.core import Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services import (
    CourseService,
    DepartmentService,
    LectureService,
    ProfessorService,
)
from artificial_u.utils.exceptions import ContentGenerationError, LectureNotFoundError

# Example AI-generated XML response
MOCK_LECTURE_XML = """
  <lecture>
    <title>Understanding Variables in Python</title>
    <week_number>1</week_number>
    <order_in_week>1</order_in_week>
    <description>Introduction to variables and data types in Python</description>
    <content>
    [Professor enters, smiling warmly]

    Good morning, everyone! Today we're going to explore one of the most fundamental
    concepts in programming: variables. Think of variables as labeled containers that
    can hold different types of data...

    [Writes 'x = 42' on the board]

    Let's start with a simple example...
  </content>
</lecture>"""


@pytest.fixture
def repository_factory():
    """Create a repository factory that uses the test database."""
    # The DATABASE_URL will be picked up from .env.test
    return RepositoryFactory()


@pytest.fixture
def content_service():
    """Create a mock ContentService with async support."""
    mock = MagicMock()
    # Set up generate_text as an AsyncMock
    mock.generate_text = AsyncMock()
    return mock


@pytest.fixture
def voice_service():
    """Create a mock VoiceService."""
    return MagicMock()


@pytest.fixture
def image_service():
    """Create a mock ImageService."""
    return MagicMock()


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
def course_service(repository_factory, professor_service, content_service):
    """Create a CourseService with actual ProfessorService and mocked ContentService."""
    return CourseService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        content_service=content_service,
    )


@pytest.fixture
def lecture_service(repository_factory, course_service, professor_service, content_service):
    """Create a LectureService with actual services and mocked ContentService."""
    return LectureService(
        repository_factory=repository_factory,
        content_service=content_service,
        course_service=course_service,
        professor_service=professor_service,
    )


@pytest.mark.integration
class TestLectureService:
    """Integration tests for LectureService."""

    def test_create_and_get_lecture(
        self, lecture_service, course_service, department_service, professor_service
    ):
        """Test creating and retrieving a lecture."""
        # First create a department
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
            description="Department of Computer Science and Engineering",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Alan Turing",
                title="Professor",
                department_id=department.id,
                specialization="Computation Theory",
                gender="Male",
                description="Pioneer in computer science",
            )
        )

        # Create a course
        course = course_service.create_course(
            title="Introduction to Programming",
            code="CS101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
            description="An introductory course to programming concepts",
            credits=3,
            weeks=14,
            lectures_per_week=2,
        )[0]

        # Create a new lecture
        lecture = lecture_service.create_lecture(
            title="Introduction to Variables",
            course_id=course.id,
            week_number=1,
            order_in_week=1,
            description="Understanding variables and data types",
            content="Today we will discuss variables...",
        )

        # Verify it was created with an ID
        assert lecture.id is not None
        assert lecture.title == "Introduction to Variables"
        assert lecture.course_id == course.id
        assert lecture.week_number == 1
        assert lecture.order_in_week == 1

        # Retrieve the lecture and verify
        retrieved = lecture_service.get_lecture(lecture.id)
        assert retrieved.id == lecture.id
        assert retrieved.title == "Introduction to Variables"
        assert retrieved.description == "Understanding variables and data types"
        assert retrieved.content == "Today we will discuss variables..."

    def test_get_lecture_by_course_week_order(
        self, lecture_service, course_service, department_service, professor_service
    ):
        """Test retrieving a lecture by its position in a course."""
        # Create department and professor
        department = department_service.create_department(
            name="Physics",
            code="PHYS",
            faculty="Science",
        )

        professor = professor_service.create_professor(
            Professor(
                name="Dr. Richard Feynman",
                title="Professor",
                department_id=department.id,
                specialization="Quantum Physics",
                gender="Male",
            )
        )

        # Create a course
        course = course_service.create_course(
            title="Quantum Mechanics",
            code="PHYS301",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create a lecture with specific position
        lecture = lecture_service.create_lecture(
            title="Wave Functions",
            course_id=course.id,
            week_number=3,
            order_in_week=2,
            description="Understanding wave functions",
        )

        # Retrieve by position and verify
        retrieved = lecture_service.get_lecture_by_course_week_order(
            course_id=course.id,
            week_number=3,
            order_in_week=2,
        )
        assert retrieved.id == lecture.id
        assert retrieved.title == "Wave Functions"
        assert retrieved.week_number == 3
        assert retrieved.order_in_week == 2

    def test_list_lectures(
        self, lecture_service, course_service, department_service, professor_service
    ):
        """Test listing lectures with various filters."""
        # Create department and professor
        department = department_service.create_department(
            name="Mathematics",
            code="MATH",
            faculty="Science",
        )

        professor = professor_service.create_professor(
            Professor(
                name="Dr. Ada Lovelace",
                title="Professor",
                department_id=department.id,
                specialization="Mathematical Analysis",
                gender="Female",
            )
        )

        # Create a course
        course = course_service.create_course(
            title="Calculus I",
            code="MATH201",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create multiple lectures
        lecture_service.create_lecture(
            title="Limits",
            course_id=course.id,
            week_number=1,
            order_in_week=1,
            description="Introduction to limits",
        )

        lecture_service.create_lecture(
            title="Derivatives",
            course_id=course.id,
            week_number=1,
            order_in_week=2,
            description="Basic differentiation",
        )

        # List all lectures for the course
        course_lectures = lecture_service.list_lectures(course_id=course.id)
        assert len(course_lectures) >= 2
        titles = [lecture.title for lecture in course_lectures]
        assert "Limits" in titles
        assert "Derivatives" in titles

        # Test pagination
        paged_lectures = lecture_service.list_lectures(course_id=course.id, page=1, size=1)
        assert len(paged_lectures) == 1

        # Test search
        search_results = lecture_service.list_lectures(search_query="limit")
        assert any(lecture.title == "Limits" for lecture in search_results)

    def test_update_lecture(
        self, lecture_service, course_service, department_service, professor_service
    ):
        """Test updating a lecture."""
        # Create necessary prerequisites
        department = department_service.create_department(
            name="Biology",
            code="BIO",
            faculty="Science",
        )

        professor = professor_service.create_professor(
            Professor(
                name="Dr. Rosalind Franklin",
                title="Professor",
                department_id=department.id,
                specialization="Molecular Biology",
                gender="Female",
            )
        )

        course = course_service.create_course(
            title="Molecular Biology",
            code="BIO301",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create a lecture
        lecture = lecture_service.create_lecture(
            title="DNA Structure",
            course_id=course.id,
            week_number=1,
            order_in_week=1,
            description="Basic DNA structure",
        )

        # Update the lecture
        updated = lecture_service.update_lecture(
            lecture.id,
            {
                "title": "Advanced DNA Structure",
                "description": "Detailed analysis of DNA structure",
                "content": "In this lecture, we will explore...",
            },
        )

        # Verify updates
        assert updated.title == "Advanced DNA Structure"
        assert updated.description == "Detailed analysis of DNA structure"
        assert updated.content == "In this lecture, we will explore..."
        # Unchanged fields
        assert updated.course_id == course.id
        assert updated.week_number == 1
        assert updated.order_in_week == 1

    def test_delete_lecture(
        self, lecture_service, course_service, department_service, professor_service
    ):
        """Test deleting a lecture."""
        # Create prerequisites
        department = department_service.create_department(
            name="Chemistry",
            code="CHEM",
            faculty="Science",
        )

        professor = professor_service.create_professor(
            Professor(
                name="Dr. Marie Curie",
                title="Professor",
                department_id=department.id,
                specialization="Radioactivity",
                gender="Female",
            )
        )

        course = course_service.create_course(
            title="Introduction to Chemistry",
            code="CHEM101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create a lecture to delete
        lecture = lecture_service.create_lecture(
            title="Lecture to Delete",
            course_id=course.id,
            week_number=1,
            order_in_week=1,
        )

        # Verify it exists
        retrieved = lecture_service.get_lecture(lecture.id)
        assert retrieved.id == lecture.id

        # Delete it
        result = lecture_service.delete_lecture(lecture.id)
        assert result is True

        # Verify it's gone
        with pytest.raises(LectureNotFoundError):
            lecture_service.get_lecture(lecture.id)

    def test_get_lecture_not_found(self, lecture_service):
        """Test getting a non-existent lecture raises appropriate error."""
        with pytest.raises(LectureNotFoundError):
            lecture_service.get_lecture(999999)

    @pytest.mark.asyncio
    async def test_generate_lecture_content(
        self, lecture_service, course_service, department_service, professor_service
    ):
        """Test generating lecture content with mocked AI response."""
        # Setup prerequisites
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        professor = professor_service.create_professor(
            Professor(
                name="Dr. Ada Lovelace",
                title="Professor",
                department_id=department.id,
                specialization="Programming Languages",
                gender="Female",
            )
        )

        course = course_service.create_course(
            title="Introduction to Programming",
            code="CS101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Mock the content service's generate_text method
        lecture_service.content_service.generate_text.return_value = MOCK_LECTURE_XML

        # Generate lecture content
        lecture_data = await lecture_service.generate_lecture_content(
            {
                "course_id": course.id,
                "week_number": 1,
                "order_in_week": 1,
                "freeform_prompt": "Focus on basic variable concepts",
                "word_count": 2000,
            }
        )

        # Verify the generated content
        assert lecture_data["title"] == "Understanding Variables in Python"
        assert lecture_data["week_number"] == 1
        assert lecture_data["order_in_week"] == 1
        assert "variables" in lecture_data["description"].lower()
        assert "Good morning" in lecture_data["content"]

        # Verify content service was called with correct arguments
        lecture_service.content_service.generate_text.assert_called_once()
        call_args = lecture_service.content_service.generate_text.call_args
        assert call_args.kwargs["model"] == get_settings().LECTURE_GENERATION_MODEL
        assert "system_prompt" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_generate_lecture_content_with_existing_lectures(
        self, lecture_service, course_service, department_service, professor_service
    ):
        """Test generating lecture content with existing lectures for context."""
        # Setup prerequisites
        department = department_service.create_department(
            name="Mathematics",
            code="MATH",
            faculty="Science",
        )

        professor = professor_service.create_professor(
            Professor(
                name="Dr. Euler",
                title="Professor",
                department_id=department.id,
                specialization="Calculus",
                gender="Male",
            )
        )

        course = course_service.create_course(
            title="Calculus I",
            code="MATH201",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create an existing lecture
        lecture_service.create_lecture(
            title="Introduction to Limits",
            course_id=course.id,
            week_number=1,
            order_in_week=1,
            description="Understanding the concept of limits",
        )

        # Mock the content service
        lecture_service.content_service.generate_text.return_value = MOCK_LECTURE_XML

        # Generate lecture content
        lecture_data = await lecture_service.generate_lecture_content(
            {
                "course_id": course.id,
                "week_number": 1,
                "order_in_week": 2,
            }
        )

        # Verify the generated content
        assert lecture_data["week_number"] == 1
        assert lecture_data["order_in_week"] == 2

        # Verify existing lectures were included in context
        call_args = lecture_service.content_service.generate_text.call_args
        prompt = call_args.kwargs.get("prompt", "")
        assert "Introduction to Limits" in prompt

    @pytest.mark.asyncio
    async def test_generate_lecture_content_error_handling(
        self, lecture_service, course_service, department_service, professor_service
    ):
        """Test error handling in lecture generation."""
        # Setup prerequisites
        department = department_service.create_department(
            name="Physics",
            code="PHYS",
            faculty="Science",
        )

        professor = professor_service.create_professor(
            Professor(
                name="Dr. Feynman",
                title="Professor",
                department_id=department.id,
                specialization="Quantum Physics",
                gender="Male",
            )
        )

        course = course_service.create_course(
            title="Quantum Mechanics",
            code="PHYS301",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Test invalid XML response
        lecture_service.content_service.generate_text.return_value = "<invalid>XML</invalid>"

        with pytest.raises(ContentGenerationError) as exc_info:
            await lecture_service.generate_lecture_content(
                {"course_id": course.id, "week_number": 1, "order_in_week": 1}
            )
        assert "Could not extract" in str(exc_info.value)

        # Test empty response
        lecture_service.content_service.generate_text.return_value = ""

        with pytest.raises(ContentGenerationError) as exc_info:
            await lecture_service.generate_lecture_content(
                {"course_id": course.id, "week_number": 1, "order_in_week": 1}
            )
        assert "Could not extract" in str(exc_info.value)

        # Test exception in content service
        lecture_service.content_service.generate_text.side_effect = Exception("API Error")

        with pytest.raises(ContentGenerationError) as exc_info:
            await lecture_service.generate_lecture_content(
                {"course_id": course.id, "week_number": 1, "order_in_week": 1}
            )
        assert "unexpected error" in str(exc_info.value).lower()
