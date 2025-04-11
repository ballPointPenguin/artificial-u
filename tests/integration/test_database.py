"""
Integration tests for the database models and repository.
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from artificial_u.models.core import Professor, Course, Lecture, Department
from artificial_u.models.database import Repository


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """Load environment variables from .env.test file."""
    load_dotenv(".env.test")
    yield


@pytest.fixture(scope="session")
def test_db_url():
    """Get the test database URL from environment."""
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/artificial_u_test",
    )


@pytest.fixture
def repository(test_db_url):
    """Create a repository instance with the test database."""
    return Repository(db_url=test_db_url)


@pytest.fixture
def sample_professor():
    """Create a sample professor for testing."""
    return Professor(
        name="Dr. Test Professor",
        title="Professor of Testing",
        department="Computer Science",
        specialization="Software Testing",
        background="Extensive experience in test-driven development",
        personality="Detail-oriented and methodical",
        teaching_style="Interactive with frequent code examples",
        voice_settings={
            "stability": 0.5,
            "clarity": 0.8,
        },
    )


@pytest.fixture
def db_professor(repository, sample_professor):
    """Create a professor in the database for testing."""
    return repository.create_professor(sample_professor)


@pytest.fixture
def sample_course(db_professor):
    """Create a sample course for testing."""
    return Course(
        code="TEST101",
        title="Introduction to Testing",
        department="Computer Science",
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
    return repository.create_course(sample_course)


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


@pytest.fixture(scope="session")
def db_available(test_db_url):
    """Check if the database is available."""
    try:
        # Try to connect to the database
        engine = create_engine(test_db_url)
        with engine.connect():
            return True
    except OperationalError:
        return False
    except Exception:
        return False


@pytest.fixture(scope="function", autouse=True)
def setup_database(test_db_url, db_available):
    """Set up a clean database for each test function."""
    # Skip if the database is not available
    if not db_available:
        pytest.skip("Database not available")

    # Get the SQLAlchemy engine
    from sqlalchemy import create_engine, text
    from artificial_u.models.database import Base

    engine = create_engine(test_db_url)

    # Truncate all tables instead of dropping and recreating them
    # This preserves the schema while clearing data
    with engine.connect() as conn:
        # Start a transaction
        with conn.begin():
            # Get a list of all tables
            tables = Base.metadata.tables.keys()

            # Disable foreign key constraints during truncation
            conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))

            # Truncate each table
            for table in tables:
                conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))

            # Re-enable constraints
            conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))

    yield

    # Clean up after test (truncate again)
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
            for table in Base.metadata.tables.keys():
                conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
            conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))


@pytest.mark.integration
@pytest.mark.requires_db
def test_professor_crud(repository, sample_professor):
    """Test CRUD operations for professors."""
    # Create
    created_prof = repository.create_professor(sample_professor)
    assert created_prof.id is not None

    # Read
    retrieved_prof = repository.get_professor(created_prof.id)
    assert retrieved_prof is not None
    assert retrieved_prof.name == sample_professor.name
    assert retrieved_prof.voice_settings == sample_professor.voice_settings

    # List
    professors = repository.list_professors()
    assert len(professors) == 1
    assert professors[0].id == created_prof.id

    # Update
    retrieved_prof.title = "Updated Professor of Testing"
    updated_prof = repository.update_professor(retrieved_prof)
    assert updated_prof.title == "Updated Professor of Testing"

    # Verify update
    verified_prof = repository.get_professor(created_prof.id)
    assert verified_prof.title == "Updated Professor of Testing"


@pytest.mark.integration
@pytest.mark.requires_db
def test_course_crud(repository, db_professor, sample_course):
    """Test CRUD operations for courses."""
    # Create course
    created_course = repository.create_course(sample_course)
    assert created_course.id is not None

    # Read
    retrieved_course = repository.get_course(created_course.id)
    assert retrieved_course is not None
    assert retrieved_course.code == sample_course.code

    # Read by code
    code_retrieved_course = repository.get_course_by_code(sample_course.code)
    assert code_retrieved_course is not None
    assert code_retrieved_course.id == created_course.id

    # List
    all_courses = repository.list_courses()
    assert len(all_courses) == 1
    assert all_courses[0].id == created_course.id

    # List by department
    dept_courses = repository.list_courses(department="Computer Science")
    assert len(dept_courses) == 1
    assert dept_courses[0].id == created_course.id


@pytest.mark.integration
@pytest.mark.requires_db
def test_lecture_crud(repository, db_course, sample_lecture):
    """Test CRUD operations for lectures."""
    # Create lecture
    created_lecture = repository.create_lecture(sample_lecture)
    assert created_lecture.id is not None

    # Read
    retrieved_lecture = repository.get_lecture(created_lecture.id)
    assert retrieved_lecture is not None
    assert retrieved_lecture.title == sample_lecture.title

    # Read by course/week/order
    week_lecture = repository.get_lecture_by_course_week_order(
        db_course.id, week_number=1, order_in_week=1
    )
    assert week_lecture is not None
    assert week_lecture.id == created_lecture.id

    # List by course
    course_lectures = repository.list_lectures_by_course(db_course.id)
    assert len(course_lectures) == 1
    assert course_lectures[0].id == created_lecture.id

    # Update audio path
    updated_lecture = repository.update_lecture_audio(
        created_lecture.id, "test_audio.mp3"
    )
    assert updated_lecture is not None
    assert updated_lecture.audio_path == "test_audio.mp3"


@pytest.mark.integration
@pytest.mark.requires_db
def test_relationships(repository, db_professor, db_course, sample_lecture):
    """Test relationships between models."""
    # Create lecture
    created_lecture = repository.create_lecture(sample_lecture)

    # Verify course listing includes the correct professor
    courses = repository.list_courses()
    assert len(courses) == 1
    assert courses[0].professor_id == db_professor.id

    # Verify lecture listing includes the correct course
    lectures = repository.list_lectures_by_course(db_course.id)
    assert len(lectures) == 1
    assert lectures[0].course_id == db_course.id
