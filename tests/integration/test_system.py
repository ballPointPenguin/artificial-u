"""
Integration tests for UniversitySystem.

These tests verify the interaction between different components
but mock external API calls.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from artificial_u.system import UniversitySystem
from artificial_u.models.core import Professor, Course, Lecture
from artificial_u.utils.exceptions import (
    ProfessorNotFoundError,
    CourseNotFoundError,
    LectureNotFoundError,
    ContentGenerationError,
)
from artificial_u.config.defaults import DEFAULT_LOG_LEVEL


@pytest.fixture
def mock_system():
    """Create a system with mocked dependencies for testing."""
    with patch("artificial_u.system.create_generator") as mock_create_generator, patch(
        "artificial_u.system.AudioProcessor"
    ) as MockAudioProcessor, patch(
        "artificial_u.system.Repository"
    ) as MockRepository, patch(
        "artificial_u.system.Path.mkdir"
    ):

        # Set up mock content generator
        mock_content_generator = MagicMock()
        mock_content_generator.create_course_syllabus.return_value = (
            "Mock syllabus content"
        )
        mock_content_generator.create_lecture.return_value = Lecture(
            title="Mock Lecture",
            course_id="course123",
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

        # Set up mock audio processor
        mock_audio_processor = MockAudioProcessor.return_value
        mock_audio_processor.get_voice_id_for_professor.return_value = "voice123"
        mock_audio_processor.text_to_speech.return_value = ("mock_audio_path.mp3", 300)

        # Set up mock repository
        mock_repository = MockRepository.return_value
        mock_repository.create_professor.side_effect = lambda p: Professor(
            id="prof123",
            name=p.name,
            title=p.title,
            department=p.department,
            specialization=p.specialization,
            background=p.background,
            teaching_style=p.teaching_style,
            personality=p.personality,
            voice_settings=p.voice_settings,
            gender=p.gender,
            accent=p.accent,
            description=p.description,
            age=p.age,
        )
        mock_repository.create_course.side_effect = lambda c: Course(
            id="course123",
            code=c.code,
            title=c.title,
            department=c.department,
            level=c.level,
            description=c.description,
            syllabus=c.syllabus,
            professor_id=c.professor_id,
            total_weeks=c.total_weeks,
            lectures_per_week=c.lectures_per_week,
        )
        mock_repository.get_professor.return_value = Professor(
            id="prof123",
            name="Dr. Mock",
            title="Professor of Computer Science",
            department="Computer Science",
            specialization="Artificial Intelligence",
            background="Test background",
            teaching_style="Interactive",
            personality="Enthusiastic",
            voice_settings={"voice_id": "voice123"},
            gender="Male",
            accent="British",
            description="A distinguished professor with a professorial appearance",
            age=52,
        )
        mock_repository.get_course_by_code.return_value = Course(
            id="course123",
            code="CS101",
            title="Introduction to Computer Science",
            department="Computer Science",
            level="Undergraduate",
            description="A basic course in CS",
            syllabus="Mock syllabus",
            professor_id="prof123",
            total_weeks=14,
            lectures_per_week=2,
        )

        # Create system with mocked dependencies
        system = UniversitySystem(
            anthropic_api_key="mock_key",
            db_path=":memory:",
            audio_path="test_audio",
            text_export_path="test_lectures",
            log_level="ERROR",  # Reduce log noise in tests
        )

        # Replace mocked repository methods with common test patterns
        setup_common_repository_patterns(mock_repository)

        yield system


def setup_common_repository_patterns(mock_repository):
    """Set up common repository mock patterns used across tests."""
    # Mock lecture retrieval
    mock_repository.get_lecture_by_course_week_order.return_value = Lecture(
        id="lecture123",
        title="Mock Lecture Title",
        course_id="course123",
        week_number=1,
        order_in_week=1,
        description="Mock lecture description",
        content="Mock lecture content",
    )

    # Mock lecture creation
    mock_repository.create_lecture.side_effect = lambda l: Lecture(
        id="lecture123",
        title=l.title,
        course_id=l.course_id,
        week_number=l.week_number,
        order_in_week=l.order_in_week,
        description=l.description,
        content=l.content,
    )

    # Mock lecture audio update
    mock_repository.update_lecture_audio.side_effect = lambda id, path: Lecture(
        id=id,
        title="Mock Lecture Title",
        course_id="course123",
        week_number=1,
        order_in_week=1,
        description="Mock lecture description",
        content="Mock lecture content",
        audio_path=path,
    )

    # Mock course listing
    mock_repository.list_courses.return_value = [
        Course(
            id="course123",
            code="CS101",
            title="Introduction to Computer Science",
            department="Computer Science",
            level="Undergraduate",
            description="A basic course in CS",
            syllabus="Mock syllabus",
            professor_id="prof123",
            total_weeks=14,
            lectures_per_week=2,
        )
    ]

    # Mock lecture listing
    mock_repository.list_lectures_by_course.return_value = [
        Lecture(
            id="lecture123",
            title="Mock Lecture Title",
            course_id="course123",
            week_number=1,
            order_in_week=1,
            description="Mock lecture description",
            content="Mock lecture content",
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
    assert course.id == "course123"
    assert course.title == "Test Course"
    assert course.code == "TEST101"
    assert course.syllabus == "Mock syllabus content"
    assert professor.id == "prof123"


@pytest.mark.integration
def test_lecture_generation_flow(mock_system):
    """Test the complete flow of generating and processing a lecture."""
    # Generate a lecture
    lecture, course, professor = mock_system.generate_lecture(
        course_code="CS101",
        week=1,
        number=1,
        topic="Test Topic",
    )

    # Validate results
    assert lecture.id == "lecture123"
    assert lecture.course_id == "course123"
    assert course.code == "CS101"
    assert professor.id == "prof123"

    # Create audio for the lecture
    audio_path, lecture = mock_system.create_lecture_audio(
        course_code="CS101",
        week=1,
        number=1,
    )

    # Validate audio results
    assert audio_path == "mock_audio_path.mp3"
    assert lecture.audio_path == "mock_audio_path.mp3"


@pytest.mark.integration
def test_error_handling(mock_system):
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
                professor_id="nonexistent_id",
            )

    # Test lecture not found error
    with patch.object(
        mock_system.repository, "get_lecture_by_course_week_order", return_value=None
    ):
        with pytest.raises(LectureNotFoundError):
            mock_system.create_lecture_audio(course_code="CS101", week=999, number=999)

    # Test content generation error
    with patch.object(
        mock_system.content_generator,
        "create_lecture",
        side_effect=Exception("Test error"),
    ):
        with pytest.raises(ContentGenerationError):
            mock_system.generate_lecture(course_code="CS101", week=1, number=1)
