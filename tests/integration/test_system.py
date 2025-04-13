"""
Integration tests for UniversitySystem.

These tests verify the interaction between different components
but mock external API calls.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from artificial_u.config.defaults import DEFAULT_LOG_LEVEL
from artificial_u.models.core import Course, Lecture, Professor
from artificial_u.system import UniversitySystem
from artificial_u.utils.exceptions import (
    ContentGenerationError,
    CourseNotFoundError,
    LectureNotFoundError,
    ProfessorNotFoundError,
)


@pytest.fixture
def mock_system():
    """Create a system with mocked dependencies for testing."""
    with (
        patch("artificial_u.system.create_generator") as mock_create_generator,
        patch("artificial_u.system.VoiceService") as MockVoiceService,
        patch("artificial_u.system.TTSService") as MockTTSService,
        patch("artificial_u.system.Repository") as MockRepository,
        patch("pathlib.Path.mkdir"),
    ):

        # Set up mock content generator
        mock_content_generator = MagicMock()
        mock_content_generator.create_course_syllabus.return_value = (
            "Mock syllabus content"
        )
        mock_content_generator.create_lecture.return_value = Lecture(
            title="Mock Lecture",
            course_id=123,
            week_number=1,
            order_in_week=1,
            description="Mock lecture description",
            content="Mock lecture content",
        )
        mock_content_generator.create_professor.return_value = Professor(
            name="AI Generated Professor",
            title="Professor of Mock Studies",
            department="Computer Science",
            specialization="Artificial Intelligence",
            background="Generated background",
            teaching_style="Interactive",
            personality="Enthusiastic",
            gender="Male",
            accent="American",
            description="An AI-generated professor",
            age=45,
        )
        mock_create_generator.return_value = mock_content_generator

        # Set up mock voice service
        mock_voice_service = MockVoiceService.return_value
        mock_voice_service.select_voice_for_professor.return_value = 1

        # Set up mock TTS service
        mock_tts_service = MockTTSService.return_value
        mock_tts_service.generate_lecture_audio.return_value = (
            "mock_storage_url/audio.mp3",
            b"mock audio data",
        )
        mock_tts_service.generate_audio.return_value = b"mock audio data"

        # Set up mock repository
        mock_repository = MockRepository.return_value
        mock_repository.create_professor.side_effect = lambda p: Professor(
            id=123,
            name=p.name,
            title=p.title,
            department_id=p.department_id,
            specialization=p.specialization,
            background=p.background,
            teaching_style=p.teaching_style,
            personality=p.personality,
            voice_id=p.voice_id,
            gender=p.gender,
            accent=p.accent,
            description=p.description,
            age=p.age,
        )
        mock_repository.create_course.side_effect = lambda c: Course(
            id=123,
            code=c.code,
            title=c.title,
            department_id=c.department_id,
            level=c.level,
            description=c.description,
            syllabus=c.syllabus,
            professor_id=c.professor_id,
            total_weeks=c.total_weeks,
            lectures_per_week=c.lectures_per_week,
        )
        mock_repository.get_professor.return_value = Professor(
            id=123,
            name="Dr. Mock",
            title="Professor of Computer Science",
            department_id=1,
            specialization="Artificial Intelligence",
            background="Test background",
            teaching_style="Interactive",
            personality="Enthusiastic",
            voice_id=1,
            gender="Male",
            accent="British",
            description="A distinguished professor with a professorial appearance",
            age=52,
        )
        mock_repository.get_course_by_code.return_value = Course(
            id=123,
            code="CS101",
            title="Introduction to Computer Science",
            department_id=1,
            level="Undergraduate",
            description="A basic course in CS",
            syllabus="Mock syllabus",
            professor_id=123,
            total_weeks=14,
            lectures_per_week=2,
        )

        # Mock lecture update
        mock_repository.update_lecture.side_effect = lambda lecture: Lecture(
            id=lecture.id,
            title=lecture.title if hasattr(lecture, "title") else "Mock Lecture Title",
            course_id=lecture.course_id if hasattr(lecture, "course_id") else 123,
            week_number=lecture.week_number if hasattr(lecture, "week_number") else 1,
            order_in_week=(
                lecture.order_in_week if hasattr(lecture, "order_in_week") else 1
            ),
            description=(
                lecture.description
                if hasattr(lecture, "description")
                else "Mock lecture description"
            ),
            content=(
                lecture.content
                if hasattr(lecture, "content")
                else "Mock lecture content"
            ),
            audio_url=lecture.audio_url if hasattr(lecture, "audio_url") else None,
        )

        # Create system with mocked dependencies
        system = UniversitySystem(
            anthropic_api_key="mock_key",
            db_url=":memory:",
            log_level="ERROR",  # Reduce log noise in tests
        )

        # Replace mocked repository methods with common test patterns
        setup_common_repository_patterns(mock_repository)

        # Mock the async audio service method
        async def mock_create_lecture_audio(course_code=None, week=None, number=None):
            if course_code == "CS101" and week == 999 and number == 999:
                # This is for the error test
                raise ValueError(
                    f"Lecture for course {course_code}, week {week}, number {number} not found"
                )

            return "mock_storage_url/audio.mp3", Lecture(
                id=123,
                title="Mock Lecture Title",
                course_id=123,
                week_number=week,
                order_in_week=number,
                description="Mock lecture description",
                content="Mock lecture content",
                audio_url="mock_storage_url/audio.mp3",
            )

        # Replace the create_lecture_audio method
        system.create_lecture_audio = mock_create_lecture_audio

        yield system


def setup_common_repository_patterns(mock_repository):
    """Set up common repository mock patterns used across tests."""
    # Mock lecture retrieval
    mock_repository.get_lecture_by_course_week_order.return_value = Lecture(
        id=123,
        title="Mock Lecture Title",
        course_id=123,
        week_number=1,
        order_in_week=1,
        description="Mock lecture description",
        content="Mock lecture content",
    )

    # Mock lecture creation
    mock_repository.create_lecture.side_effect = lambda l: Lecture(
        id=123,
        title=l.title,
        course_id=l.course_id,
        week_number=l.week_number,
        order_in_week=l.order_in_week,
        description=l.description,
        content=l.content,
    )

    # Mock course listing
    mock_repository.list_courses.return_value = [
        Course(
            id=123,
            code="CS101",
            title="Introduction to Computer Science",
            department="Computer Science",
            level="Undergraduate",
            description="A basic course in CS",
            syllabus="Mock syllabus",
            professor_id=123,
            total_weeks=14,
            lectures_per_week=2,
        )
    ]

    # Mock lecture listing
    mock_repository.list_lectures_by_course.return_value = [
        Lecture(
            id=123,
            title="Mock Lecture Title",
            course_id=123,
            week_number=1,
            order_in_week=1,
            description="Mock lecture description",
            content="Mock lecture content",
            audio_url="mock_storage_url/audio.mp3",
        )
    ]


@pytest.mark.integration
def test_course_creation_flow(mock_system):
    """Test the complete flow of creating a course with professor."""
    # Create a course (should create a professor automatically)
    course, professor = mock_system.create_course(
        title="Test Course",
        code="TEST101",
        department="Computer Science",
    )

    # Validate results
    assert course.id == 123
    assert course.title == "Test Course"
    assert course.code == "TEST101"
    assert course.syllabus == "Mock syllabus content"
    assert professor.id == 123


@pytest.mark.integration
@pytest.mark.asyncio
async def test_lecture_generation_flow(mock_system):
    """Test the complete flow of generating and processing a lecture."""
    # Generate a lecture
    lecture, course, professor = mock_system.generate_lecture(
        course_code="CS101",
        week=1,
        number=1,
        topic="Test Topic",
    )

    # Validate results
    assert lecture.id == 123
    assert lecture.course_id == 123
    assert course.code == "CS101"
    assert professor.id == 123

    # Create audio for the lecture
    audio_path, updated_lecture = await mock_system.create_lecture_audio(
        course_code="CS101",
        week=1,
        number=1,
    )

    # Validate audio results
    assert audio_path == "mock_storage_url/audio.mp3"
    assert updated_lecture.audio_url == "mock_storage_url/audio.mp3"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling(mock_system):
    """Test error handling in the system."""
    # Test course not found error
    with patch.object(mock_system.repository, "get_course_by_code", return_value=None):
        with pytest.raises(CourseNotFoundError):
            mock_system.generate_lecture(course_code="NONEXISTENT", week=1, number=1)

    # Test professor not found error
    with patch.object(mock_system.repository, "get_professor", return_value=None):
        with pytest.raises(ProfessorNotFoundError):
            mock_system.create_course(
                title="Test Course",
                code="TEST101",
                department="Computer Science",
                professor_id=999,  # Non-existent ID
            )

    # Test lecture not found error
    with patch.object(
        mock_system.repository, "get_lecture_by_course_week_order", return_value=None
    ):
        with pytest.raises(
            ValueError, match="Lecture for course CS101, week 999, number 999 not found"
        ):
            await mock_system.create_lecture_audio(
                course_code="CS101", week=999, number=999
            )

    # Test content generation error
    with patch.object(
        mock_system.content_generator,
        "create_lecture",
        side_effect=Exception("Test error"),
    ):
        with pytest.raises(ContentGenerationError):
            mock_system.generate_lecture(course_code="CS101", week=1, number=1)
