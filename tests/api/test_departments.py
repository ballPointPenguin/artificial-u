"""
Unit Tests for the department API endpoints, mocking the service layer.
"""

from unittest.mock import MagicMock  # Import MagicMock only

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.models.departments import DepartmentCreate  # Keep request model
from artificial_u.api.models.departments import DepartmentUpdate  # Keep request model
from artificial_u.api.models.departments import (
    CourseBrief,
    DepartmentCoursesResponse,
    DepartmentProfessorsResponse,
    DepartmentResponse,
    DepartmentsListResponse,
    ProfessorBrief,
)

# Use base data structures to define mock responses
sample_departments_base = [
    DepartmentResponse(
        id=i,
        name=f"Test Department {i}",
        code=f"TD{i}",
        faculty=f"Test Faculty {i % 2 + 1}",
        description=f"Description for department {i}",
    )
    for i in range(1, 4)
]

sample_professors_brief_base = [
    ProfessorBrief(
        id=i,
        name=f"Dr. Test Professor {i}",
        title=f"Professor of Test {i}",
        specialization=f"Test Specialization {i}",
    )
    for i in range(1, 5)
]

sample_courses_brief_base = [
    CourseBrief(
        id=i,
        code=f"TEST{i}01",
        title=f"Test Course {i}",
        level="Undergraduate",
        credits=3,
        professor_id=i,
    )
    for i in range(1, 5)
]


@pytest.fixture
def mock_api_service(monkeypatch):
    """Mock the DepartmentApiService methods for unit testing the API router."""
    # Use MagicMock for synchronous methods, AsyncMock for async methods
    mock_service = {
        "get_departments": MagicMock(),  # Sync
        "get_department": MagicMock(),  # Sync
        "create_department": MagicMock(),  # Sync
        "update_department": MagicMock(),  # Sync
        "delete_department": MagicMock(),  # Sync
        "get_department_professors": MagicMock(),  # Sync
        "get_department_courses": MagicMock(),  # Sync
        "get_department_by_code": MagicMock(),  # Sync
        # "generate_department": AsyncMock(), # Keep AsyncMock if/when added
    }

    # --- Configure Mock Return Values ---

    # LIST Departments
    mock_service["get_departments"].return_value = DepartmentsListResponse(
        items=sample_departments_base, total=3, page=1, size=10, pages=1
    )

    # GET Department by ID
    def _mock_get_department(dept_id):
        if dept_id == 1:
            return sample_departments_base[0]
        elif dept_id in [2, 3]:
            # Find by ID in base list
            return next((d for d in sample_departments_base if d.id == dept_id), None)
        return None  # Simulate not found for other IDs

    mock_service["get_department"].side_effect = _mock_get_department

    # CREATE Department
    def _mock_create_department(dept_data: DepartmentCreate):
        new_id = 4  # Simulate next ID
        return DepartmentResponse(id=new_id, **dept_data.model_dump())

    mock_service["create_department"].side_effect = _mock_create_department

    # UPDATE Department
    def _mock_update_department(dept_id: int, dept_data: DepartmentUpdate):
        if dept_id == 1:
            return DepartmentResponse(id=dept_id, **dept_data.model_dump())
        return None  # Simulate not found

    mock_service["update_department"].side_effect = _mock_update_department

    # DELETE Department
    def _mock_delete_department(dept_id: int):
        if dept_id == 3:  # Simulate successful deletion
            return True
        elif dept_id == 1:  # Simulate dependency conflict (core service would raise Exception)
            # The API service catches generic exception and returns False or raises HTTP 409
            # Let's simulate it returning False (or raising 409 - depends on service impl)
            # Based on current service impl, it should raise 409 or return False. Let's say False.
            # OR raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="...")
            return False  # Simulating failure, maybe due to dependencies
        return False  # Simulate not found

    mock_service["delete_department"].side_effect = _mock_delete_department

    # GET Department Professors
    def _mock_get_department_professors(dept_id: int):
        if dept_id == 1:
            profs = [
                p for i, p in enumerate(sample_professors_brief_base) if i < 2
            ]  # First 2 profs
            return DepartmentProfessorsResponse(
                department_id=dept_id, professors=profs, total=len(profs)
            )
        elif dept_id == 2:
            profs = [
                p for i, p in enumerate(sample_professors_brief_base) if i >= 2
            ]  # Last 2 profs
            return DepartmentProfessorsResponse(
                department_id=dept_id, professors=profs, total=len(profs)
            )
        return None  # Simulate department not found

    mock_service["get_department_professors"].side_effect = _mock_get_department_professors

    # GET Department Courses
    def _mock_get_department_courses(dept_id: int):
        if dept_id == 1:
            courses = [
                c for i, c in enumerate(sample_courses_brief_base) if i < 2
            ]  # First 2 courses
            return DepartmentCoursesResponse(
                department_id=dept_id, courses=courses, total=len(courses)
            )
        elif dept_id == 2:
            courses = [
                c for i, c in enumerate(sample_courses_brief_base) if i >= 2
            ]  # Last 2 courses
            return DepartmentCoursesResponse(
                department_id=dept_id, courses=courses, total=len(courses)
            )
        return None  # Simulate department not found

    mock_service["get_department_courses"].side_effect = _mock_get_department_courses

    # GET Department by Code
    def _mock_get_department_by_code(code: str):
        return next((d for d in sample_departments_base if d.code == code), None)

    mock_service["get_department_by_code"].side_effect = _mock_get_department_by_code

    # --- Apply Patches ---
    monkeypatch.setattr(
        "artificial_u.api.services.DepartmentApiService.get_departments",
        mock_service["get_departments"],
    )
    monkeypatch.setattr(
        "artificial_u.api.services.DepartmentApiService.get_department",
        mock_service["get_department"],
    )
    monkeypatch.setattr(
        "artificial_u.api.services.DepartmentApiService.create_department",
        mock_service["create_department"],
    )
    monkeypatch.setattr(
        "artificial_u.api.services.DepartmentApiService.update_department",
        mock_service["update_department"],
    )
    monkeypatch.setattr(
        "artificial_u.api.services.DepartmentApiService.delete_department",
        mock_service["delete_department"],
    )
    monkeypatch.setattr(
        "artificial_u.api.services.DepartmentApiService.get_department_professors",
        mock_service["get_department_professors"],
    )
    monkeypatch.setattr(
        "artificial_u.api.services.DepartmentApiService.get_department_courses",
        mock_service["get_department_courses"],
    )
    monkeypatch.setattr(
        "artificial_u.api.services.DepartmentApiService.get_department_by_code",
        mock_service["get_department_by_code"],
    )
    # Patch generate_department if testing it:
    # monkeypatch.setattr(
    #     "artificial_u.api.services.DepartmentApiService.generate_department",
    #     mock_service["generate_department"], # Assuming it's AsyncMock
    # )

    return mock_service  # Return the dictionary of mocks if needed for assertion


