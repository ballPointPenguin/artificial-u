"""
Integration tests for TopicService.
"""

import logging
from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Professor, Topic
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import CourseService, DepartmentService, ProfessorService, TopicService
from artificial_u.utils import DatabaseError


@pytest.fixture
def repository_factory():
    """Create a repository factory that uses the test database."""
    # The DATABASE_URL will be picked up from .env.test
    return RepositoryFactory()


@pytest.fixture
def department_service(repository_factory):
    """Create a DepartmentService with mocked dependent services."""
    professor_service_mock = MagicMock()
    course_service_mock = MagicMock()
    content_service_mock = MagicMock()
    return DepartmentService(
        repository_factory=repository_factory,
        professor_service=professor_service_mock,
        course_service=course_service_mock,
        content_service=content_service_mock,
    )


@pytest.fixture
def professor_service(repository_factory):
    """Create a ProfessorService with mocked dependent services."""
    content_service_mock = MagicMock()
    image_service_mock = MagicMock()
    voice_service_mock = MagicMock()
    return ProfessorService(
        repository_factory=repository_factory,
        content_service=content_service_mock,
        image_service=image_service_mock,
        voice_service=voice_service_mock,
    )


@pytest.fixture
def course_service(repository_factory, professor_service):
    """Create a CourseService with actual ProfessorService."""
    content_service_mock = MagicMock()
    return CourseService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        content_service=content_service_mock,
    )


@pytest.fixture
def topic_service(repository_factory):
    """Create a TopicService with mocked logger."""
    logger = logging.getLogger(__name__)
    return TopicService(
        repository_factory=repository_factory,
        logger=logger,
    )


