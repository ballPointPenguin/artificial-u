"""
Integration tests for the database models and repository.
"""

import pytest

from artificial_u.models.core import Course, Department, Lecture, Professor, Topic
from artificial_u.models.repositories import RepositoryFactory


@pytest.fixture
def repository(test_db_url):
    """Create a repository instance with the test database."""
    return RepositoryFactory(db_url=test_db_url)


@pytest.fixture
def sample_department():
    """Create a sample department for testing."""
    return Department(
        name="Test Department",
        code="TEST",
        faculty="Science and Engineering",
        description="A test department for testing purposes",
    )


@pytest.fixture
def db_department(repository, sample_department):
    """Create a department in the database for testing."""
    return repository.department.create(sample_department)


@pytest.fixture
def sample_professor(db_department):
    """Create a sample professor for testing."""
    return Professor(
        name="Dr. Test Professor",
        title="Professor of Testing",
        accent="British",
        age=42,
        background="Extensive experience in test-driven development",
        description="A test professor for testing purposes",
        gender="Male",
        personality="Detail-oriented and methodical",
        specialization="Software Testing",
        teaching_style="Interactive with frequent code examples",
        department_id=db_department.id,
    )


@pytest.fixture
def db_professor(repository, sample_professor):
    """Create a professor in the database for testing."""
    return repository.professor.create(sample_professor)


@pytest.fixture
def sample_course(db_professor, db_department):
    """Create a sample course for testing."""
    return Course(
        code="TEST101",
        title="Introduction to Testing",
        credits=3,
        description="A comprehensive introduction to software testing principles",
        lectures_per_week=2,
        level="Undergraduate",
        total_weeks=14,
        department_id=db_department.id,
        professor_id=db_professor.id,
    )


@pytest.fixture
def db_course(repository, sample_course):
    """Create a course in the database for testing."""
    return repository.course.create(sample_course)


@pytest.fixture
def sample_topic(db_course):
    """Create a sample topic for testing."""
    return Topic(
        title="Unit Testing Fundamentals",
        order=1,
        week=1,
        course_id=db_course.id,
    )


@pytest.fixture
def db_topic(repository, sample_topic):
    """Create a topic in the database for testing."""
    return repository.topic.create(sample_topic)


@pytest.fixture
def sample_lecture(db_course, db_topic):
    """Create a sample lecture for testing."""
    return Lecture(
        course_id=db_course.id,
        revision=1,
        content="In this lecture, we will explore the fundamentals of unit testing...",
        summary="This lecture covers the basics of unit testing",
        audio_url="storage://test_audio.mp3",
        transcript_url="storage://test_transcript.txt",
        topic_id=db_topic.id,
    )


@pytest.fixture
def db_lecture(repository, sample_lecture):
    """Create a lecture in the database for testing."""
    return repository.lecture.create(sample_lecture)


@pytest.mark.integration
def test_department_crud(repository, sample_department):
    """Test CRUD operations for departments."""
    # Create
    created_dept = repository.department.create(sample_department)
    assert created_dept.id is not None

    # Get
    retrieved_dept = repository.department.get(created_dept.id)
    assert retrieved_dept is not None
    assert retrieved_dept.name == sample_department.name

    # Get by code
    code_retrieved_dept = repository.department.get_by_code(sample_department.code)
    assert code_retrieved_dept is not None
    assert code_retrieved_dept.id == created_dept.id

    # List
    departments = repository.department.list()
    assert len(departments) >= 1
    assert any(d.id == created_dept.id for d in departments)

    # Update
    retrieved_dept.name = "Updated Department"
    updated_dept = repository.department.update(retrieved_dept)
    assert updated_dept is not None
    assert updated_dept.name == "Updated Department"

    # Verify update
    verified_dept = repository.department.get(created_dept.id)
    assert verified_dept.name == "Updated Department"

    # Delete
    deleted_dept = repository.department.delete(created_dept.id)
    assert deleted_dept is True

    # Verify delete
    deleted_dept = repository.department.get(created_dept.id)
    assert deleted_dept is None