# Removed mock_repository fixture and related imports/logic

# --- Test Cases ---


@pytest.mark.unit
def test_list_departments(client: TestClient, mock_api_service):  # Use mock_api_service
    """Test listing departments endpoint relies on mocked service."""
    response = client.get("/api/v1/departments")
    assert response.status_code == 200
    data = response.json()

    # Assert response structure based on mock return value
    assert "items" in data
    assert data["total"] == len(sample_departments_base)  # Use length of base data used in mock
    assert len(data["items"]) == len(sample_departments_base)
    assert data["items"][0]["name"] == sample_departments_base[0].name

    # Assert that the mocked service method was called correctly
    mock_api_service["get_departments"].assert_called_once_with(
        page=1, size=10, faculty=None, name=None  # Default parameters
    )


@pytest.mark.unit
def test_filter_departments_by_faculty(client: TestClient, mock_api_service):
    """Test filtering departments by faculty (relies on mocked service)."""
    # Configure mock specifically for this faculty filter test case if needed
    faculty_filter = "Test Faculty 1"
    expected_items = [d for d in sample_departments_base if d.faculty == faculty_filter]
    mock_api_service["get_departments"].return_value = DepartmentsListResponse(
        items=expected_items, total=len(expected_items), page=1, size=10, pages=1
    )

    response = client.get(f"/api/v1/departments?faculty={faculty_filter}")
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == len(expected_items)
    assert data["total"] == len(expected_items)
    for item in data["items"]:
        assert item["faculty"] == faculty_filter

    mock_api_service["get_departments"].assert_called_once_with(
        page=1, size=10, faculty=faculty_filter, name=None
    )


