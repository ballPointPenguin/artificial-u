"""
Tests for the department API endpoints.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app
from artificial_u.models.core import Course, Department, Professor

# Base data definitions (can be reused)
sample_departments_base = [
    Department(
        id=i,
        name=f"Test Department {i}",
        code=f"TD{i}",
        faculty=f"Test Faculty {i % 2 + 1}",
        description=f"Description for department {i}",
    )
    for i in range(1, 4)
]

sample_professors_base = [
    Professor(
        id=i,
        name=f"Dr. Test Professor {i}",
        title=f"Professor of Test {i}",
        department_id=1 if i < 3 else 2,  # Link to departments 1 and 2
        specialization=f"Test Specialization {i}",
        background="Test background",
        personality="Test personality",
        teaching_style="Test teaching style",
        # Add other fields if needed by ProfessorBrief
    )
    for i in range(1, 5)
]

sample_courses_base = [
    Course(
        id=i,
        code=f"TEST{i}01",
        title=f"Test Course {i}",
        department_id=1 if i < 3 else 2,  # Link to departments 1 and 2
        level="Undergraduate",
        credits=3,
        professor_id=i,  # Link course to professor
        description=f"Test course description {i}",
        lectures_per_week=2,
        total_weeks=14,
        # Add other fields if needed by CourseBrief
    )
    for i in range(1, 5)
]


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_repository(monkeypatch):
    """Mock repository with encapsulated state for testing department API."""

    # --- State local to this fixture instance ---
    local_sample_departments = [
        Department(**d.model_dump()) for d in sample_departments_base
    ]
    local_sample_professors = [
        Professor(**p.model_dump()) for p in sample_professors_base
    ]
    local_sample_courses = [Course(**c.model_dump()) for c in sample_courses_base]
    # --- End Local State ---

    # --- Mock functions operating on local state ---
    def mock_list_departments(self, faculty=None, *args, **kwargs):
        if faculty:
            return [d for d in local_sample_departments if d.faculty == faculty]
        return local_sample_departments

    def mock_get_department(self, department_id, *args, **kwargs):
        return next(
            (d for d in local_sample_departments if d.id == department_id), None
        )

    def mock_get_department_by_code(self, code, *args, **kwargs):
        return next((d for d in local_sample_departments if d.code == code), None)

    def mock_create_department(self, department, *args, **kwargs):
        # Use max ID from LOCAL list + 1
        new_id = (
            max(d.id for d in local_sample_departments)
            if local_sample_departments
            else 0
        ) + 1
        department.id = new_id
        local_sample_departments.append(department)
        return department

    def mock_update_department(self, department, *args, **kwargs):
        for i, d in enumerate(local_sample_departments):
            if d.id == department.id:
                local_sample_departments[i] = department  # Update local list
                return department
        return None

    def mock_delete_department(self, dept_id, *args, **kwargs):
        nonlocal local_sample_departments  # Modify the fixture's local list
        initial_len = len(local_sample_departments)
        # Check LOCAL lists for dependencies
        has_professors = any(
            p.department_id == dept_id for p in local_sample_professors
        )
        has_courses = any(c.department_id == dept_id for c in local_sample_courses)

        if has_professors or has_courses:
            return False  # Simulate constraint violation

        new_list = [d for d in local_sample_departments if d.id != dept_id]
        deleted = len(new_list) < initial_len
        local_sample_departments = new_list  # Update the local list state
        return deleted

    def mock_list_professors(self, *args, **kwargs):
        department_id_filter = kwargs.get("department_id")
        if department_id_filter is not None:
            # Filter LOCAL list
            return [
                p
                for p in local_sample_professors
                if p.department_id == department_id_filter
            ]
        return local_sample_professors

    def mock_list_courses(self, *args, **kwargs):
        department_id_filter = kwargs.get("department_id")
        if department_id_filter is not None:
            # Filter LOCAL list
            return [
                c
                for c in local_sample_courses
                if c.department_id == department_id_filter
            ]
        return local_sample_courses

    # --- End Mock Functions ---

    # --- Patch Repository Methods ---
    monkeypatch.setattr(
        "artificial_u.models.repositories.department.DepartmentRepository.list",
        mock_list_departments,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.department.DepartmentRepository.get",
        mock_get_department,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.department.DepartmentRepository.get_by_code",
        mock_get_department_by_code,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.department.DepartmentRepository.create",
        mock_create_department,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.department.DepartmentRepository.update",
        mock_update_department,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.department.DepartmentRepository.delete",
        mock_delete_department,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.professor.ProfessorRepository.list",
        mock_list_professors,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.course.CourseRepository.list",
        mock_list_courses,
    )
    # --- End Patching ---

    # Return the initial state if tests need it, primarily for inspection
    return {
        "departments": local_sample_departments,
        "professors": local_sample_professors,
        "courses": local_sample_courses,
    }


@pytest.mark.api
def test_list_departments(client, mock_repository):
    """Test listing departments endpoint."""
    response = client.get("/api/v1/departments")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Assert based on initial base data length
    assert len(data["items"]) == len(sample_departments_base)
    assert data["total"] == len(sample_departments_base)


@pytest.mark.api
def test_filter_departments_by_faculty(client, mock_repository):
    """Test filtering departments by faculty."""
    response = client.get("/api/v1/departments?faculty=Test Faculty 1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    # Calculate expected count from base data
    expected_count = sum(
        1 for d in sample_departments_base if d.faculty == "Test Faculty 1"
    )
    assert len(data["items"]) == expected_count
    assert data["total"] == expected_count
    for item in data["items"]:
        assert item["faculty"] == "Test Faculty 1"


@pytest.mark.api
def test_filter_departments_by_name(client, mock_repository):
    """Test filtering departments by name."""
    response = client.get("/api/v1/departments?name=Department 1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert "Department 1" in data["items"][0]["name"]


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
    # Department 3 has no dependencies in base data
    response_delete_3 = client.delete("/api/v1/departments/3")
    assert response_delete_3.status_code == 204

    # Verify Department 3 is gone
    response_get_3 = client.get("/api/v1/departments/3")
    assert response_get_3.status_code == 404

    # Department 1 has dependencies (profs/courses linked to dept_id=1)
    response_delete_1 = client.delete("/api/v1/departments/1")
    assert response_delete_1.status_code == 409  # Expect conflict

    # Department 999 doesn't exist
    response_delete_999 = client.delete("/api/v1/departments/999")
    assert response_delete_999.status_code == 404


@pytest.mark.api
def test_create_department(client, mock_repository):
    """Test creating a new department."""
    initial_count = len(sample_departments_base)
    expected_new_id = initial_count + 1
    new_department = {
        "name": "New Department",
        "code": "ND1",
        "faculty": "New Faculty",
        "description": "A brand new department",
    }
    response = client.post("/api/v1/departments", json=new_department)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == expected_new_id  # Check correct ID based on initial count
    assert data["name"] == "New Department"
    assert data["code"] == "ND1"

    # Verify it was added by getting it
    get_response = client.get(f"/api/v1/departments/{expected_new_id}")
    assert get_response.status_code == 200


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

    # Get the updated department again to check if it was actually updated
    get_response = client.get("/api/v1/departments/1")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["name"] == "Updated Department"

    # Test with invalid ID
    response = client.put("/api/v1/departments/999", json=updated_data)
    assert response.status_code == 404


@pytest.mark.api
def test_get_department_professors(client, mock_repository):
    """Test getting professors in a department."""
    # Calculate expected counts from base data
    expected_dept1_profs = sum(
        1 for p in sample_professors_base if p.department_id == 1
    )
    expected_dept2_profs = sum(
        1 for p in sample_professors_base if p.department_id == 2
    )

    # Test with valid ID for Test Department 1
    response = client.get("/api/v1/departments/1/professors")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 1
    assert "professors" in data
    assert len(data["professors"]) == expected_dept1_profs

    # Test with valid ID for Test Department 2
    response = client.get("/api/v1/departments/2/professors")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 2
    assert len(data["professors"]) == expected_dept2_profs

    # Test with invalid ID
    response = client.get("/api/v1/departments/999/professors")
    assert response.status_code == 404


@pytest.mark.api
def test_get_department_courses(client, mock_repository):
    """Test getting courses in a department."""
    # Calculate expected counts from base data
    expected_dept1_courses = sum(1 for c in sample_courses_base if c.department_id == 1)
    expected_dept2_courses = sum(1 for c in sample_courses_base if c.department_id == 2)

    # Test with valid ID for Test Department 1
    response = client.get("/api/v1/departments/1/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 1
    assert "courses" in data
    assert len(data["courses"]) == expected_dept1_courses

    # Test with valid ID for Test Department 2
    response = client.get("/api/v1/departments/2/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 2
    assert len(data["courses"]) == expected_dept2_courses

    # Test with invalid ID
    response = client.get("/api/v1/departments/999/courses")
    assert response.status_code == 404