@pytest.mark.integration
class TestTopicService:
    """Integration tests for TopicService."""

    def test_create_and_get_topic(
        self, topic_service, course_service, department_service, professor_service
    ):
        """Test creating and retrieving a topic."""
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

        # Create a course
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
        )[0]

        # Create a new topic
        topic = topic_service.create_topic(
            title="Introduction to Python",
            course_id=course.id,
            week=1,
            order=1,
        )

        # Verify it was created with an ID
        assert topic.id is not None
        assert topic.title == "Introduction to Python"
        assert topic.course_id == course.id
        assert topic.week == 1
        assert topic.order == 1

        # Retrieve the topic and verify
        retrieved = topic_service.get_topic(topic.id)
        assert retrieved.id == topic.id
        assert retrieved.title == "Introduction to Python"
        assert retrieved.course_id == course.id
        assert retrieved.week == 1
        assert retrieved.order == 1

    def test_create_topics_batch(
        self, topic_service, course_service, department_service, professor_service
    ):
        """Test creating multiple topics in a batch."""
        # First create a department
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Alan Turing",
                title="Professor",
                department_id=department.id,
                specialization="Computation Theory",
                gender="Male",
            )
        )

        # Create a course
        course = course_service.create_course(
            title="Introduction to Programming",
            code="CS101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create multiple topics
        topics = [
            Topic(
                title="Topic 1",
                course_id=course.id,
                week=1,
                order=1,
            ),
            Topic(
                title="Topic 2",
                course_id=course.id,
                week=1,
                order=2,
            ),
        ]

        created_topics = topic_service.create_topics(topics)

        # Verify all topics were created with IDs
        assert len(created_topics) == 2
        for topic in created_topics:
            assert topic.id is not None

        # Verify the topics can be retrieved
        for topic in created_topics:
            retrieved = topic_service.get_topic(topic.id)
            assert retrieved.id == topic.id
            assert retrieved.title == topic.title

    def test_get_topic_by_course_week_order(
        self, topic_service, course_service, department_service, professor_service
    ):
        """Test getting a topic by course ID, week, and order."""
        # First create a department
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Alan Turing",
                title="Professor",
                department_id=department.id,
                specialization="Computation Theory",
                gender="Male",
            )
        )

        # Create a course
        course = course_service.create_course(
            title="Introduction to Programming",
            code="CS101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create a topic
        topic = topic_service.create_topic(
            title="Advanced Python",
            course_id=course.id,
            week=2,
            order=1,
        )

        # Retrieve by course, week, and order
        retrieved = topic_service.get_topic_by_course_week_order(
            course_id=course.id,
            week=2,
            order=1,
        )

        assert retrieved is not None
        assert retrieved.id == topic.id
        assert retrieved.title == "Advanced Python"

    def test_list_topics_by_course(
        self, topic_service, course_service, department_service, professor_service
    ):
        """Test listing all topics for a course."""
        # First create a department
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Alan Turing",
                title="Professor",
                department_id=department.id,
                specialization="Computation Theory",
                gender="Male",
            )
        )

        # Create two courses
        course1 = course_service.create_course(
            title="Introduction to Programming",
            code="CS101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        course2 = course_service.create_course(
            title="Advanced Programming",
            code="CS201",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create topics for course 1
        topic_service.create_topic(title="Topic 1", course_id=course1.id, week=1, order=1)
        topic_service.create_topic(title="Topic 2", course_id=course1.id, week=1, order=2)
        topic_service.create_topic(
            title="Topic 3", course_id=course2.id, week=1, order=1
        )  # Different course

        # List topics for course 1
        topics = topic_service.list_topics_by_course(course_id=course1.id)
        assert len(topics) >= 2  # At least our 2 topics (could be more if DB has existing data)
        assert all(t.course_id == course1.id for t in topics)

    def test_list_topics_by_course_week(
        self, topic_service, course_service, department_service, professor_service
    ):
        """Test listing topics for a specific course and week."""
        # First create a department
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Alan Turing",
                title="Professor",
                department_id=department.id,
                specialization="Computation Theory",
                gender="Male",
            )
        )

        # Create a course
        course = course_service.create_course(
            title="Introduction to Programming",
            code="CS101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create topics for different weeks
        topic_service.create_topic(title="Week 1 Topic", course_id=course.id, week=1, order=1)
        topic_service.create_topic(title="Week 2 Topic", course_id=course.id, week=2, order=1)
        topic_service.create_topic(title="Week 1 Topic 2", course_id=course.id, week=1, order=2)

        # List topics for week 1
        topics = topic_service.list_topics_by_course_week(course_id=course.id, week=1)
        assert len(topics) >= 2  # At least our 2 topics for week 1
        assert all(t.week == 1 for t in topics)

    def test_update_topic(
        self, topic_service, course_service, department_service, professor_service
    ):
        """Test updating a topic."""
        # First create a department
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Alan Turing",
                title="Professor",
                department_id=department.id,
                specialization="Computation Theory",
                gender="Male",
            )
        )

        # Create a course
        course = course_service.create_course(
            title="Introduction to Programming",
            code="CS101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create a topic
        topic = topic_service.create_topic(
            title="Original Title",
            course_id=course.id,
            week=1,
            order=1,
        )

        # Update the topic
        topic.title = "Updated Title"
        topic.week = 2
        updated = topic_service.update_topic(topic)

        # Verify updates
        assert updated.title == "Updated Title"
        assert updated.week == 2

        # Retrieve to confirm persistence
        retrieved = topic_service.get_topic(topic.id)
        assert retrieved.title == "Updated Title"
        assert retrieved.week == 2

    def test_delete_topic(
        self, topic_service, course_service, department_service, professor_service
    ):
        """Test deleting a topic."""
        # First create a department
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Alan Turing",
                title="Professor",
                department_id=department.id,
                specialization="Computation Theory",
                gender="Male",
            )
        )

        # Create a course
        course = course_service.create_course(
            title="Introduction to Programming",
            code="CS101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create a topic
        topic = topic_service.create_topic(
            title="Topic to Delete",
            course_id=course.id,
            week=1,
            order=1,
        )

        # Delete it
        result = topic_service.delete_topic(topic.id)
        assert result is True

        # Verify it's gone
        assert topic_service.get_topic(topic.id) is None

    def test_delete_topics_by_course(
        self, topic_service, course_service, department_service, professor_service
    ):
        """Test deleting all topics for a course."""
        # First create a department
        department = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty="Engineering",
        )

        # Then create a professor
        professor = professor_service.create_professor(
            Professor(
                name="Dr. Alan Turing",
                title="Professor",
                department_id=department.id,
                specialization="Computation Theory",
                gender="Male",
            )
        )

        # Create two courses
        course1 = course_service.create_course(
            title="Introduction to Programming",
            code="CS101",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        course2 = course_service.create_course(
            title="Advanced Programming",
            code="CS201",
            department_id=department.id,
            level="Undergraduate",
            professor_id=professor.id,
        )[0]

        # Create topics for course 1
        topic_service.create_topic(title="Topic 1", course_id=course1.id, week=1, order=1)
        topic_service.create_topic(title="Topic 2", course_id=course1.id, week=1, order=2)
        topic_service.create_topic(
            title="Topic 3", course_id=course2.id, week=1, order=1
        )  # Different course

        # Delete topics for course 1
        count = topic_service.delete_topics_by_course(course_id=course1.id)
        assert count >= 2  # At least our 2 topics were deleted

        # Verify topics for course 1 are gone
        topics = topic_service.list_topics_by_course(course_id=course1.id)
        assert len(topics) == 0

        # Verify topics for course 2 still exist
        topics = topic_service.list_topics_by_course(course_id=course2.id)
        assert len(topics) >= 1

    def test_error_handling(self, topic_service):
        """Test error handling in topic operations."""
        # Test getting non-existent topic
        assert topic_service.get_topic(999999) is None

        # Test updating non-existent topic
        non_existent_topic = Topic(
            id=999999,
            title="Non-existent",
            course_id=1,
            week=1,
            order=1,
        )
        with pytest.raises(DatabaseError):
            topic_service.update_topic(non_existent_topic)

        # Test deleting non-existent topic
        result = topic_service.delete_topic(999999)
        assert result is False
