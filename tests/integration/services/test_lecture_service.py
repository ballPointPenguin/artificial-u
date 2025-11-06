"""
Integration tests for LectureService.
"""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.models.core import Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services import (
    CourseService,
    DepartmentService,
    LectureService,
    ProfessorService,
    TopicService,
)
from artificial_u.utils.exceptions import LectureNotFoundError

# Example AI-generated XML response
MOCK_LECTURE_XML = """
<output>
  <lecture>
    <title>
    Introduction to Variables
    </title>
    <content>
    [Professor enters, smiling warmly]

    Good morning, everyone! Today we\'re going to explore one of the most fundamental
    concepts in programming: variables. Think of variables as labeled containers that
    can hold different types of data...

    [Writes \'x = 42\' on the board]

    Let\'s start with a simple example...
  </content>
</lecture>
</output>"""


@pytest.fixture
def repository_factory():
    """Create a repository factory that uses the test database."""
    # The DATABASE_URL will be picked up from .env.test
    return RepositoryFactory()


@pytest.fixture
def content_service():
    """Create a mock ContentService with async support."""
    mock = MagicMock()
    mock.generate_text = AsyncMock(return_value=MOCK_LECTURE_XML)
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
def professor_service(repository_factory, voice_service):
    """Create a ProfessorService with mocked dependent services."""
    from artificial_u.services.job_enqueue_service import JobEnqueueService

    job_enqueue_service = JobEnqueueService(
        repository_factory=repository_factory,
        logger=logging.getLogger(__name__),
    )

    return ProfessorService(
        repository_factory=repository_factory,
        voice_service=voice_service,
        job_enqueue_service=job_enqueue_service,
    )


@pytest.fixture
def department_service(repository_factory):
    """Create a DepartmentService with mocked dependent services."""
    professor_service_mock_for_dept = MagicMock()
    course_service_mock_for_dept = MagicMock()

    return DepartmentService(
        repository_factory=repository_factory,
        professor_service=professor_service_mock_for_dept,
        course_service=course_service_mock_for_dept,
        logger=logging.getLogger(__name__),
    )


@pytest.fixture
def department_selector_service():
    """Create a mock DepartmentSelectorService."""
    mock_service = MagicMock()
    mock_service.resolve_department = AsyncMock(return_value=1)  # Mock department ID
    return mock_service


@pytest.fixture
def professor_selector_service():
    """Create a mock ProfessorSelectorService."""
    mock_service = MagicMock()
    mock_service.resolve_professor = AsyncMock(return_value=1)  # Mock professor ID
    return mock_service


@pytest.fixture
def course_service(
    repository_factory, professor_service, department_selector_service, professor_selector_service
):
    """Create a CourseService with selector services."""
    return CourseService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        department_selector_service=department_selector_service,
        professor_selector_service=professor_selector_service,
        logger=logging.getLogger(__name__),
    )


@pytest.fixture
def topic_service(repository_factory):
    """Create a TopicService."""
    # This assumes TopicService primarily uses the repository for CRUD.
    return TopicService(
        repository_factory=repository_factory,
        logger=logging.getLogger(__name__),
    )


@pytest.fixture
def lecture_service(repository_factory):
    """Create a LectureService with repository factory only."""
    return LectureService(
        repository_factory=repository_factory,
        logger=logging.getLogger(__name__),
    )


@pytest.fixture
def sample_faculties(repository_factory):
    """Create sample faculties for testing."""
    from artificial_u.models.core import Faculty

    faculties = {}
    for name in ["Engineering", "Science", "Arts", "Business", "Testing"]:
        faculty = Faculty(name=name, description=f"The {name} faculty.")
        faculty = repository_factory.faculty.create(faculty)
        faculties[name] = faculty.id
    return faculties


