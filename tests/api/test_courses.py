"""
Tests for the course API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app
from artificial_u.models.core import Course, Professor, Department, Lecture
from artificial_u.models.database import Repository


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_repository(monkeypatch):
    """Mock repository for testing."""
    # Sample course data
    sample_courses = [
        Course(
            id=i,
            code=f"CS{i}01",
            title=f"Test Course {i}",
            department="Computer Science",
            level="Undergraduate" if i % 2 == 0 else "Graduate",
            credits=3,
            professor_id=i,
            description=f"Description for course {i}",
            lectures_per_week=2,
            total_weeks=14,
        )
        for i in range(1, 4)
    ]

    # Sample professor data
    sample_professors = [
        Professor(
            id=i,
            name=f"Dr. Test Professor {i}",
            title=f"Professor of Test {i}",
            department="Computer Science",
            specialization=f"Test Specialization {i}",
            background="Test background",
            personality="Test personality",
            teaching_style="Test teaching style",
        )
        for i in range(1, 4)
    ]

    # Sample department data
    sample_departments = [
        Department(
            id=1,
            name="Computer Science",
            code="CS",
            faculty="Science and Engineering",
            description="The Computer Science department",
        ),
        Department(
            id=2,
            name="Mathematics",
            code="MATH",
            faculty="Science and Engineering",
            description="The Mathematics department",
        ),
    ]

    # Sample lecture data
    sample_lectures = []
    for course_id in range(1, 4):
        for week in range(1, 3):  # 2 weeks
            for order in range(1, 3):  # 2 lectures per week
                sample_lectures.append(
                    {
                        "id": len(sample_lectures) + 1,
                        "title": f"Lecture {week}.{order} for Course {course_id}",
                        "course_id": course_id,
                        "week_number": week,
                        "order_in_week": order,
                        "description": f"Description for lecture {week}.{order} of course {course_id}",
                        "content": "Test content",
                        "audio_path": None,
                    }
                )

    # Mock the repository methods
    def mock_list_courses(self, department=None, *args, **kwargs):
        if department:
            return [c for c in sample_courses if c.department == department]
        return sample_courses

    def mock_get_course(self, course_id, *args, **kwargs):
        for course in sample_courses:
            if course.id == course_id:
                return course
        return None

    def mock_get_course_by_code(self, code, *args, **kwargs):
        for course in sample_courses:
            if course.code == code:
                return course
        return None

    def mock_create_course(self, course, *args, **kwargs):
        course.id = len(sample_courses) + 1
        return course

    def mock_get_professor(self, professor_id, *args, **kwargs):
        for professor in sample_professors:
            if professor.id == professor_id:
                return professor
        return None

    def mock_list_departments(self, *args, **kwargs):
        return sample_departments

    def mock_list_lectures_by_course(self, course_id, *args, **kwargs):
        return [
            Lecture(**lecture)
            for lecture in sample_lectures
            if lecture["course_id"] == course_id
        ]

    # Patch the Repository methods
    monkeypatch.setattr(Repository, "list_courses", mock_list_courses)
    monkeypatch.setattr(Repository, "get_course", mock_get_course)
    monkeypatch.setattr(Repository, "get_course_by_code", mock_get_course_by_code)
    monkeypatch.setattr(Repository, "create_course", mock_create_course)
    monkeypatch.setattr(Repository, "get_professor", mock_get_professor)
    monkeypatch.setattr(Repository, "list_departments", mock_list_departments)
    monkeypatch.setattr(
        Repository, "list_lectures_by_course", mock_list_lectures_by_course
    )

    return sample_courses


@pytest.mark.api
def test_list_courses(client, mock_repository):
    """Test listing courses endpoint."""
    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 3
    assert data["total"] == 3


@pytest.mark.api
def test_filter_courses_by_department(client, mock_repository):
    """Test filtering courses by department."""
    response = client.get("/api/v1/courses?department=Computer%20Science")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert item["department"] == "Computer Science"


@pytest.mark.api
def test_filter_courses_by_level(client, mock_repository):
    """Test filtering courses by level."""
    response = client.get("/api/v1/courses?level=Undergraduate")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
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

    # Test with invalid code
    response = client.get("/api/v1/courses/code/INVALID")
    assert response.status_code == 404


@pytest.mark.api
def test_create_course(client, mock_repository):
    """Test creating a new course."""
    new_course = {
        "code": "CS501",
        "title": "Advanced Programming",
        "department": "Computer Science",
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


@pytest.mark.api
def test_update_course(client, mock_repository):
    """Test updating an existing course."""
    updated_data = {
        "code": "CS101-Updated",
        "title": "Updated Course Title",
        "department": "Computer Science",
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

    # Test with invalid ID
    response = client.put("/api/v1/courses/999", json=updated_data)
    assert response.status_code == 404


@pytest.mark.api
def test_delete_course(client, mock_repository):
    """Test deleting a course."""
    # Test with valid ID
    response = client.delete("/api/v1/courses/1")
    assert response.status_code == 204

    # Test with invalid ID
    response = client.delete("/api/v1/courses/999")
    assert response.status_code == 404


@pytest.mark.api
def test_get_course_professor(client, mock_repository):
    """Test getting the professor for a course."""
    # Test with valid course ID
    response = client.get("/api/v1/courses/1/professor")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "name" in data
    assert "title" in data

    # Test with invalid course ID
    response = client.get("/api/v1/courses/999/professor")
    assert response.status_code == 404


@pytest.mark.api
def test_get_course_department(client, mock_repository):
    """Test getting the department for a course."""
    # Test with valid course ID
    response = client.get("/api/v1/courses/1/department")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Computer Science"
    assert "code" in data
    assert "faculty" in data

    # Test with invalid course ID
    response = client.get("/api/v1/courses/999/department")
    assert response.status_code == 404


@pytest.mark.api
def test_get_course_lectures(client, mock_repository):
    """Test getting lectures for a course."""
    # Test with valid course ID
    response = client.get("/api/v1/courses/1/lectures")
    assert response.status_code == 200
    data = response.json()
    assert data["course_id"] == 1
    assert "lectures" in data
    assert len(data["lectures"]) == 4  # 2 weeks * 2 lectures per week = 4 total

    # Test with invalid course ID
    response = client.get("/api/v1/courses/999/lectures")
    assert response.status_code == 404
