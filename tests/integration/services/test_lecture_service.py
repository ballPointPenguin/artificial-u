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
    TopicService,
)
from artificial_u.utils.exceptions import ContentGenerationError, LectureNotFoundError

# Example AI-generated XML response
MOCK_LECTURE_XML = """
<output>
  <lecture>
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
    professor_service_mock_for_dept = MagicMock()
    course_service_mock_for_dept = MagicMock()

    return DepartmentService(
        repository_factory=repository_factory,
        professor_service=professor_service_mock_for_dept,
        course_service=course_service_mock_for_dept,
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


@pytest.fixture
def topic_service(repository_factory):
    """Create a TopicService."""
    # This assumes TopicService primarily uses the repository for CRUD.
    return TopicService(
        repository_factory=repository_factory,
        content_service=content_service,
        course_service=course_service,
    )


@pytest.fixture
def lecture_service(
    repository_factory,
    course_service,
    professor_service,
    topic_service,
    content_service,
):
    """Create a LectureService with actual services and mocked ContentService."""
    return LectureService(
        repository_factory=repository_factory,
        content_service=content_service,
        course_service=course_service,
        professor_service=professor_service,
        topic_service=topic_service,
    )


@pytest.mark.integration
class TestLectureService:
    """Integration tests for LectureService."""

    def _create_prerequisites(
        self, department_service, professor_service, course_service, topic_service
    ):
        department = department_service.create_department(
            name="Test Department for Lectures",
            code="TDL",
            faculty="Testing",
        )
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Test Lecturer",
                title="Lecturer",
                department_id=department.id,
                specialization="Testology",
            )
        )
        course, _ = course_service.create_course(
            title="Test Course for Lectures",
            code="TCL101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )
        topic = topic_service.create_topic(
            title="Test Topic 1",
            course_id=course.id,
            week=1,
            order=1,
        )
        return department, professor, course, topic

    def test_create_and_get_lecture(
        self, lecture_service, course_service, department_service, professor_service, topic_service
    ):
        """Test creating and retrieving a lecture."""
        _, _, course, topic = self._create_prerequisites(
            department_service, professor_service, course_service, topic_service
        )

        lecture_content = "This is the test lecture content."
        lecture_summary = "Summary of the test lecture."
        lecture = lecture_service.create_lecture(
            course_id=course.id,
            topic_id=topic.id,
            content=lecture_content,
            summary=lecture_summary,
            revision=1,
        )

        assert lecture.id is not None
        assert lecture.course_id == course.id
        assert lecture.topic_id == topic.id
        assert lecture.content == lecture_content
        assert lecture.summary == lecture_summary
        assert lecture.revision == 1

        retrieved = lecture_service.get_lecture(lecture.id)
        assert retrieved.id == lecture.id
        assert retrieved.course_id == course.id
        assert retrieved.topic_id == topic.id
        assert retrieved.content == lecture_content
        assert retrieved.summary == lecture_summary
        assert retrieved.revision == 1

    def test_list_lectures(
        self, lecture_service, course_service, department_service, professor_service, topic_service
    ):
        """Test listing lectures with various filters."""
        _, professor, course, topic1 = self._create_prerequisites(
            department_service, professor_service, course_service, topic_service
        )
        topic2 = topic_service.create_topic(
            title="Test Topic 2", course_id=course.id, week=1, order=2
        )

        lecture_service.create_lecture(
            course_id=course.id,
            topic_id=topic1.id,
            content="Content for lecture 1",
            summary="Summary 1",
        )
        lecture_service.create_lecture(
            course_id=course.id,
            topic_id=topic2.id,
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

    def test_update_lecture(
        self, lecture_service, course_service, department_service, professor_service, topic_service
    ):
        """Test updating a lecture."""
        _, _, course, topic = self._create_prerequisites(
            department_service, professor_service, course_service, topic_service
        )

        lecture = lecture_service.create_lecture(
            course_id=course.id,
            topic_id=topic.id,
            content="Initial content",
            summary="Initial summary",
            revision=1,
        )

        updated_content = "Updated lecture content."
        updated_summary = "Updated lecture summary."
        updated_revision = 2

        updated = lecture_service.update_lecture(
            lecture.id,
            {
                "content": updated_content,
                "summary": updated_summary,
                "revision": updated_revision,
                # course_id and topic_id typically not updated this way, but can be included
                "course_id": course.id,
                "topic_id": topic.id,
            },
        )

        assert updated.content == updated_content
        assert updated.summary == updated_summary
        assert updated.revision == updated_revision
        assert updated.course_id == course.id  # Ensure these remain or are correctly updated
        assert updated.topic_id == topic.id

        retrieved = lecture_service.get_lecture(lecture.id)
        assert retrieved.content == updated_content
        assert retrieved.summary == updated_summary
        assert retrieved.revision == updated_revision

    def test_delete_lecture(
        self, lecture_service, course_service, department_service, professor_service, topic_service
    ):
        """Test deleting a lecture."""
        _, _, course, topic = self._create_prerequisites(
            department_service, professor_service, course_service, topic_service
        )

        lecture_to_delete = lecture_service.create_lecture(
            course_id=course.id, topic_id=topic.id, content="Content to delete"
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

    @pytest.mark.asyncio
    async def test_generate_lecture_content(
        self,
        lecture_service,
        course_service,
        department_service,
        professor_service,
        topic_service,
        content_service,
    ):
        """Test generating lecture content with mocked AI response."""
        _, professor, course, topic = self._create_prerequisites(
            department_service, professor_service, course_service, topic_service
        )

        # Mock dependent service calls within lecture_service._process_models_for_generation
        # CourseService.get_course is already part of the fixture, so it's real.
        # ProfessorService.get_professor is also real.
        # TopicService methods need to be mocked if not using a real TopicService with a repo
        # For this test, we'll assume topic_service fixture provides a real service.
        # We need to ensure the created topic is fetchable.

        # For the specific topic being generated
        topic_service.get_topic = AsyncMock(
            return_value=topic
        )  # Mock if TopicService is not fully "real"
        # For the list of all topics in the course
        topic_service.list_topics = AsyncMock(
            return_value=[topic]
        )  # Mock if TopicService is not fully "real"

        # Ensure content_service.generate_text is using the class-level mock
        content_service.generate_text.return_value = MOCK_LECTURE_XML

        partial_attrs = {
            "course_id": course.id,
            "topic_id": topic.id,
            "freeform_prompt": "Focus on basic variable concepts",
            "word_count": 2000,  # lecture_service uses 2500 default if not provided
            "summary": "A generated summary (if we want to test passing it through)",
            "revision": 1,
        }
        lecture_data = await lecture_service.generate_lecture(partial_attrs)

        assert "Good morning, everyone!" in lecture_data["content"]
        assert lecture_data["course_id"] == course.id
        assert lecture_data["topic_id"] == topic.id
        assert (
            lecture_data.get("summary") == partial_attrs["summary"]
        )  # Check if summary from partial_attrs is passed
        assert lecture_data.get("revision") == partial_attrs["revision"]

        content_service.generate_text.assert_called_once()
        call_args = content_service.generate_text.call_args
        assert call_args.kwargs["model"] == get_settings().LECTURE_GENERATION_MODEL

        prompt_str = call_args.kwargs["prompt"]
        assert f"<title>{topic.title}</title>" in prompt_str
        assert f"<name>{professor.name}</name>" in prompt_str
        assert f"<code>{course.code}</code>" in prompt_str
        assert "Focus on basic variable concepts" in prompt_str  # freeform_prompt

    @pytest.mark.asyncio
    async def test_generate_lecture_content_with_existing_lectures(
        self,
        lecture_service,
        course_service,
        department_service,
        professor_service,
        topic_service,
        content_service,
    ):
        """Test generating lecture content with existing lectures for context."""
        _, _, course, topic1 = self._create_prerequisites(
            department_service, professor_service, course_service, topic_service
        )
        topic2 = topic_service.create_topic(
            title="Test Topic 2 for Gen", course_id=course.id, week=1, order=2
        )

        # Create an existing lecture
        existing_lecture = lecture_service.create_lecture(
            course_id=course.id,
            topic_id=topic1.id,
            content="Existing lecture content.",
            summary="Summary of existing lecture.",
            revision=1,
        )

        # Mock TopicService calls for the generation process
        # For the topic of the lecture being generated (topic2)
        lecture_service.topic_service.get_topic = AsyncMock(
            side_effect=lambda tid: topic2 if tid == topic2.id else topic1
        )
        # For listing all topics in the course
        lecture_service.topic_service.list_topics = AsyncMock(return_value=[topic1, topic2])
        # Lecture repository's list_by_course will be called to fetch existing_lecture

        content_service.generate_text.return_value = MOCK_LECTURE_XML

        lecture_data = await lecture_service.generate_lecture(
            {
                "course_id": course.id,
                "topic_id": topic2.id,  # Generating for topic2
                "revision": 1,
            }
        )

        assert lecture_data["course_id"] == course.id
        assert lecture_data["topic_id"] == topic2.id
        assert "Good morning, everyone!" in lecture_data["content"]

        call_args = content_service.generate_text.call_args
        prompt_str = call_args.kwargs.get("prompt", "")
        assert f"<topic>{topic1.title}</topic>" in prompt_str  # Check existing lecture topic title
        assert (
            f"<summary>{existing_lecture.summary}</summary>" in prompt_str
        )  # Check existing lecture summary
        assert (
            f"<title>{topic2.title}</title>" in prompt_str
        )  # Check current topic title for generation

    @pytest.mark.asyncio
    async def test_generate_lecture_content_error_handling(
        self,
        lecture_service,
        course_service,
        department_service,
        professor_service,
        topic_service,
        content_service,
    ):
        """Test error handling in lecture generation."""
        _, _, course, topic = self._create_prerequisites(
            department_service, professor_service, course_service, topic_service
        )

        # Mock TopicService methods for this test too
        lecture_service.topic_service.get_topic = AsyncMock(return_value=topic)
        lecture_service.topic_service.list_topics = AsyncMock(return_value=[topic])

        # Test missing topic_id (should raise ValueError in _process_models,
        # caught as ContentGenerationError)
        with pytest.raises(ContentGenerationError) as exc_info:
            await lecture_service.generate_lecture({"course_id": course.id})  # Missing topic_id
        assert (
            "topic_id is required" in str(exc_info.value).lower()
        )  # lecture_service raises ValueError first

        # Test invalid XML response
        content_service.generate_text.return_value = "<output><invalid>XML</invalid></output>"
        with pytest.raises(ContentGenerationError) as exc_info:
            await lecture_service.generate_lecture({"course_id": course.id, "topic_id": topic.id})
        # This error comes from extract_xml_content trying to get <lecture>
        # from <invalid>XML</invalid>
        assert "Failed to extract valid <content> from generated XML" in str(exc_info.value)

        # Test empty response (after output tag extraction)
        # This case means <output> was found, but it was empty, so <lecture> would not be found.
        content_service.generate_text.return_value = "<output></output>"
        with pytest.raises(ContentGenerationError) as exc_info:
            await lecture_service.generate_lecture({"course_id": course.id, "topic_id": topic.id})
        assert "Could not extract <output> or <lecture> tag" in str(exc_info.value)

        # Test exception in content service
        content_service.generate_text.side_effect = Exception("API Error")
        with pytest.raises(ContentGenerationError) as exc_info:
            await lecture_service.generate_lecture({"course_id": course.id, "topic_id": topic.id})
        assert "an unexpected error occurred" in str(exc_info.value).lower()
        assert "API Error" in str(exc_info.value)
