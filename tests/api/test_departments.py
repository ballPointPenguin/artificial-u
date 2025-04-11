"""
Tests for the department API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app
from artificial_u.models.core import Department, Professor, Course
from artificial_u.models.database import Repository


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_repository(monkeypatch):
    """Mock repository for testing."""
    # Sample department data
    sample_departments = [
        Department(
            id=i,
            name=f"Test Department {i}",
            code=f"TD{i}",
            faculty=f"Test Faculty {i % 2 + 1}",
            description=f"Description for department {i}",
        )
        for i in range(1, 4)
    ]

    # Sample professor data
    sample_professors = [
        Professor(
            id=i,
            name=f"Dr. Test Professor {i}",
            title=f"Professor of Test {i}",
            department="Test Department 1" if i < 3 else "Test Department 2",
            specialization=f"Test Specialization {i}",
            background="Test background",
            personality="Test personality",
            teaching_style="Test teaching style",
        )
        for i in range(1, 5)
    ]

    # Sample courses data
    sample_courses = [
        Course(
            id=i,
            code=f"TEST{i}01",
            title=f"Test Course {i}",
            department="Test Department 1" if i < 3 else "Test Department 2",
            level="Undergraduate",
            credits=3,
            professor_id=i,
            description=f"Test course description {i}",
            lectures_per_week=2,
            total_weeks=14,
        )
        for i in range(1, 5)
    ]

    # Mock the repository methods
    def mock_list_departments(self, faculty=None, *args, **kwargs):
        if faculty:
            return [d for d in sample_departments if d.faculty == faculty]
        return sample_departments

    def mock_get_department(self, department_id, *args, **kwargs):
        for department in sample_departments:
            if department.id == department_id:
                return department
        return None

    def mock_get_department_by_code(self, code, *args, **kwargs):
        for department in sample_departments:
            if department.code == code:
                return department
        return None

    def mock_create_department(self, department, *args, **kwargs):
        department.id = len(sample_departments) + 1
        return department

    def mock_update_department(self, department, *args, **kwargs):
        for i, d in enumerate(sample_departments):
            if d.id == department.id:
                sample_departments[i] = department
                return department
        return None

    def mock_list_professors(self, *args, **kwargs):
        return sample_professors

    def mock_list_courses(self, department=None, *args, **kwargs):
        if department:
            return [c for c in sample_courses if c.department == department]
        return sample_courses

    # Patch the Repository methods
    monkeypatch.setattr(Repository, "list_departments", mock_list_departments)
    monkeypatch.setattr(Repository, "get_department", mock_get_department)
    monkeypatch.setattr(
        Repository, "get_department_by_code", mock_get_department_by_code
    )
    monkeypatch.setattr(Repository, "create_department", mock_create_department)
    monkeypatch.setattr(Repository, "update_department", mock_update_department)
    monkeypatch.setattr(Repository, "list_professors", mock_list_professors)
    monkeypatch.setattr(Repository, "list_courses", mock_list_courses)

    return sample_departments


@pytest.mark.api
def test_list_departments(client, mock_repository):
    """Test listing departments endpoint."""
    response = client.get("/api/v1/departments")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 3
    assert data["total"] == 3


@pytest.mark.api
def test_filter_departments_by_faculty(client, mock_repository):
    """Test filtering departments by faculty."""
    response = client.get("/api/v1/departments?faculty=Test Faculty 1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert item["faculty"] == "Test Faculty 1"


@pytest.mark.api
def test_filter_departments_by_name(client, mock_repository):
    """Test filtering departments by name."""
    response = client.get("/api/v1/departments?name=Department 1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert "Department 1" in item["name"]


@pytest.mark.api
def test_get_department(client, mock_repository):
    """Test getting a single department by ID."""
    # Test with valid ID
    response = client.get("/api/v1/departments/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Test Department 1"

    # Test with invalid ID
    response = client.get("/api/v1/departments/999")
    assert response.status_code == 404


@pytest.mark.api
def test_delete_department(client, mock_repository):
    """Test deleting a department."""
    # We need to mock the return value of delete_department in the service, not in the repository
    # For simplicity, we'll consider:
    # - Department 3 will be successfully deleted (no professors or courses)
    # - Department 1 will fail because it has professors (checked in service layer)
    # - Department 999 doesn't exist

    # Test with valid ID and no professors (ID 3)
    response = client.delete("/api/v1/departments/3")
    assert response.status_code == 204

    # Test with valid ID but with professors (ID 1)
    response = client.delete("/api/v1/departments/1")
    assert response.status_code == 409

    # Test with invalid ID
    response = client.delete("/api/v1/departments/999")
    assert response.status_code == 404


@pytest.mark.api
def test_create_department(client, mock_repository):
    """Test creating a new department."""
    new_department = {
        "name": "New Department",
        "code": "ND1",
        "faculty": "New Faculty",
        "description": "A brand new department",
    }
    response = client.post("/api/v1/departments", json=new_department)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 4
    assert data["name"] == "New Department"
    assert data["code"] == "ND1"


@pytest.mark.api
def test_update_department(client, mock_repository):
    """Test updating an existing department."""
    updated_data = {
        "name": "Updated Department",
        "code": "UD1",
        "faculty": "Updated Faculty",
        "description": "An updated department description",
    }
    # Test with valid ID
    response = client.put("/api/v1/departments/1", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Updated Department"
    assert data["code"] == "UD1"

    # Test with invalid ID
    response = client.put("/api/v1/departments/999", json=updated_data)
    assert response.status_code == 404


@pytest.mark.api
def test_get_department_professors(client, mock_repository):
    """Test getting professors in a department."""
    # Test with valid ID for Test Department 1
    response = client.get("/api/v1/departments/1/professors")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 1
    assert "professors" in data
    assert len(data["professors"]) == 2  # 2 professors in Test Department 1

    # Test with valid ID for Test Department 2
    response = client.get("/api/v1/departments/2/professors")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 2
    assert len(data["professors"]) == 2  # 2 professors in Test Department 2

    # Test with invalid ID
    response = client.get("/api/v1/departments/999/professors")
    assert response.status_code == 404


@pytest.mark.api
def test_get_department_courses(client, mock_repository):
    """Test getting courses in a department."""
    # Test with valid ID for Test Department 1
    response = client.get("/api/v1/departments/1/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 1
    assert "courses" in data
    assert len(data["courses"]) == 2  # 2 courses in Test Department 1

    # Test with valid ID for Test Department 2
    response = client.get("/api/v1/departments/2/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 2
    assert len(data["courses"]) == 2  # 2 courses in Test Department 2

    # Test with invalid ID
    response = client.get("/api/v1/departments/999/courses")
    assert response.status_code == 404
