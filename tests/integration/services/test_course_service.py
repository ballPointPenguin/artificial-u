"""
Integration tests for CourseService.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.config import get_settings
from artificial_u.models.core import Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services import CourseService, DepartmentService, ProfessorService
from artificial_u.utils.exceptions import ContentGenerationError, CourseNotFoundError

# Example AI-generated XML response for course
MOCK_COURSE_XML = """
<output>
  <course>
    <title>Advanced Machine Learning</title>
    <code>CS501</code>
    <description>Deep dive into modern machine learning algorithms and applications.</description>
    <level>Graduate</level>
    <credits>4</credits>
    <lectures_per_week>2</lectures_per_week>
    <total_weeks>14</total_weeks>
  </course>
</output>
"""


@pytest.fixture
def repository_factory():
    """Create a repository factory that uses the test database."""
    # The DATABASE_URL will be picked up from .env.test
    return RepositoryFactory()


@pytest.fixture
def content_service():
    """Create a mock ContentService with async support."""
    mock = MagicMock()
    mock.generate_text = AsyncMock(return_value=MOCK_COURSE_XML)
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
def course_service(repository_factory, professor_service, content_service):
    """Create a CourseService with actual ProfessorService and mocked ContentService."""
    return CourseService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        content_service=content_service,
    )


@pytest.mark.integration
class TestCourseService:
    """Integration tests for CourseService."""

    def test_create_and_get_course(self, course_service, department_service, professor_service):
        """Test creating and retrieving a course."""
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

        # Create a new course
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
        )[
            0
        ]  # The create_course method returns a tuple (course, professor)

        # Verify it was created with an ID
        assert course.id is not None
        assert course.title == "Introduction to Programming"
        assert course.code == "CS101"
        assert course.department_id == department.id
        assert course.professor_id == professor.id

        # Retrieve the course and verify
        retrieved = course_service.get_course(course.id)
        assert retrieved.id == course.id
        assert retrieved.title == "Introduction to Programming"
        assert retrieved.code == "CS101"

    def test_get_course_by_code(self, course_service, department_service, professor_service):
        """Test retrieving a course by its code."""
        # First create a department
        department = department_service.create_department(
            name="Physics",
            code="PHYS",
            faculty="Science",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Albert Einstein",
                title="Professor",
                department_id=department.id,
                specialization="Theoretical Physics",
                gender="Male",
            )
        )

        # Create a new course with a unique code
        course_code = "PHYS101"
        course = course_service.create_course(
            title="Introduction to Physics",
            code=course_code,
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Verify retrieval by code
        retrieved = course_service.get_course_by_code(course_code)
        assert retrieved.id == course.id
        assert retrieved.title == "Introduction to Physics"
        assert retrieved.code == course_code

    def test_update_course(self, course_service, department_service, professor_service):
        """Test updating a course."""
        # First create a department
        department = department_service.create_department(
            name="Mathematics",
            code="MATH",
            faculty="Science",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Ada Lovelace",
                title="Associate Professor",
                department_id=department.id,
                specialization="Algorithm Theory",
                gender="Female",
            )
        )

        # Create a new course
        course = course_service.create_course(
            title="Calculus I",
            code="MATH201",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
            description="Introduction to differential calculus",
            credits=4,
        )[0]

        # Update the course
        updated = course_service.update_course(
            course.id,
            {
                "title": "Advanced Calculus I",
                "description": "In-depth study of differential calculus",
                "credits": 5,
            },
        )

        # Verify updates
        assert updated.title == "Advanced Calculus I"
        assert updated.description == "In-depth study of differential calculus"
        assert updated.credits == 5
        # Unchanged fields
        assert updated.code == "MATH201"
        assert updated.department_id == department.id
        assert updated.professor_id == professor.id

        # Retrieve to confirm persistence
        retrieved = course_service.get_course(course.id)
        assert retrieved.title == "Advanced Calculus I"
        assert retrieved.description == "In-depth study of differential calculus"
        assert retrieved.credits == 5

    def test_list_courses(self, course_service, department_service, professor_service):
        """Test listing courses with/without department filter."""
        # Create departments
        cs_dept = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        math_dept = department_service.create_department(
            name="Mathematics",
            code="MATH",
            faculty="Science",
        )

        # Create professors
        cs_prof = professor_service.create_professor(
            Professor(
                name="Dr. Grace Hopper",
                title="Professor",
                department_id=cs_dept.id,
                specialization="Programming Languages",
                gender="Female",
            )
        )

        math_prof = professor_service.create_professor(
            Professor(
                name="Dr. John Nash",
                title="Professor",
                department_id=math_dept.id,
                specialization="Game Theory",
                gender="Male",
            )
        )

        # Create courses in different departments
        course_service.create_course(
            title="Algorithms",
            code="CS301",
            department_id=cs_dept.id,
            level="Undergraduate",
            professor_id=cs_prof.id,
        )

        course_service.create_course(
            title="Data Structures",
            code="CS302",
            department_id=cs_dept.id,
            level="Undergraduate",
            professor_id=cs_prof.id,
        )

        course_service.create_course(
            title="Game Theory",
            code="MATH401",
            department_id=math_dept.id,
            level="Graduate",
            professor_id=math_prof.id,
        )

        # List all courses
        all_courses = course_service.list_courses()
        assert len(all_courses) >= 3  # At least our 3 (could be more if DB has existing data)

        # List by department_id
        cs_courses = course_service.list_courses(department_id=cs_dept.id)
        assert len(cs_courses) >= 2
        course_codes = [c["course"]["code"] for c in cs_courses]
        assert "CS301" in course_codes
        assert "CS302" in course_codes

        math_courses = course_service.list_courses(department_id=math_dept.id)
        assert len(math_courses) >= 1
        assert any(c["course"]["code"] == "MATH401" for c in math_courses)

    def test_get_course_not_found(self, course_service):
        """Test getting a non-existent course raises appropriate error."""
        with pytest.raises(CourseNotFoundError):
            course_service.get_course(999999)

    def test_delete_course(self, course_service, department_service, professor_service):
        """Test deleting a course."""
        # First create a department
        department = department_service.create_department(
            name="Temporary Department",
            code="TEMP",
            faculty="Test",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Temp Professor",
                title="Adjunct Professor",
                department_id=department.id,
                specialization="Testing",
            )
        )

        # Create a course to delete
        course = course_service.create_course(
            title="Course to Delete",
            code="DELETE101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Verify it exists
        retrieved = course_service.get_course(course.id)
        assert retrieved.id == course.id

        # Delete it
        result = course_service.delete_course(course.id)
        assert result is True

        # Verify it's gone
        with pytest.raises(CourseNotFoundError):
            course_service.get_course(course.id)

    @pytest.mark.asyncio
    async def test_generate_course_content(
        self, course_service, department_service, professor_service
    ):
        """Test generating course content with mocked AI response."""
        # Setup prerequisites
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        professor = professor_service.create_professor(
            Professor(
                name="Dr. Geoffrey Hinton",
                title="Professor",
                department_id=department.id,
                specialization="Machine Learning",
                gender="Male",
            )
        )

        # Mock the content service's generate_text method
        course_service.content_service.generate_text.return_value = MOCK_COURSE_XML

        # Generate course content
        course_data = await course_service.generate_course(
            {
                "department_id": department.id,
                "professor_id": professor.id,
                "freeform_prompt": "Focus on advanced ML concepts",
            }
        )

        # Verify the generated content
        assert course_data["title"] == "Advanced Machine Learning"
        assert course_data["code"] == "CS501"
        assert course_data["level"] == "Graduate"
        assert course_data["credits"] == 4
        assert course_data["lectures_per_week"] == 2
        assert course_data["total_weeks"] == 14
        assert "machine learning" in course_data["description"].lower()

        # Verify content service was called with correct arguments
        course_service.content_service.generate_text.assert_called_once()
        call_args = course_service.content_service.generate_text.call_args
        assert call_args.kwargs["model"] == get_settings().COURSE_GENERATION_MODEL
        assert "system_prompt" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_generate_course_content_error_handling(
        self, course_service, department_service, professor_service
    ):
        """Test error handling in course generation."""
        # Setup prerequisites
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        professor = professor_service.create_professor(
            Professor(
                name="Dr. Test Professor",
                title="Professor",
                department_id=department.id,
                specialization="Testing",
                gender="Other",
            )
        )

        # Test invalid XML response
        course_service.content_service.generate_text = AsyncMock(
            return_value="<invalid>XML</invalid>"
        )

        with pytest.raises(ContentGenerationError) as exc_info:
            await course_service.generate_course(
                {
                    "department_id": department.id,
                    "professor_id": professor.id,
                }
            )
        assert "Could not extract <output> or <course> tag" in str(exc_info.value)

        # Test empty response
        course_service.content_service.generate_text = AsyncMock(return_value="")

        with pytest.raises(ContentGenerationError) as exc_info:
            await course_service.generate_course(
                {
                    "department_id": department.id,
                    "professor_id": professor.id,
                }
            )
        assert "Could not extract <output> or <course> tag" in str(exc_info.value)

        # Test exception in content service
        course_service.content_service.generate_text = AsyncMock(side_effect=Exception("API Error"))

        with pytest.raises(ContentGenerationError) as exc_info:
            await course_service.generate_course(
                {
                    "department_id": department.id,
                    "professor_id": professor.id,
                }
            )
        assert "An unexpected error occurred" in str(exc_info.value)