@pytest.mark.integration
def test_professor_crud(repository, sample_professor):
    """Test CRUD operations for professors."""
    # Create
    created_prof = repository.professor.create(sample_professor)
    assert created_prof.id is not None

    # Get
    retrieved_prof = repository.professor.get(created_prof.id)
    assert retrieved_prof is not None
    assert retrieved_prof.name == sample_professor.name

    # List
    professors = repository.professor.list()
    assert len(professors) >= 1
    assert any(p.id == created_prof.id for p in professors)

    # List by department
    department_professors = repository.professor.list_by_department(created_prof.department_id)
    assert len(department_professors) >= 1
    assert any(p.id == created_prof.id for p in department_professors)

    # Update
    retrieved_prof.title = "Updated Professor of Testing"
    updated_prof = repository.professor.update(retrieved_prof)
    assert updated_prof.title == "Updated Professor of Testing"

    # Verify update
    verified_prof = repository.professor.get(created_prof.id)
    assert verified_prof.title == "Updated Professor of Testing"

    # Delete
    deleted_prof = repository.professor.delete(created_prof.id)
    assert deleted_prof is True

    # Verify delete
    deleted_prof = repository.professor.get(created_prof.id)
    assert deleted_prof is None


@pytest.mark.integration
def test_course_crud(repository, sample_course):
    """Test CRUD operations for courses."""
    # Create
    created_course = repository.course.create(sample_course)
    assert created_course.id is not None

    # Get
    retrieved_course = repository.course.get(created_course.id)
    assert retrieved_course is not None
    assert retrieved_course.code == sample_course.code

    # Get by code
    code_retrieved_course = repository.course.get_by_code(sample_course.code)
    assert code_retrieved_course is not None
    assert code_retrieved_course.id == created_course.id

    # List
    courses = repository.course.list()
    assert len(courses) >= 1
    assert any(c.id == created_course.id for c in courses)

    # List by Department
    department_courses = repository.course.list(created_course.department_id)
    assert len(department_courses) >= 1
    assert any(c.id == created_course.id for c in department_courses)

    # Update
    retrieved_course.title = "Updated Course"
    updated_course = repository.course.update(retrieved_course)
    assert updated_course is not None
    assert updated_course.title == "Updated Course"

    # Verify update
    verified_course = repository.course.get(created_course.id)
    assert verified_course.title == "Updated Course"

    # Delete
    deleted_course = repository.course.delete(created_course.id)
    assert deleted_course is True

    # Verify delete
    deleted_course = repository.course.get(created_course.id)
    assert deleted_course is None


@pytest.mark.integration
def test_topic_crud(repository, sample_topic):
    """Test CRUD operations for topics."""
    # Create
    created_topic = repository.topic.create(sample_topic)
    assert created_topic.id is not None

    # Get
    retrieved_topic = repository.topic.get(created_topic.id)
    assert retrieved_topic is not None
    assert retrieved_topic.title == sample_topic.title

    # Get by course/week/order
    course_week_order_topic = repository.topic.get_by_course_week_order(
        created_topic.course_id, created_topic.week, created_topic.order
    )
    assert course_week_order_topic is not None
    assert course_week_order_topic.id == created_topic.id

    # List by course
    course_topics = repository.topic.list_by_course(created_topic.course_id)
    assert len(course_topics) >= 1
    assert any(t.id == created_topic.id for t in course_topics)

    # List by course/week
    course_week_topics = repository.topic.list_by_course_week(
        created_topic.course_id, created_topic.week
    )
    assert len(course_week_topics) >= 1
    assert any(t.id == created_topic.id for t in course_week_topics)

    # Update
    retrieved_topic.title = "Updated Topic"
    updated_topic = repository.topic.update(retrieved_topic)
    assert updated_topic is not None
    assert updated_topic.title == "Updated Topic"

    # Verify update
    verified_topic = repository.topic.get(created_topic.id)
    assert verified_topic.title == "Updated Topic"

    # Delete
    deleted_topic = repository.topic.delete(created_topic.id)
    assert deleted_topic is True

    # Verify delete
    deleted_topic = repository.topic.get(created_topic.id)
    assert deleted_topic is None


