"""
Integration tests for hidden-course discoverability.

Hidden courses (and their topics/lectures) must not surface in discovery
queries except for their owner or an admin, while direct course-scoped
lookups still return them.
"""

import uuid

import pytest

from artificial_u.api.routers.search import global_search
from artificial_u.models.core import Course, Department, Faculty, Lecture, Professor, Topic
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.models.visibility import discoverable_courses


@pytest.fixture
def repository(test_db_url):
    return RepositoryFactory(db_url=test_db_url)


@pytest.fixture
def tag():
    """Unique marker so search/list assertions only see this test's rows."""
    return f"vis{uuid.uuid4().hex[:8]}"


@pytest.fixture
def owner(repository, tag):
    return repository.student.create(name="Owner", email=None, auth0_sub=f"auth0|{tag}-owner")


@pytest.fixture
def other_student(repository, tag):
    return repository.student.create(name="Other", email=None, auth0_sub=f"auth0|{tag}-other")


@pytest.fixture
def admin(repository, tag):
    student = repository.student.create(name="Admin", email=None, auth0_sub=f"auth0|{tag}-admin")
    return student.model_copy(update={"role": "admin"})


@pytest.fixture
def world(repository, owner, tag):
    """A professor teaching one published and one hidden course, each with a lecture."""
    faculty = repository.faculty.create(Faculty(name=f"Faculty {tag}", language="en"))
    department = repository.department.create(
        Department(name=f"Dept {tag}", code=tag.upper(), faculty_id=faculty.id, language="en")
    )
    professor = repository.professor.create(
        Professor(name=f"Prof {tag}", title="Professor", department_id=department.id)
    )

    def make_course(status: str) -> tuple[Course, Lecture]:
        course = repository.course.create(
            Course(
                code=f"{tag}-{status}",
                title=f"{tag} {status} course",
                status=status,
                created_by=owner.id,
                department_id=department.id,
                professor_id=professor.id,
                language="en",
            )
        )
        topic = repository.topic.create(
            Topic(title=f"{tag} {status} topic", order=1, week=1, course_id=course.id)
        )
        lecture = repository.lecture.create(
            Lecture(
                course_id=course.id,
                topic_id=topic.id,
                revision=1,
                title=f"{tag} {status} lecture",
                content="content",
                audio_url="storage://audio.mp3",
            )
        )
        return course, lecture

    published, published_lecture = make_course("published")
    hidden, hidden_lecture = make_course("hidden")
    return {
        "department": department,
        "professor": professor,
        "published": published,
        "hidden": hidden,
        "published_lecture": published_lecture,
        "hidden_lecture": hidden_lecture,
    }


def _course_ids(repository, world, viewer):
    courses = repository.course.list(
        professor_id=world["professor"].id, course_filter=discoverable_courses(viewer)
    )
    return {c.id for c in courses}


@pytest.mark.integration
def test_course_listing_hides_hidden_from_anonymous_and_non_owners(
    repository, world, other_student
):
    published_only = {world["published"].id}
    assert _course_ids(repository, world, None) == published_only
    assert _course_ids(repository, world, other_student) == published_only


@pytest.mark.integration
def test_course_listing_shows_hidden_to_owner_and_admin(repository, world, owner, admin):
    both = {world["published"].id, world["hidden"].id}
    assert _course_ids(repository, world, owner) == both
    assert _course_ids(repository, world, admin) == both


@pytest.mark.integration
def test_lecture_discovery_filters_but_course_scoped_listing_does_not(repository, world):
    discovered = repository.lecture.list(
        professor_id=world["professor"].id, course_filter=discoverable_courses(None), size=100
    )
    assert {lec.id for lec in discovered} == {world["published_lecture"].id}
    assert (
        repository.lecture.count(
            professor_id=world["professor"].id, course_filter=discoverable_courses(None)
        )
        == 1
    )

    # Direct access by course id: no visibility filter
    direct = repository.lecture.list(course_id=world["hidden"].id)
    assert {lec.id for lec in direct} == {world["hidden_lecture"].id}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_hides_hidden_content_from_non_owners(
    repository, world, tag, owner, other_student
):
    for viewer in (None, other_student):
        results = await global_search(
            q=tag, limit=20, repository_factory=repository, student=viewer
        )
        assert [c.id for c in results.courses] == [world["published"].id]
        assert [lec.id for lec in results.lectures] == [world["published_lecture"].id]
        assert {t.course_id for t in results.topics} == {world["published"].id}

    owner_results = await global_search(
        q=tag, limit=20, repository_factory=repository, student=owner
    )
    assert {c.id for c in owner_results.courses} == {world["published"].id, world["hidden"].id}
    assert len(owner_results.lectures) == 2
    assert len(owner_results.topics) == 2


@pytest.mark.integration
def test_only_owner_or_admin_can_newly_connect_hidden_course(
    repository, world, owner, other_student, admin
):
    requested = [world["published"].id, world["hidden"].id]
    find = repository.course.find_disallowed_connections

    assert find(None, requested, None) == [world["hidden"].id]
    assert find(None, requested, other_student) == [world["hidden"].id]
    assert find(None, requested, owner) == []
    assert find(None, requested, admin) == []


@pytest.mark.integration
def test_existing_connection_to_since_hidden_course_is_kept(repository, world, other_student):
    published = world["published"]
    other_course = repository.course.create(
        published.model_copy(
            update={"id": None, "code": f"{published.code}-other", "created_by": other_student.id}
        )
    )
    repository.course.set_connected_courses(other_course.id, [published.id])

    # The connected course's owner hides it after the fact; re-saving keeps the connection
    repository.course.update(
        repository.course.get(published.id).model_copy(update={"status": "hidden"})
    )
    find = repository.course.find_disallowed_connections
    assert find(other_course.id, [published.id], other_student) == []
    # ...but a different course can't newly connect to it
    assert find(None, [published.id], other_student) == [published.id]
