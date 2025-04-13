"""
Unit tests for data models.
"""

from datetime import datetime
import pytest
from artificial_u.models.core import Department, Professor, Course, Lecture, Voice


@pytest.mark.unit
def test_department_creation():
    """Test Department model creation and validation."""
    dept = Department(
        name="Computer Science",
        code="CS",
        faculty="Science and Engineering",
        description="Study of computation and information",
    )

    assert dept.name == "Computer Science"
    assert dept.code == "CS"
    assert dept.faculty == "Science and Engineering"
    assert dept.description == "Study of computation and information"
    assert dept.id is None  # Optional field should be None by default


@pytest.mark.unit
def test_voice_creation():
    """Test Voice model creation and validation."""
    voice = Voice(
        el_voice_id="test_voice_123",
        name="British Male Teacher",
        accent="british",
        gender="male",
        age="middle_aged",
        descriptive="professional",
        use_case="informative_educational",
        category="premade",
        language="en",
        locale="en-GB",
        description="A professional British male voice suitable for educational content",
        preview_url="https://example.com/preview.mp3",
    )

    assert voice.el_voice_id == "test_voice_123"
    assert voice.name == "British Male Teacher"
    assert voice.accent == "british"
    assert voice.gender == "male"
    assert voice.age == "middle_aged"
    assert voice.language == "en"
    assert voice.id is None  # Optional field should be None by default
    assert isinstance(voice.verified_languages, dict)
    assert voice.verified_languages == {}  # Should be empty by default
    assert isinstance(voice.last_updated, datetime)


@pytest.mark.unit
def test_voice_minimal_creation():
    """Test Voice model creation with only required fields."""
    voice = Voice(
        el_voice_id="minimal_voice_456",
        name="Basic Voice",
    )

    assert voice.el_voice_id == "minimal_voice_456"
    assert voice.name == "Basic Voice"
    assert voice.accent is None
    assert voice.gender is None
    assert voice.age is None
    assert voice.language is None
    assert voice.id is None
    assert isinstance(voice.verified_languages, dict)
    assert voice.verified_languages == {}
    assert isinstance(voice.last_updated, datetime)


@pytest.mark.unit
def test_professor_creation():
    """Test Professor model creation and validation."""
    prof = Professor(
        name="Dr. Jane Smith",
        title="Associate Professor",
        department_id=1,
        specialization="Machine Learning",
        background="15 years of research experience in ML",
        personality="Enthusiastic and engaging",
        teaching_style="Interactive with hands-on examples",
        voice_id=1,
    )

    assert prof.name == "Dr. Jane Smith"
    assert prof.department_id == 1
    assert prof.voice_id == 1
    assert prof.image_path is None


@pytest.mark.unit
def test_course_creation():
    """Test Course model creation and validation."""
    course = Course(
        code="CS101",
        title="Introduction to Programming",
        department="Computer Science",
        level="Undergraduate",
        professor_id=1,
        description="Basic programming concepts",
        lectures_per_week=2,
        total_weeks=14,
    )

    assert course.code == "CS101"
    assert course.credits == 3  # Default value
    assert course.lectures_per_week == 2
    assert course.total_weeks == 14
    assert isinstance(course.generated_at, datetime)


@pytest.mark.unit
def test_lecture_creation():
    """Test Lecture model creation and validation."""
    lecture = Lecture(
        title="Introduction to Python",
        course_id=101,
        week_number=1,
        order_in_week=1,
        description="Overview of Python basics",
        content="Welcome to your first Python lecture...",
    )

    assert lecture.title == "Introduction to Python"
    assert lecture.week_number == 1
    assert lecture.order_in_week == 1
    assert lecture.audio_url is None
    assert isinstance(lecture.generated_at, datetime)


@pytest.mark.unit
def test_invalid_department():
    """Test Department model validation with missing required fields."""
    with pytest.raises(ValueError):
        Department(
            name="Computer Science",
            # Missing required code field
            faculty="Science and Engineering",
            description="Study of computation",
        )


@pytest.mark.unit
def test_invalid_voice():
    """Test Voice model validation with missing required fields."""
    with pytest.raises(ValueError):
        Voice(
            # Missing required el_voice_id field
            name="Invalid Voice",
        )

    with pytest.raises(ValueError):
        Voice(
            el_voice_id="missing_name_voice",
            # Missing required name field
        )


@pytest.mark.unit
def test_invalid_professor():
    """Test Professor model validation with missing required fields."""
    with pytest.raises(ValueError):
        Professor(
            name="Dr. Jane Smith",
            # Missing required title field
            department="Computer Science",
            # Missing other required fields
        )


@pytest.mark.unit
def test_invalid_course():
    """Test Course model validation with invalid field values."""
    with pytest.raises(ValueError):
        Course(
            code="CS101",
            title="Introduction to Programming",
            department="Computer Science",
            level="Undergraduate",
            professor_id=1,
            description="Basic programming concepts",
            lectures_per_week=-1,  # Invalid negative value
            total_weeks=14,
        )


@pytest.mark.unit
def test_invalid_lecture():
    """Test Lecture model validation with invalid field values."""
    with pytest.raises(ValueError):
        Lecture(
            title="Introduction to Python",
            course_id=101,
            week_number=0,  # Invalid week number
            order_in_week=1,
            description="Overview of Python basics",
            content="Welcome to your first Python lecture...",
        )
