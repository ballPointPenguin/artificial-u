"""
Tests for the professor API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app
from artificial_u.models.core import Professor, Course, Lecture
from artificial_u.models.database import Repository


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_repository(monkeypatch):
    """Mock repository for testing."""
    # Sample professor data
    sample_professors = [
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
            image_path=f"/path/to/image{i}.jpg",
        )
        for i in range(1, 4)
    ]

    # Sample courses data
    sample_courses = [
        Course(
            id=i,
            code=f"TEST{i}01",
            title=f"Test Course {i}",
            department="Test Department",
            level="Undergraduate",
            credits=3,
            professor_id=1,
            description=f"Test course description {i}",
            lectures_per_week=2,
            total_weeks=14,
        )
        for i in range(1, 3)
    ]

    # Sample lectures data
    sample_lectures = [
        Lecture(
            id=i,
            title=f"Test Lecture {i}",
            course_id=1,
            week_number=1,
            order_in_week=i,
            description=f"Test lecture description {i}",
            content=f"Test lecture content {i}",
        )
        for i in range(1, 4)
    ]

    # Mock the repository methods
    def mock_list_professors(self, *args, **kwargs):
        return sample_professors

    def mock_get_professor(self, professor_id, *args, **kwargs):
        for professor in sample_professors:
            if professor.id == professor_id:
                return professor
        return None

    def mock_create_professor(self, professor, *args, **kwargs):
        # Set an integer ID instead of a string
        professor.id = len(sample_professors) + 1
        return professor

    def mock_update_professor(self, professor, *args, **kwargs):
        for i, p in enumerate(sample_professors):
            if p.id == professor.id:
                sample_professors[i] = professor
                return professor
        return None

    def mock_list_courses(self, department=None, *args, **kwargs):
        if department:
            return [c for c in sample_courses if c.department == department]
        return sample_courses

    def mock_list_lectures_by_course(self, course_id, *args, **kwargs):
        return [l for l in sample_lectures if l.course_id == course_id]

    # Patch the Repository methods
    monkeypatch.setattr(Repository, "list_professors", mock_list_professors)
    monkeypatch.setattr(Repository, "get_professor", mock_get_professor)
    monkeypatch.setattr(Repository, "create_professor", mock_create_professor)
    monkeypatch.setattr(Repository, "update_professor", mock_update_professor)
    monkeypatch.setattr(Repository, "list_courses", mock_list_courses)
    monkeypatch.setattr(
        Repository, "list_lectures_by_course", mock_list_lectures_by_course
    )

    return sample_professors


@pytest.mark.api
def test_list_professors(client, mock_repository):
    """Test listing professors endpoint."""
    response = client.get("/api/v1/professors")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 3
    assert data["total"] == 3


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
        "image_path": "/path/to/new_image.jpg",
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
        "image_path": "/path/to/updated_image.jpg",
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
    assert len(data["courses"]) == 2

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
    assert len(data["lectures"]) == 3

    # Test with invalid ID
    response = client.get("/api/v1/professors/999/lectures")
    assert response.status_code == 404
