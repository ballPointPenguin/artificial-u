"""
Integration tests for CourseSelectorService.
"""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.models.core import Course, Faculty, Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.course_selector_service import CourseSelectorService
from artificial_u.utils.exceptions import ContentGenerationError

# Mock AI response for SELECT decision
MOCK_SELECT_RESPONSE = """
<decision>
  <action>SELECT</action>
  <course_ids>{course_ids}</course_ids>
  <reasoning>These courses match the student's learning goal about machine learning.</reasoning>
</decision>
"""

# Mock AI response for GENERATE decision
MOCK_GENERATE_RESPONSE = """
<decision>
  <action>GENERATE</action>
  <course_ids></course_ids>
  <reasoning>No existing courses cover this specialized topic. A new course should be generated.</reasoning>
</decision>
"""


@pytest.fixture
def repository_factory():
    """Create a repository factory that uses the test database."""
    return RepositoryFactory()


@pytest.fixture
def content_service():
    """Create a mock ContentService with async support."""
    mock = MagicMock()
    mock.generate_text = AsyncMock(return_value=MOCK_GENERATE_RESPONSE)
    return mock


@pytest.fixture
def course_selector_service(content_service, repository_factory):
    """Create a CourseSelectorService with mocked content service."""
    return CourseSelectorService(
        content_service=content_service,
        repository_factory=repository_factory,
        logger=logging.getLogger(__name__),
    )


@pytest.fixture
def sample_faculty(repository_factory):
    """Create a sample faculty for testing."""
    faculty = Faculty(
        name="Test Faculty",
        description="A test faculty for selector tests.",
        language="en",
    )
    return repository_factory.faculty.create(faculty)


@pytest.fixture
def sample_department(repository_factory, sample_faculty):
    """Create a sample department for testing."""
    from artificial_u.models.core import Department

    department = Department(
        name="Test Department",
        code="TEST",
        faculty_id=sample_faculty.id,
        description="Test department for selector tests",
    )
    return repository_factory.department.create(department)


@pytest.fixture
def sample_professor(repository_factory, sample_department):
    """Create a sample professor for testing."""
    professor = Professor(
        name="Dr. Test Professor",
        title="Professor",
        department_id=sample_department.id,
        specialization="Testing",
        gender="Female",
    )
    return repository_factory.professor.create(professor)


@pytest.fixture
def published_course(repository_factory, sample_department, sample_professor):
    """Create a published course for testing."""
    course = Course(
        title="Introduction to Machine Learning",
        code="ML101",
        department_id=sample_department.id,
        professor_id=sample_professor.id,
        level="Undergraduate",
        description="Learn the fundamentals of machine learning algorithms.",
        status="published",
    )
    return repository_factory.course.create(course)


@pytest.fixture
def hidden_course(repository_factory, sample_department, sample_professor):
    """Create a hidden course for testing."""
    course = Course(
        title="Advanced Neural Networks",
        code="ML501",
        department_id=sample_department.id,
        professor_id=sample_professor.id,
        level="Graduate",
        description="Deep dive into neural network architectures.",
        status="hidden",
    )
    return repository_factory.course.create(course)


