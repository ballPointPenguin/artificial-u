"""
Tests for the course API endpoints.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app
from artificial_u.models.core import Course, Department, Lecture, Professor

# Base data definitions
sample_courses_base = [
    Course(
        id=i,
        code=f"CS{i}01",
        title=f"Test Course {i}",
        department_id=1,  # Link all sample courses to Dept 1 for simplicity
        level="Undergraduate" if i % 2 == 0 else "Graduate",
        credits=3,
        professor_id=i,  # Link course i to professor i
        description=f"Description for course {i}",
        lectures_per_week=2,
        total_weeks=14,
        # Add generated_at for validation in CourseResponse
        generated_at=datetime.now(),
    )
    for i in range(1, 4)
]

sample_professors_base = [
    Professor(
        id=i,
        name=f"Dr. Test Professor {i}",
        title=f"Professor of Test {i}",
        department_id=1,  # Ensure professors are in Dept 1
        specialization=f"Test Specialization {i}",
        background="Test background",
        personality="Test personality",
        teaching_style="Test teaching style",
        # Add other fields if needed by ProfessorBrief
    )
    for i in range(1, 4)
]

sample_departments_base = [
    Department(
        id=1,
        name="Computer Science",
        code="CS",
        faculty="Science and Engineering",
        description="The Computer Science department",
        generated_at=datetime.now(),
    ),
    Department(
        id=2,
        name="Mathematics",
        code="MATH",
        faculty="Science and Engineering",
        description="The Mathematics department",
        generated_at=datetime.now(),
    ),
]

sample_lectures_data = []  # Renamed to avoid conflict
for i in range(1, 5):  # Create 4 lectures
    course_id = (i % 2) + 1  # Assign to courses 1 and 2
    sample_lectures_data.append(
        {
            "id": i,
            "title": f"Lecture {i} for Course {course_id}",
            "course_id": course_id,
            "week_number": 1,
            "order_in_week": i,
            "description": f"Description for lecture {i}",
            "content": "Test content",
            "audio_url": None,
            "generated_at": datetime.now(),
        }
    )


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_repository(monkeypatch):
    """Mock repository with encapsulated state for testing course API."""

    # --- State local to this fixture instance ---
    local_sample_courses = [Course(**c.model_dump()) for c in sample_courses_base]
    local_sample_professors = [
        Professor(**p.model_dump()) for p in sample_professors_base
    ]
    local_sample_departments = [
        Department(**d.model_dump()) for d in sample_departments_base
    ]
    local_sample_lectures = [Lecture(**lec_dict) for lec_dict in sample_lectures_data]
    # --- End Local State ---

    # --- Define and Patch Repository Methods ---
    _patch_course_repo_methods(monkeypatch, locals())
    _patch_dependent_repo_methods(monkeypatch, locals())
    # --- End Patching ---

    # Return the local state dictionary if tests need to inspect it
    return locals()  # Return the dict containing local lists


# --- Mock Function Definitions (Outside Fixture) ---


def mock_list_courses(local_sample_courses, department_id=None, *args, **kwargs):
    if department_id:
        return [c for c in local_sample_courses if c.department_id == department_id]
    return local_sample_courses


def mock_get_course(local_sample_courses, course_id, *args, **kwargs):
    return next((c for c in local_sample_courses if c.id == course_id), None)


def mock_get_course_by_code(local_sample_courses, code, *args, **kwargs):
    return next((c for c in local_sample_courses if c.code == code), None)


def mock_create_course_impl(local_sample_courses, course):
    new_id = (
        max(c.id for c in local_sample_courses) if local_sample_courses else 0
    ) + 1
    course.id = new_id
    if not hasattr(course, "generated_at"):
        course.generated_at = datetime.now()
    local_sample_courses.append(course)
    return course


def mock_update_course_impl(local_sample_courses, course):
    for i, existing_course in enumerate(local_sample_courses):
        if existing_course.id == course.id:
            local_sample_courses[i] = course
            return course
    return None


def mock_delete_course_impl(local_sample_courses, course_id):
    initial_len = len(local_sample_courses)
    new_list = [c for c in local_sample_courses if c.id != course_id]
    # Note: We are modifying the list passed by reference (nonlocal behavior)
    local_sample_courses[:] = new_list
    return len(local_sample_courses) < initial_len


def mock_get_professor(local_sample_professors, professor_id, *args, **kwargs):
    return next((p for p in local_sample_professors if p.id == professor_id), None)


def mock_get_department(local_sample_departments, department_id, *args, **kwargs):
    return next((d for d in local_sample_departments if d.id == department_id), None)


def mock_list_lectures_by_course(local_sample_lectures, course_id, *args, **kwargs):
    return [lec for lec in local_sample_lectures if lec.course_id == course_id]


# --- Patching Helper Functions ---
def _patch_course_repo_methods(monkeypatch, local_state):
    local_courses = local_state["local_sample_courses"]
    # Use lambdas to capture the current local_courses list for the mocks
    monkeypatch.setattr(
        "artificial_u.models.repositories.course.CourseRepository.list",
        lambda self, **kwargs: mock_list_courses(local_courses, **kwargs),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.course.CourseRepository.get",
        lambda self, cid, **kwargs: mock_get_course(local_courses, cid, **kwargs),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.course.CourseRepository.get_by_code",
        lambda self, code, **kwargs: mock_get_course_by_code(
            local_courses, code, **kwargs
        ),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.course.CourseRepository.create",
        lambda self, course, **kwargs: mock_create_course_impl(local_courses, course),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.course.CourseRepository.update",
        lambda self, course, **kwargs: mock_update_course_impl(local_courses, course),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.course.CourseRepository.delete",
        lambda self, cid, **kwargs: mock_delete_course_impl(local_courses, cid),
    )


def _patch_dependent_repo_methods(monkeypatch, local_state):
    local_profs = local_state["local_sample_professors"]
    local_depts = local_state["local_sample_departments"]
    local_lecs = local_state["local_sample_lectures"]
    monkeypatch.setattr(
        "artificial_u.models.repositories.professor.ProfessorRepository.get",
        lambda self, pid, **kwargs: mock_get_professor(local_profs, pid, **kwargs),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.department.DepartmentRepository.get",
        lambda self, did, **kwargs: mock_get_department(local_depts, did, **kwargs),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.lecture.LectureRepository.list_by_course",
        lambda self, cid, **kwargs: mock_list_lectures_by_course(
            local_lecs, cid, **kwargs
        ),
    )


@pytest.mark.api
def test_list_courses(client, mock_repository):
    """Test listing courses endpoint."""
    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == len(sample_courses_base)
    assert data["total"] == len(sample_courses_base)


@pytest.mark.api
def test_filter_courses_by_department(client, mock_repository):
    """Test filtering courses by department ID."""
    # Note: Service/Router might filter by name, but repo mock expects ID if filtering happens there
    # Adjust query parameter based on actual router implementation
    response = client.get("/api/v1/courses?department_id=1")
    assert response.status_code == 200
    data = response.json()
    expected_count = sum(1 for c in sample_courses_base if c.department_id == 1)
    assert len(data["items"]) == expected_count
    assert data["total"] == expected_count
    for item in data["items"]:
        assert item["department_id"] == 1


@pytest.mark.api
def test_filter_courses_by_level(client, mock_repository):
    """Test filtering courses by level."""
    response = client.get("/api/v1/courses?level=Undergraduate")
    assert response.status_code == 200
    data = response.json()
    expected_count = sum(1 for c in sample_courses_base if c.level == "Undergraduate")
    assert len(data["items"]) == expected_count
    assert data["total"] == expected_count
    for item in data["items"]:
        assert item["level"] == "Undergraduate"


@pytest.mark.api
def test_get_course(client, mock_repository):
    """Test getting a single course by ID."""
    # Test with valid ID
    response = client.get("/api/v1/courses/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["code"] == "CS101"
    assert data["department_id"] == 1

    # Test with invalid ID
    response = client.get("/api/v1/courses/999")
    assert response.status_code == 404


@pytest.mark.api
def test_get_course_by_code(client, mock_repository):
    """Test getting a course by code."""
    # Test with valid code
    response = client.get("/api/v1/courses/code/CS101")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["code"] == "CS101"
    assert data["department_id"] == 1

    # Test with invalid code
    response = client.get("/api/v1/courses/code/INVALID")
    assert response.status_code == 404


@pytest.mark.api
def test_create_course(client, mock_repository):
    """Test creating a new course."""
    new_course = {
        "code": "CS501",
        "title": "Advanced Programming",
        "department_id": 1,
        "level": "Graduate",
        "credits": 4,
        "professor_id": 1,
        "description": "An advanced programming course",
        "lectures_per_week": 2,
        "total_weeks": 15,
    }
    response = client.post("/api/v1/courses", json=new_course)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 4
    assert data["code"] == "CS501"
    assert data["title"] == "Advanced Programming"
    assert data["department_id"] == 1


@pytest.mark.api
def test_update_course(client, mock_repository):
    """Test updating an existing course."""
    updated_data = {
        "code": "CS101-Updated",
        "title": "Updated Course Title",
        "department_id": 2,
        "level": "Undergraduate",
        "credits": 4,
        "professor_id": 1,
        "description": "Updated description",
        "lectures_per_week": 3,
        "total_weeks": 12,
    }
    # Test with valid ID
    response = client.put("/api/v1/courses/1", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["code"] == "CS101-Updated"
    assert data["title"] == "Updated Course Title"
    assert data["department_id"] == 2

    # Test with invalid ID
    response = client.put("/api/v1/courses/999", json=updated_data)
    assert response.status_code == 404


@pytest.mark.api
def test_delete_course(client, mock_repository):
    """Test deleting a course."""
    # Test with valid ID
    response = client.delete("/api/v1/courses/1")
    assert response.status_code == 204

    # Verify it's deleted by trying to get it
    get_response = client.get("/api/v1/courses/1")
    assert get_response.status_code == 404

    # Test with invalid ID
    response = client.delete("/api/v1/courses/999")
    assert response.status_code == 404


@pytest.mark.api
def test_get_course_professor(client, mock_repository):
    """Test getting the professor for a course."""
    # Test with valid course ID (Course 1 -> Prof 1)
    response = client.get("/api/v1/courses/1/professor")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Dr. Test Professor 1"

    # Test with invalid course ID
    response = client.get("/api/v1/courses/999/professor")
    assert response.status_code == 404


@pytest.mark.api
def test_get_course_department(client, mock_repository):
    """Test getting the department for a course."""
    # Test with valid course ID (Course 1 -> Dept 1)
    response = client.get("/api/v1/courses/1/department")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Computer Science"
    assert "code" in data
    assert "faculty" in data
    assert data["id"] == 1

    # Test with invalid course ID
    response = client.get("/api/v1/courses/999/department")
    assert response.status_code == 404


@pytest.mark.api
def test_get_course_lectures(client, mock_repository):
    """Test getting lectures for a course."""
    # Test with valid course ID (Course 1 -> Lectures 1, 3)
    response = client.get("/api/v1/courses/1/lectures")
    assert response.status_code == 200
    data = response.json()
    assert data["course_id"] == 1
    assert "lectures" in data
    assert len(data["lectures"]) == 2

    # Test with invalid course ID
    response = client.get("/api/v1/courses/999/lectures")
    assert response.status_code == 404