@pytest.mark.unit
def test_filter_departments_by_name(client: TestClient, mock_api_service):
    """Test filtering departments by name (relies on mocked service)."""
    name_filter = "Department 1"
    # Simulate service filtering logic in the mock setup
    expected_items = [d for d in sample_departments_base if name_filter in d.name]
    mock_api_service["get_departments"].return_value = DepartmentsListResponse(
        items=expected_items, total=len(expected_items), page=1, size=10, pages=1
    )

    response = client.get(f"/api/v1/departments?name={name_filter}")
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert name_filter in data["items"][0]["name"]

    mock_api_service["get_departments"].assert_called_once_with(
        page=1, size=10, faculty=None, name=name_filter
    )


@pytest.mark.unit
def test_get_department(client: TestClient, mock_api_service):
    """Test getting a single department by ID relies on mocked service."""
    # Test with valid ID (mock returns department 1)
    response = client.get("/api/v1/departments/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == sample_departments_base[0].name
    mock_api_service["get_department"].assert_called_with(1)

    # Test with invalid ID (mock returns None, router raises 404)
    # Reset mock call count if necessary or configure side effect to raise HTTPException
    mock_api_service["get_department"].reset_mock()
    mock_api_service["get_department"].return_value = None  # Ensure mock returns None for 999
    response = client.get("/api/v1/departments/999")
    assert response.status_code == 404
    mock_api_service["get_department"].assert_called_once_with(999)


@pytest.mark.unit
def test_delete_department(client: TestClient, mock_api_service):
    """Test deleting a department relies on mocked service."""
    # Test successful deletion (mock returns True) -> 204 No Content
    mock_api_service["delete_department"].return_value = True
    response_delete_3 = client.delete("/api/v1/departments/3")
    assert response_delete_3.status_code == 204
    mock_api_service["delete_department"].assert_called_with(3)

    # Test deletion conflict (mock returns False, router raises 404 or 409)
    # Assuming router handles 'False' from service as 'Not Found' 404
    # If service raises 409, the TestClient would get 409. Adjust mock accordingly.
    mock_api_service["delete_department"].reset_mock()
    mock_api_service["delete_department"].return_value = (
        False  # Simulate failure (e.g., not found or conflict handled as false return)
    )
    response_delete_1 = client.delete("/api/v1/departments/1")
    # Check the router's behavior based on the service returning False
    # Current router raises 404 if service returns False.
    assert response_delete_1.status_code == 404
    mock_api_service["delete_department"].assert_called_with(1)

    # Test deleting non-existent (mock returns False) -> 404 Not Found
    mock_api_service["delete_department"].reset_mock()
    mock_api_service["delete_department"].return_value = False
    response_delete_999 = client.delete("/api/v1/departments/999")
    assert response_delete_999.status_code == 404
    mock_api_service["delete_department"].assert_called_with(999)


@pytest.mark.unit
def test_create_department(client: TestClient, mock_api_service):
    """Test creating a new department relies on mocked service."""
    new_department_data = {
        "name": "New Department",
        "code": "ND1",
        "faculty": "New Faculty",
        "description": "A brand new department",
    }
    # Mock configured to return ID 4
    expected_response_data = {"id": 4, **new_department_data}

    response = client.post("/api/v1/departments", json=new_department_data)

    assert response.status_code == 201
    assert response.json() == expected_response_data

    # Assert the mock was called with the correct Pydantic model instance
    mock_api_service["create_department"].assert_called_once()
    call_args = mock_api_service["create_department"].call_args[0]
    assert isinstance(call_args[0], DepartmentCreate)
    assert call_args[0].model_dump() == new_department_data


@pytest.mark.unit
def test_update_department(client: TestClient, mock_api_service):
    """Test updating an existing department relies on mocked service."""
    update_data = {
        "name": "Updated Department",
        "code": "UD1",
        "faculty": "Updated Faculty",
        "description": "An updated department description",
    }
    # Mock configured to return updated data for ID 1
    expected_response_data = {"id": 1, **update_data}

    # Test with valid ID
    response = client.put("/api/v1/departments/1", json=update_data)
    assert response.status_code == 200
    assert response.json() == expected_response_data
    # Assert mock call
    mock_api_service["update_department"].assert_called_once()
    call_args, call_kwargs = mock_api_service["update_department"].call_args
    assert call_args[0] == 1  # department_id
    assert isinstance(call_args[1], DepartmentUpdate)
    assert call_args[1].model_dump() == update_data

    # Test with invalid ID (mock returns None, router raises 404)
    mock_api_service["update_department"].reset_mock()
    mock_api_service["update_department"].return_value = None
    response = client.put("/api/v1/departments/999", json=update_data)
    assert response.status_code == 404
    mock_api_service["update_department"].assert_called_once()  # Check it was called


@pytest.mark.unit
def test_get_department_professors(client: TestClient, mock_api_service):
    """Test getting professors in a department relies on mocked service."""
    # Test with valid ID for Dept 1 (mock returns first 2 profs)
    response = client.get("/api/v1/departments/1/professors")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 1
    assert "professors" in data
    assert len(data["professors"]) == 2  # Based on mock setup
    assert data["total"] == 2
    assert data["professors"][0]["name"] == sample_professors_brief_base[0].name
    mock_api_service["get_department_professors"].assert_called_with(1)

    # Test with valid ID for Dept 2 (mock returns last 2 profs)
    mock_api_service["get_department_professors"].reset_mock()
    response = client.get("/api/v1/departments/2/professors")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 2
    assert len(data["professors"]) == 2  # Based on mock setup
    assert data["total"] == 2
    mock_api_service["get_department_professors"].assert_called_with(2)

    # Test with invalid ID (mock returns None, router raises 404)
    mock_api_service["get_department_professors"].reset_mock()
    mock_api_service["get_department_professors"].return_value = None
    response = client.get("/api/v1/departments/999/professors")
    assert response.status_code == 404
    mock_api_service["get_department_professors"].assert_called_with(999)


@pytest.mark.unit
def test_get_department_courses(client: TestClient, mock_api_service):
    """Test getting courses in a department relies on mocked service."""
    # Test with valid ID for Dept 1 (mock returns first 2 courses)
    response = client.get("/api/v1/departments/1/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 1
    assert "courses" in data
    assert len(data["courses"]) == 2  # Based on mock setup
    assert data["total"] == 2
    assert data["courses"][0]["code"] == sample_courses_brief_base[0].code
    mock_api_service["get_department_courses"].assert_called_with(1)

    # Test with valid ID for Dept 2 (mock returns last 2 courses)
    mock_api_service["get_department_courses"].reset_mock()
    response = client.get("/api/v1/departments/2/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["department_id"] == 2
    assert len(data["courses"]) == 2  # Based on mock setup
    assert data["total"] == 2
    mock_api_service["get_department_courses"].assert_called_with(2)

    # Test with invalid ID (mock returns None, router raises 404)
    mock_api_service["get_department_courses"].reset_mock()
    mock_api_service["get_department_courses"].return_value = None
    response = client.get("/api/v1/departments/999/courses")
    assert response.status_code == 404
    mock_api_service["get_department_courses"].assert_called_with(999)


@pytest.mark.unit
def test_get_department_by_code(client: TestClient, mock_api_service):
    """Test getting department by code relies on mocked service."""
    # Test with valid code
    target_code = "TD1"
    expected_dept = sample_departments_base[0]
    mock_api_service["get_department_by_code"].return_value = expected_dept

    response = client.get(f"/api/v1/departments/code/{target_code}")
    assert response.status_code == 200
    assert response.json()["code"] == target_code
    assert response.json()["id"] == expected_dept.id
    mock_api_service["get_department_by_code"].assert_called_once_with(target_code)

    # Test with invalid code
    mock_api_service["get_department_by_code"].reset_mock()
    mock_api_service["get_department_by_code"].return_value = None
    response = client.get("/api/v1/departments/code/INVALID")
    assert response.status_code == 404
    mock_api_service["get_department_by_code"].assert_called_once_with("INVALID")


# Note: Tests for the duplicate /professors and /courses endpoints defined later in the router
# (list_department_professors, list_department_courses) are implicitly covered by
# test_get_department_professors and test_get_department_courses if they rely on the
# same service methods. If they use different service methods or have different response
# models (e.g., ProfessorsListResponse vs DepartmentProfessorsResponse), separate tests
# mocking the relevant service calls would be needed.

# Test for generate endpoint would go here, mocking the generate_department service method.
