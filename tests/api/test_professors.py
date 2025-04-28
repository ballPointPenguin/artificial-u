"""
Tests for the professor API endpoints.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app
from artificial_u.models.core import Course, Lecture, Professor

# Base data definitions
sample_professors_base = [
    Professor(
        id=i,
        name=f"Dr. Test Professor {i}",
        title=f"Professor of Test {i}",
        department_id=1,
        specialization=f"Test Specialization {i}",
        background="Test background",
        personality="Test personality",
        teaching_style="Test teaching style",
        gender="Male",
        accent="Standard",
        description=f"Description for professor {i}",
        age=45 + i,
        voice_id=1,
        image_url=f"/path/to/image{i}.jpg",
    )
    for i in range(1, 4)
]

sample_courses_base = [
    Course(
        id=i,
        code=f"TEST{i}01",
        title=f"Test Course {i}",
        department_id=1,
        level="Undergraduate",
        credits=3,
        professor_id=i,
        description=f"Test course description {i}",
        lectures_per_week=2,
        total_weeks=14,
    )
    for i in range(1, 4)
]

sample_lectures_data = []
for i in range(1, 7):
    lecture_dict = {
        "id": i,
        "title": f"Test Lecture {i}",
        "course_id": (i % 3) + 1,
        "week_number": 1,
        "order_in_week": i,
        "description": f"Test lecture description {i}",
        "content": f"Test lecture content {i}",
    }
    sample_lectures_data.append(lecture_dict)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_repository(monkeypatch):
    """Mock repository with encapsulated state for testing professor API."""

    # --- State local to this fixture instance ---
    local_sample_professors = [
        Professor(**p.model_dump()) for p in sample_professors_base
    ]
    local_sample_courses = [Course(**c.model_dump()) for c in sample_courses_base]
    local_sample_lectures = [Lecture(**lec_dict) for lec_dict in sample_lectures_data]
    # --- End Local State ---

    # --- Define and Patch Repository Methods (using helpers) ---
    _patch_professor_repo_methods(monkeypatch, locals())
    _patch_prof_dependent_repo_methods(monkeypatch, locals())
    # --- End Patching ---

    # Return the local state if tests need to inspect it
    return locals()


# --- Mock Function Definitions (Outside Fixture) ---
def mock_list_professors(local_sample_professors, *args, **kwargs):
    # Add filtering logic if service passes filters to repo
    # For now, return all as service handles filtering
    return local_sample_professors


def mock_get_professor(local_sample_professors, professor_id, *args, **kwargs):
    return next((p for p in local_sample_professors if p.id == professor_id), None)


def mock_create_professor_impl(local_sample_professors, professor):
    new_id = (
        max(p.id for p in local_sample_professors) if local_sample_professors else 0
    ) + 1
    professor.id = new_id
    local_sample_professors.append(professor)
    return professor


def mock_update_professor_impl(local_sample_professors, professor):
    for i, p in enumerate(local_sample_professors):
        if p.id == professor.id:
            local_sample_professors[i] = professor
            return professor
    return None


def mock_delete_professor_impl(local_sample_professors, prof_id):
    initial_len = len(local_sample_professors)
    # Simulate constraint checks if needed (e.g., check courses)
    new_list = [p for p in local_sample_professors if p.id != prof_id]
    local_sample_professors[:] = new_list
    return len(local_sample_professors) < initial_len


def mock_list_courses(local_sample_courses, *args, **kwargs):
    # Service currently filters after getting all, so just return all
    return local_sample_courses


def mock_list_lectures_by_course(local_sample_lectures, course_id, *args, **kwargs):
    return [lec for lec in local_sample_lectures if lec.course_id == course_id]


# --- Patching Helper Functions ---
def _patch_professor_repo_methods(monkeypatch, local_state):
    local_profs = local_state["local_sample_professors"]
    monkeypatch.setattr(
        "artificial_u.models.repositories.professor.ProfessorRepository.list",
        lambda self, **kwargs: mock_list_professors(local_profs, **kwargs),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.professor.ProfessorRepository.get",
        lambda self, pid, **kwargs: mock_get_professor(local_profs, pid, **kwargs),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.professor.ProfessorRepository.create",
        lambda self, prof, **kwargs: mock_create_professor_impl(local_profs, prof),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.professor.ProfessorRepository.update",
        lambda self, prof, **kwargs: mock_update_professor_impl(local_profs, prof),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.professor.ProfessorRepository.delete",
        lambda self, pid, **kwargs: mock_delete_professor_impl(local_profs, pid),
    )


def _patch_prof_dependent_repo_methods(monkeypatch, local_state):
    local_courses = local_state["local_sample_courses"]
    local_lecs = local_state["local_sample_lectures"]
    monkeypatch.setattr(
        "artificial_u.models.repositories.course.CourseRepository.list",
        lambda self, **kwargs: mock_list_courses(local_courses, **kwargs),
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.lecture.LectureRepository.list_by_course",
        lambda self, cid, **kwargs: mock_list_lectures_by_course(
            local_lecs, cid, **kwargs
        ),
    )


@pytest.mark.api
def test_list_professors(client, mock_repository):
    """Test listing professors endpoint."""
    response = client.get("/api/v1/professors")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == len(sample_professors_base)
    assert data["total"] == len(sample_professors_base)


@pytest.mark.api
def test_get_professor(client, mock_repository):
    """Test getting a single professor by ID."""
    # Test with valid ID
    response = client.get("/api/v1/professors/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Dr. Test Professor 1"

    # Test with invalid ID
    response = client.get("/api/v1/professors/999")
    assert response.status_code == 404


@pytest.mark.api
def test_create_professor(client, mock_repository):
    """Test creating a new professor."""
    new_professor = {
        "name": "Dr. New Professor",
        "title": "Professor of New",
        "department_id": 1,
        "specialization": "New Specialization",
        "background": "New background",
        "personality": "New personality",
        "teaching_style": "New teaching style",
        "gender": "Female",
        "accent": "British",
        "description": "A brilliant new professor",
        "age": 42,
        "voice_id": 1,
        "image_url": "/path/to/new_image.jpg",
    }
    response = client.post("/api/v1/professors", json=new_professor)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 4
    assert data["name"] == "Dr. New Professor"


@pytest.mark.api
def test_update_professor(client, mock_repository):
    """Test updating an existing professor."""
    updated_data = {
        "name": "Dr. Updated Professor",
        "title": "Professor of Updated",
        "department_id": 2,
        "specialization": "Updated Specialization",
        "background": "Updated background",
        "personality": "Updated personality",
        "teaching_style": "Updated teaching style",
        "gender": "Non-binary",
        "accent": "Australian",
        "description": "An updated professor profile",
        "age": 50,
        "voice_id": 2,
        "image_url": "/path/to/updated_image.jpg",
    }
    # Test with valid ID
    response = client.put("/api/v1/professors/1", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Dr. Updated Professor"

    # Test with invalid ID
    response = client.put("/api/v1/professors/999", json=updated_data)
    assert response.status_code == 404


@pytest.mark.api
def test_delete_professor(client, mock_repository):
    """Test deleting a professor."""
    # Test with valid ID
    response = client.delete("/api/v1/professors/1")
    assert response.status_code == 204

    # Test with invalid ID
    response = client.delete("/api/v1/professors/999")
    assert response.status_code == 404


@pytest.mark.api
def test_get_professor_courses(client, mock_repository):
    """Test getting courses for a professor."""
    # Test with valid ID
    response = client.get("/api/v1/professors/1/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["professor_id"] == 1
    assert len(data["courses"]) == 1

    # Test with invalid ID
    response = client.get("/api/v1/professors/999/courses")
    assert response.status_code == 404


@pytest.mark.api
def test_get_professor_lectures(client, mock_repository):
    """Test getting lectures by a professor."""
    # Test with valid ID
    response = client.get("/api/v1/professors/1/lectures")
    assert response.status_code == 200
    data = response.json()
    assert data["professor_id"] == 1
    assert len(data["lectures"]) == 2

    # Test with invalid ID
    response = client.get("/api/v1/professors/999/lectures")
    assert response.status_code == 404
