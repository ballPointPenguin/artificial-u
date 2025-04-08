"""
Unit tests for data models.
"""

from datetime import datetime
import pytest
from artificial_u.models.core import Department, Professor, Course, Lecture


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


def test_professor_creation():
    """Test Professor model creation and validation."""
    prof = Professor(
        name="Dr. Jane Smith",
        title="Associate Professor",
        department="Computer Science",
        specialization="Machine Learning",
        background="15 years of research experience in ML",
        personality="Enthusiastic and engaging",
        teaching_style="Interactive with hands-on examples",
    )

    assert prof.name == "Dr. Jane Smith"
    assert prof.department == "Computer Science"
    assert isinstance(prof.voice_settings, dict)
    assert prof.voice_settings == {}  # Should be empty by default
    assert prof.image_path is None


def test_course_creation():
    """Test Course model creation and validation."""
    course = Course(
        code="CS101",
        title="Introduction to Programming",
        department="Computer Science",
        level="Undergraduate",
        professor_id="prof_123",
        description="Basic programming concepts",
        lectures_per_week=2,
        total_weeks=14,
    )

    assert course.code == "CS101"
    assert course.credits == 3  # Default value
    assert course.lectures_per_week == 2
    assert course.total_weeks == 14
    assert isinstance(course.generated_at, datetime)


def test_lecture_creation():
    """Test Lecture model creation and validation."""
    lecture = Lecture(
        title="Introduction to Python",
        course_id="CS101",
        week_number=1,
        order_in_week=1,
        description="Overview of Python basics",
        content="Welcome to your first Python lecture...",
    )

    assert lecture.title == "Introduction to Python"
    assert lecture.week_number == 1
    assert lecture.order_in_week == 1
    assert lecture.audio_path is None
    assert isinstance(lecture.generated_at, datetime)


def test_invalid_department():
    """Test Department model validation with missing required fields."""
    with pytest.raises(ValueError):
        Department(
            name="Computer Science",
            # Missing required code field
            faculty="Science and Engineering",
            description="Study of computation",
        )


def test_invalid_professor():
    """Test Professor model validation with missing required fields."""
    with pytest.raises(ValueError):
        Professor(
            name="Dr. Jane Smith",
            # Missing required title field
            department="Computer Science",
            # Missing other required fields
        )


def test_invalid_course():
    """Test Course model validation with invalid field values."""
    with pytest.raises(ValueError):
        Course(
            code="CS101",
            title="Introduction to Programming",
            department="Computer Science",
            level="Undergraduate",
            professor_id="prof_123",
            description="Basic programming concepts",
            lectures_per_week=-1,  # Invalid negative value
            total_weeks=14,
        )


def test_invalid_lecture():
    """Test Lecture model validation with invalid field values."""
    with pytest.raises(ValueError):
        Lecture(
            title="Introduction to Python",
            course_id="CS101",
            week_number=0,  # Invalid week number
            order_in_week=1,
            description="Overview of Python basics",
            content="Welcome to your first Python lecture...",
        )
