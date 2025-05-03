"""
Integration tests for the database models and repository.
"""

import pytest

from artificial_u.models.core import Course, Lecture, Professor
from artificial_u.models.repositories import RepositoryFactory


@pytest.fixture
def repository(test_db_url):
    """Create a repository instance with the test database."""
    return RepositoryFactory(db_url=test_db_url)


@pytest.fixture
def sample_professor():
    """Create a sample professor for testing."""
    return Professor(
        name="Dr. Test Professor",
        title="Professor of Testing",
        specialization="Software Testing",
        background="Extensive experience in test-driven development",
        personality="Detail-oriented and methodical",
        teaching_style="Interactive with frequent code examples",
    )


@pytest.fixture
def db_professor(repository, sample_professor):
    """Create a professor in the database for testing."""
    return repository.professor.create(sample_professor)


@pytest.fixture
def sample_course(db_professor):
    """Create a sample course for testing."""
    return Course(
        code="TEST101",
        title="Introduction to Testing",
        level="Undergraduate",
        credits=3,
        professor_id=db_professor.id,
        description="A comprehensive introduction to software testing principles",
        lectures_per_week=2,
        total_weeks=14,
    )


@pytest.fixture
def db_course(repository, sample_course):
    """Create a course in the database for testing."""
    return repository.course.create(sample_course)


@pytest.fixture
def sample_lecture(db_course):
    """Create a sample lecture for testing."""
    return Lecture(
        title="Unit Testing Fundamentals",
        course_id=db_course.id,
        week_number=1,
        order_in_week=1,
        description="Introduction to unit testing concepts",
        content="In this lecture, we will explore the fundamentals of unit testing...",
    )


@pytest.mark.integration
def test_professor_crud(repository, sample_professor):
    """Test CRUD operations for professors."""
    # Create
    created_prof = repository.professor.create(sample_professor)
    assert created_prof.id is not None

    # Read
    retrieved_prof = repository.professor.get(created_prof.id)
    assert retrieved_prof is not None
    assert retrieved_prof.name == sample_professor.name

    # List
    professors = repository.professor.list()
    assert len(professors) >= 1
    assert any(p.id == created_prof.id for p in professors)

    # Update
    retrieved_prof.title = "Updated Professor of Testing"
    updated_prof = repository.professor.update(retrieved_prof)
    assert updated_prof.title == "Updated Professor of Testing"

    # Verify update
    verified_prof = repository.professor.get(created_prof.id)
    assert verified_prof.title == "Updated Professor of Testing"


@pytest.mark.integration
def test_course_crud(repository):
    """Test CRUD operations for courses."""
    # First create a professor (required by foreign key)
    professor = repository.professor.create(
        Professor(
            name="Dr. Course Test",
            title="Professor of Course Testing",
        )
    )

    # Create a course with this professor
    course = Course(
        code="TEST101",
        title="Introduction to Testing",
        level="Undergraduate",
        credits=3,
        professor_id=professor.id,
        description="A comprehensive introduction to software testing principles",
        lectures_per_week=2,
        total_weeks=14,
    )

    # Create course
    created_course = repository.course.create(course)
    assert created_course.id is not None

    # Read
    retrieved_course = repository.course.get(created_course.id)
    assert retrieved_course is not None
    assert retrieved_course.code == course.code

    # Read by code
    code_retrieved_course = repository.course.get_by_code(course.code)
    assert code_retrieved_course is not None
    assert code_retrieved_course.id == created_course.id

    # List
    all_courses = repository.course.list()
    assert len(all_courses) >= 1
    assert any(c.id == created_course.id for c in all_courses)


@pytest.mark.integration
def test_lecture_crud(repository):
    """Test CRUD operations for lectures."""
    # Create professor and course first (required by foreign keys)
    professor = repository.professor.create(
        Professor(
            name="Dr. Lecture Test",
            title="Professor of Lecture Testing",
        )
    )

    course = repository.course.create(
        Course(
            code="LECT101",
            title="Introduction to Lectures",
            level="Undergraduate",
            credits=3,
            professor_id=professor.id,
            description="A comprehensive introduction to lecture testing",
            lectures_per_week=2,
            total_weeks=14,
        )
    )

    # Create a lecture with this course
    lecture = Lecture(
        title="Unit Testing Fundamentals",
        course_id=course.id,
        week_number=1,
        order_in_week=1,
        description="Introduction to unit testing concepts",
        content="In this lecture, we will explore the fundamentals of unit testing...",
    )

    # Create lecture
    created_lecture = repository.lecture.create(lecture)
    assert created_lecture.id is not None

    # Read
    retrieved_lecture = repository.lecture.get(created_lecture.id)
    assert retrieved_lecture is not None
    assert retrieved_lecture.title == lecture.title

    # Read by course/week/order
    week_lecture = repository.lecture.get_by_course_week_order(
        course.id, week_number=1, order_in_week=1
    )
    assert week_lecture is not None
    assert week_lecture.id == created_lecture.id

    # List by course
    course_lectures = repository.lecture.list_by_course(course.id)
    assert len(course_lectures) >= 1
    assert any(lecture_item.id == created_lecture.id for lecture_item in course_lectures)

    # Update audio path
    lecture_to_update = repository.lecture.get(created_lecture.id)
    lecture_to_update.audio_url = "storage://test_audio.mp3"
    updated_lecture = repository.lecture.update(lecture_to_update)
    assert updated_lecture is not None
    assert updated_lecture.audio_url == "storage://test_audio.mp3"


@pytest.mark.integration
def test_relationships(repository):
    """Test relationships between models."""
    # Create all related records in the correct order
    professor = repository.professor.create(
        Professor(name="Dr. Relationship Test", title="Professor of Relationships")
    )

    course = repository.course.create(
        Course(
            code="REL101",
            title="Introduction to Relationships",
            level="Undergraduate",
            credits=3,
            professor_id=professor.id,
            description="A comprehensive introduction to database relationships",
            lectures_per_week=2,
            total_weeks=14,
        )
    )

    lecture = repository.lecture.create(
        Lecture(
            title="Relationship Fundamentals",
            course_id=course.id,
            week_number=1,
            order_in_week=1,
            description="Introduction to relationship concepts",
            content="In this lecture, we will explore database relationships...",
        )
    )

    # Verify course listing includes the correct professor
    courses = repository.course.list()
    assert len(courses) >= 1
    assert any(c.id == course.id for c in courses)

    # Find the course we just created
    found_course = next(c for c in courses if c.id == course.id)
    assert found_course.professor_id == professor.id

    # Verify lecture listing includes the correct course
    lectures = repository.lecture.list_by_course(course.id)
    assert len(lectures) >= 1
    assert any(lecture_item.id == lecture.id for lecture_item in lectures)