@pytest.mark.integration
class TestCourseSelectorService:
    """Integration tests for CourseSelectorService."""

    @pytest.mark.asyncio
    async def test_match_courses_no_published_courses(self, course_selector_service, hidden_course):
        """Test matching when no published courses exist (only hidden)."""
        result = await course_selector_service.match_courses(
            "I want to learn about machine learning"
        )

        assert result["action"] == "GENERATE"
        assert result["courses"] == []
        assert result["course_ids"] == []
        assert "No published courses" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_match_courses_returns_generate(
        self, course_selector_service, content_service, published_course
    ):
        """Test matching returns GENERATE when AI decides no match."""
        content_service.generate_text = AsyncMock(return_value=MOCK_GENERATE_RESPONSE)

        result = await course_selector_service.match_courses(
            "I want to learn about quantum physics"
        )

        assert result["action"] == "GENERATE"
        assert result["courses"] == []
        assert result["course_ids"] == []
        assert "specialized topic" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_match_courses_returns_select(
        self, course_selector_service, content_service, published_course
    ):
        """Test matching returns SELECT with matched course."""
        # Configure mock to return SELECT with the published course ID
        select_response = MOCK_SELECT_RESPONSE.format(course_ids=str(published_course.id))
        content_service.generate_text = AsyncMock(return_value=select_response)

        result = await course_selector_service.match_courses(
            "I want to learn about machine learning"
        )

        assert result["action"] == "SELECT"
        assert len(result["courses"]) == 1
        assert result["courses"][0].id == published_course.id
        assert result["course_ids"] == [published_course.id]
        assert "machine learning" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_match_courses_select_invalid_ids_falls_back_to_generate(
        self, course_selector_service, content_service, published_course
    ):
        """Test that SELECT with invalid course IDs falls back to GENERATE."""
        # Configure mock to return SELECT with non-existent course ID
        select_response = MOCK_SELECT_RESPONSE.format(course_ids="999999")
        content_service.generate_text = AsyncMock(return_value=select_response)

        result = await course_selector_service.match_courses("I want to learn something")

        # Should fall back to GENERATE since course ID doesn't exist
        assert result["action"] == "GENERATE"
        assert result["courses"] == []
        assert "not found" in result["reasoning"]

    @pytest.mark.asyncio
    async def test_match_courses_filters_hidden_courses(
        self, course_selector_service, repository_factory, sample_department, sample_professor
    ):
        """Test that only published courses are considered for matching."""
        # Create one published and one hidden course
        published = repository_factory.course.create(
            Course(
                title="Published Course",
                code="PUB101",
                department_id=sample_department.id,
                professor_id=sample_professor.id,
                level="Undergraduate",
                status="published",
            )
        )
        repository_factory.course.create(
            Course(
                title="Hidden Course",
                code="HID101",
                department_id=sample_department.id,
                professor_id=sample_professor.id,
                level="Undergraduate",
                status="hidden",
            )
        )

        # Get published courses for matching
        published_courses = course_selector_service._get_published_courses_for_matching()

        # Should only include published courses
        course_ids = [c["id"] for c in published_courses]
        assert published.id in course_ids

        # Hidden courses should be filtered out
        course_titles = [c["title"] for c in published_courses]
        assert "Hidden Course" not in course_titles

    @pytest.mark.asyncio
    async def test_match_courses_includes_professor_name(
        self, course_selector_service, published_course, sample_professor
    ):
        """Test that professor names are included in course data."""
        published_courses = course_selector_service._get_published_courses_for_matching()

        # Find our test course
        test_course = next((c for c in published_courses if c["id"] == published_course.id), None)

        assert test_course is not None
        assert test_course["professor_name"] == sample_professor.name

    @pytest.mark.asyncio
    async def test_match_courses_ai_error_raises_exception(
        self, course_selector_service, content_service, published_course
    ):
        """Test that AI errors are properly propagated."""
        content_service.generate_text = AsyncMock(
            side_effect=ContentGenerationError("AI service unavailable")
        )

        with pytest.raises(ContentGenerationError, match="AI service unavailable"):
            await course_selector_service.match_courses("I want to learn something")

    @pytest.mark.asyncio
    async def test_match_courses_empty_ai_response_raises_error(
        self, course_selector_service, content_service, published_course
    ):
        """Test that empty AI response raises error."""
        content_service.generate_text = AsyncMock(return_value="")

        with pytest.raises(ContentGenerationError, match="empty response"):
            await course_selector_service.match_courses("I want to learn something")

    @pytest.mark.asyncio
    async def test_match_courses_multiple_selected_courses(
        self,
        course_selector_service,
        content_service,
        repository_factory,
        sample_department,
        sample_professor,
    ):
        """Test matching with multiple selected courses."""
        # Create multiple published courses
        course1 = repository_factory.course.create(
            Course(
                title="ML Basics",
                code="ML100",
                department_id=sample_department.id,
                professor_id=sample_professor.id,
                level="Undergraduate",
                status="published",
            )
        )
        course2 = repository_factory.course.create(
            Course(
                title="Deep Learning",
                code="ML200",
                department_id=sample_department.id,
                professor_id=sample_professor.id,
                level="Graduate",
                status="published",
            )
        )

        # Configure mock to return SELECT with multiple course IDs
        select_response = MOCK_SELECT_RESPONSE.format(course_ids=f"{course1.id}, {course2.id}")
        content_service.generate_text = AsyncMock(return_value=select_response)

        result = await course_selector_service.match_courses(
            "I want to learn machine learning comprehensively"
        )

        assert result["action"] == "SELECT"
        assert len(result["courses"]) == 2
        assert set(result["course_ids"]) == {course1.id, course2.id}