@pytest.mark.integration
def test_topic_create_batch(repository, sample_topic):
    """Test creating a batch of topics."""
    # Create batch
    created_topics = repository.topic.create_batch([sample_topic, sample_topic])
    assert len(created_topics) == 2
    assert all(topic.id is not None for topic in created_topics)


@pytest.mark.integration
def test_topic_delete_by_course(repository, db_topic):
    """Test deleting topics by course."""
    # Delete by course
    deleted_course_topics = repository.topic.delete_by_course(db_topic.course_id)
    assert deleted_course_topics == 1

    # Verify delete by course
    course_topics = repository.topic.list_by_course(db_topic.course_id)
    assert len(course_topics) == 0


@pytest.mark.integration
def test_lecture_crud(repository, sample_lecture):
    """Test CRUD operations for lectures."""
    # Create
    created_lecture = repository.lecture.create(sample_lecture)
    assert created_lecture.id is not None

    # Get
    retrieved_lecture = repository.lecture.get(created_lecture.id)
    assert retrieved_lecture is not None

    # Get content
    content = repository.lecture.get_content(created_lecture.id)
    assert content is not None

    # Get audio URL
    audio_url = repository.lecture.get_audio_url(created_lecture.id)
    assert audio_url is not None

    # Get transcript URL
    transcript_url = repository.lecture.get_transcript_url(created_lecture.id)
    assert transcript_url is not None

    # List by course
    course_lectures = repository.lecture.list_by_course(created_lecture.course_id)
    assert len(course_lectures) >= 1
    assert any(lecture.id == created_lecture.id for lecture in course_lectures)

    # List by topic
    topic_lectures = repository.lecture.list_by_topic(created_lecture.topic_id)
    assert len(topic_lectures) >= 1
    assert any(lecture.id == created_lecture.id for lecture in topic_lectures)

    # List
    lectures = repository.lecture.list()
    assert len(lectures) >= 1
    assert any(lecture.id == created_lecture.id for lecture in lectures)

    # Update
    retrieved_lecture.content = "Updated lecture content"
    updated_lecture = repository.lecture.update(retrieved_lecture)
    assert updated_lecture is not None
    assert updated_lecture.content == "Updated lecture content"

    # Verify update
    verified_lecture = repository.lecture.get(created_lecture.id)
    assert verified_lecture.content == "Updated lecture content"

    # Delete
    deleted_lecture = repository.lecture.delete(created_lecture.id)
    assert deleted_lecture is True

    # Verify delete
    deleted_lecture = repository.lecture.get(created_lecture.id)
    assert deleted_lecture is None


@pytest.mark.integration
def test_lecture_delete_by_course(repository, db_lecture):
    """Test deleting lectures by course."""
    # Delete by course
    deleted_count = repository.lecture.delete_by_course(db_lecture.course_id)
    assert deleted_count == 1

    # Verify delete by course
    course_lectures = repository.lecture.list_by_course(db_lecture.course_id)
    assert len(course_lectures) == 0


@pytest.mark.integration
def test_lecture_delete_by_topic(repository, db_lecture):
    """Test deleting lectures by topic."""
    # Delete by topic
    deleted_count = repository.lecture.delete_by_topic(db_lecture.topic_id)
    assert deleted_count == 1

    # Verify delete by topic
    topic_lectures = repository.lecture.list_by_topic(db_lecture.topic_id)
    assert len(topic_lectures) == 0