@pytest.mark.integration
class TestLectureService:
    """Integration tests for LectureService."""

    async def _create_prerequisites(
        self,
        department_service,
        professor_service,
        course_service,
        topic_service,
        repository_factory,
        sample_faculties,
    ):
        department = department_service.create_department(
            name="Test Department for Lectures",
            code="TDL",
            faculty_id=sample_faculties["Testing"],
        )
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Test Lecturer",
                title="Lecturer",
                department_id=department.id,
                specialization="Testology",
            )
        )
        course_result = await course_service.create_course(
            title="Test Course for Lectures",
            code="TCL101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )
        course = course_result[0]
        topic = topic_service.create_topic(
            title="Test Topic 1",
            course_id=course.id,
            week=1,
            order=1,
        )
        return department, professor, course, topic

    @pytest.mark.asyncio
    async def test_create_and_get_lecture(
        self,
        lecture_service,
        course_service,
        department_service,
        professor_service,
        topic_service,
        repository_factory,
        sample_faculties,
    ):
        """Test creating and retrieving a lecture."""
        _, _, course, topic = await self._create_prerequisites(
            department_service,
            professor_service,
            course_service,
            topic_service,
            repository_factory,
            sample_faculties,
        )

        lecture_title = "Test Lecture Title"
        lecture_content = "This is the test lecture content."
        lecture_summary = "Summary of the test lecture."
        lecture = lecture_service.create_lecture(
            course_id=course.id,
            topic_id=topic.id,
            title=lecture_title,
            content=lecture_content,
            summary=lecture_summary,
            revision=1,
        )

        assert lecture.id is not None
        assert lecture.course_id == course.id
        assert lecture.topic_id == topic.id
        assert lecture.title == lecture_title
        assert lecture.content == lecture_content
        assert lecture.summary == lecture_summary
        assert lecture.revision == 1

        retrieved = lecture_service.get_lecture(lecture.id)
        assert retrieved.id == lecture.id
        assert retrieved.course_id == course.id
        assert retrieved.topic_id == topic.id
        assert retrieved.title == lecture_title
        assert retrieved.content == lecture_content
        assert retrieved.summary == lecture_summary
        assert retrieved.revision == 1

    @pytest.mark.asyncio
    async def test_list_lectures(
        self,
        lecture_service,
        course_service,
        department_service,
        professor_service,
        topic_service,
        repository_factory,
        sample_faculties,
    ):
        """Test listing lectures with various filters."""
        _, professor, course, topic1 = await self._create_prerequisites(
            department_service,
            professor_service,
            course_service,
            topic_service,
            repository_factory,
            sample_faculties,
        )
        topic2 = topic_service.create_topic(
            title="Test Topic 2", course_id=course.id, week=1, order=2
        )

        lecture_service.create_lecture(
            course_id=course.id,
            topic_id=topic1.id,
            title="Lecture 1",
            content="Content for lecture 1",
            summary="Summary 1",
        )
        lecture_service.create_lecture(
            course_id=course.id,
            topic_id=topic2.id,
            title="Lecture 2",
            content="Content for lecture 2",
            summary="Summary 2",
        )

        # List all lectures for the course
        course_lectures = lecture_service.list_lectures(course_id=course.id)
        assert len(course_lectures) >= 2
        topic_ids = {lecture.topic_id for lecture in course_lectures}
        assert topic1.id in topic_ids
        assert topic2.id in topic_ids

        # Test pagination (assuming default size is 10, so if we have 2, page 1 size 1 works)
        paged_lectures = lecture_service.list_lectures(course_id=course.id, page=1, size=1)
        assert len(paged_lectures) == 1

        # Test search (searches content and summary)
        search_results_content = lecture_service.list_lectures(search_query="Content for lecture 1")
        assert any(lec.summary == "Summary 1" for lec in search_results_content)

        search_results_summary = lecture_service.list_lectures(search_query="Summary 2")
        assert any(lec.content == "Content for lecture 2" for lec in search_results_summary)

    @pytest.mark.asyncio
    async def test_update_lecture(
        self,
        lecture_service,
        course_service,
        department_service,
        professor_service,
        topic_service,
        repository_factory,
        sample_faculties,
    ):
        """Test updating a lecture."""
        _, _, course, topic = await self._create_prerequisites(
            department_service,
            professor_service,
            course_service,
            topic_service,
            repository_factory,
            sample_faculties,
        )

        lecture = lecture_service.create_lecture(
            course_id=course.id,
            topic_id=topic.id,
            title="Initial title",
            content="Initial content",
            summary="Initial summary",
            revision=1,
        )

        updated_content = "Updated lecture content."
        updated_summary = "Updated lecture summary."
        updated_title = "Updated lecture title."
        updated_revision = 2

        updated = lecture_service.update_lecture(
            lecture.id,
            {
                "content": updated_content,
                "summary": updated_summary,
                "title": updated_title,
                "revision": updated_revision,
                # course_id and topic_id typically not updated this way, but can be included
                "course_id": course.id,
                "topic_id": topic.id,
            },
        )

        assert updated.content == updated_content
        assert updated.summary == updated_summary
        assert updated.revision == updated_revision
        assert updated.title == updated_title
        assert updated.course_id == course.id  # Ensure these remain or are correctly updated
        assert updated.topic_id == topic.id

        retrieved = lecture_service.get_lecture(lecture.id)
        assert retrieved.content == updated_content
        assert retrieved.summary == updated_summary
        assert retrieved.revision == updated_revision
        assert retrieved.title == updated_title

    @pytest.mark.asyncio
    async def test_delete_lecture(
        self,
        lecture_service,
        course_service,
        department_service,
        professor_service,
        topic_service,
        repository_factory,
        sample_faculties,
    ):
        """Test deleting a lecture."""
        _, _, course, topic = await self._create_prerequisites(
            department_service,
            professor_service,
            course_service,
            topic_service,
            repository_factory,
            sample_faculties,
        )

        lecture_to_delete = lecture_service.create_lecture(
            course_id=course.id,
            topic_id=topic.id,
            content="Content to delete",
            title="Title to delete",
        )

        retrieved = lecture_service.get_lecture(lecture_to_delete.id)
        assert retrieved.id == lecture_to_delete.id

        result = lecture_service.delete_lecture(lecture_to_delete.id)
        assert result is True

        with pytest.raises(LectureNotFoundError):
            lecture_service.get_lecture(lecture_to_delete.id)

    def test_get_lecture_not_found(self, lecture_service):
        """Test getting a non-existent lecture raises appropriate error."""
        with pytest.raises(LectureNotFoundError):
            lecture_service.get_lecture(999999)  # Non-existent ID
