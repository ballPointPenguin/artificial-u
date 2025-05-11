"""
Unit Tests for the course API endpoints, mocking the service layer.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

# Import relevant API models for courses
from artificial_u.api.models import CourseCreate  # Request model
from artificial_u.api.models import (
    CourseDepartmentBrief,  # Needed for CourseDepartmentBrief response simulation
)
from artificial_u.api.models import CourseLectureBrief  # Needed for CourseLecturesResponse
from artificial_u.api.models import (
    CourseProfessorBrief,  # Needed for CourseProfessorBrief response simulation
)
from artificial_u.api.models import CourseUpdate  # Request model
from artificial_u.api.models import (
    CourseGenerate,
    CourseLecturesResponse,
    CourseResponse,
    CoursesListResponse,
)

# Base data for mocking responses
sample_courses_base = [
    CourseResponse(
        id=i,
        code=f"COURSE{i}01",
        title=f"Test Course {i}",
        department_id=1 if i < 3 else 2,
        level="Undergraduate",
        credits=3,
        professor_id=i,
        description=f"Description {i}",
        lectures_per_week=2,
        total_weeks=14,
    )
    for i in range(1, 5)
]

sample_professor_brief_base = CourseProfessorBrief(
    id=1, name="Dr. Test Professor 1", title="Professor", specialization="Testing", department_id=1
)

sample_department_brief_base = CourseDepartmentBrief(
    id=1, name="Test Department 1", code="TD1", faculty="Test Faculty"
)

sample_lectures_brief_base = [
    CourseLectureBrief(
        id=j, title=f"Lecture {j}", week_number=j, order_in_week=1, description=f"Description {j}"
    )
    for j in range(1, 4)
]


@pytest.fixture
def mock_api_service(monkeypatch):
    """Mock the CourseApiService methods for unit testing the API router."""
    mock_service = {
        "get_courses": MagicMock(),
        "get_course": MagicMock(),
        "get_course_by_code": MagicMock(),
        "create_course": MagicMock(),
        "update_course": MagicMock(),
        "delete_course": MagicMock(),
        "get_course_professor": MagicMock(),
        "get_course_department": MagicMock(),
        "get_course_lectures": MagicMock(),
        "generate_course": AsyncMock(),
    }

    # --- Configure Mock Return Values ---

    # LIST Courses (Default: all)
    mock_service["get_courses"].return_value = CoursesListResponse(
        items=sample_courses_base, total=4, page=1, size=10, pages=1
    )

    # GET Course by ID
    def _mock_get_course(course_id):
        return next((c for c in sample_courses_base if c.id == course_id), None)

    mock_service["get_course"].side_effect = _mock_get_course

    # GET Course by Code
    def _mock_get_course_by_code(code):
        return next((c for c in sample_courses_base if c.code == code), None)

    mock_service["get_course_by_code"].side_effect = _mock_get_course_by_code

    # CREATE Course
    def _mock_create_course(course_data: CourseCreate):
        new_id = 5  # Simulate next ID
        # Simulate successful creation, return data resembling a saved course
        return CourseResponse(id=new_id, **course_data.model_dump())

    mock_service["create_course"].side_effect = _mock_create_course

    # UPDATE Course
    def _mock_update_course(course_id: int, course_data: CourseUpdate):
        if course_id in [c.id for c in sample_courses_base]:
            # Simulate successful update, return updated data
            # Fetch original to merge update
            original_course = next(c for c in sample_courses_base if c.id == course_id)
            updated_data = original_course.model_dump()
            updated_data.update(course_data.model_dump(exclude_unset=True))
            return CourseResponse(**updated_data)
        return None  # Simulate course not found

    mock_service["update_course"].side_effect = _mock_update_course

    # DELETE Course
    # Service returns bool (True if deleted, False if not found/error occurred before delete)
    # Router translates False to 404. Service raises HTTPException for 409/500.
    def _mock_delete_course(course_id: int):
        if course_id in [c.id for c in sample_courses_base]:  # Simulate finding it
            # Assume deletion is successful if found for this mock
            # To test 409, the service mock would need to raise HTTPException
            return True
        return False  # Simulate not found

    mock_service["delete_course"].side_effect = _mock_delete_course

    # GET Course Professor
    def _mock_get_course_professor(course_id: int):
        # Return the base ProfessorBrief, router expects CourseProfessorBrief
        # But structure is compatible for this test
        if course_id == 1:
            return sample_professor_brief_base
        return None  # Simulate course or professor not found

    mock_service["get_course_professor"].side_effect = _mock_get_course_professor

    # GET Course Department
    def _mock_get_course_department(course_id: int):
        # Return the base DepartmentBrief, router expects CourseDepartmentBrief
        # But structure is compatible for this test
        if course_id == 1:
            return sample_department_brief_base
        return None  # Simulate course or department not found

    mock_service["get_course_department"].side_effect = _mock_get_course_department

    # GET Course Lectures
    def _mock_get_course_lectures(course_id: int):
        if course_id == 1:
            return CourseLecturesResponse(
                course_id=1,
                lectures=sample_lectures_brief_base,
                total=len(sample_lectures_brief_base),
            )
        return None  # Simulate course not found

    mock_service["get_course_lectures"].side_effect = _mock_get_course_lectures

    # GENERATE Course
    mock_service["generate_course"].return_value = sample_courses_base[
        0
    ]  # Return a sample generated course

    # --- Apply Patches ---
    base_path = "artificial_u.api.services.CourseApiService"
    monkeypatch.setattr(f"{base_path}.get_courses", mock_service["get_courses"])
    monkeypatch.setattr(f"{base_path}.get_course", mock_service["get_course"])
    monkeypatch.setattr(f"{base_path}.get_course_by_code", mock_service["get_course_by_code"])
    monkeypatch.setattr(f"{base_path}.create_course", mock_service["create_course"])
    monkeypatch.setattr(f"{base_path}.update_course", mock_service["update_course"])
    monkeypatch.setattr(f"{base_path}.delete_course", mock_service["delete_course"])
    monkeypatch.setattr(f"{base_path}.get_course_professor", mock_service["get_course_professor"])
    monkeypatch.setattr(f"{base_path}.get_course_department", mock_service["get_course_department"])
    monkeypatch.setattr(f"{base_path}.get_course_lectures", mock_service["get_course_lectures"])
    monkeypatch.setattr(f"{base_path}.generate_course", mock_service["generate_course"])

    return mock_service


# Test functions will go here

# --- Test Cases ---


@pytest.mark.unit
def test_list_courses(client: TestClient, mock_api_service):
    """Test listing courses endpoint relies on mocked service."""
    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == len(sample_courses_base)
    assert len(data["items"]) == len(sample_courses_base)
    assert data["items"][0]["code"] == sample_courses_base[0].code
    mock_api_service["get_courses"].assert_called_once_with(
        page=1, size=10, department_id=None, professor_id=None, level=None, title=None
    )


@pytest.mark.unit
def test_list_courses_with_filters(client: TestClient, mock_api_service):
    """Test listing courses with various filters."""
    # Simulate filtered response from service
    filtered_courses = [c for c in sample_courses_base if c.department_id == 1]
    mock_api_service["get_courses"].return_value = CoursesListResponse(
        items=filtered_courses, total=len(filtered_courses), page=1, size=10, pages=1
    )

    response = client.get("/api/v1/courses?department_id=1&level=Undergraduate")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == len(filtered_courses)
    assert data["total"] == len(filtered_courses)
    mock_api_service["get_courses"].assert_called_once_with(
        page=1, size=10, department_id=1, professor_id=None, level="Undergraduate", title=None
    )


@pytest.mark.unit
def test_get_course(client: TestClient, mock_api_service):
    """Test getting a single course by ID."""
    # Test valid ID
    response = client.get("/api/v1/courses/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["code"] == sample_courses_base[0].code
    mock_api_service["get_course"].assert_called_once_with(1)

    # Test invalid ID
    mock_api_service["get_course"].reset_mock()
    mock_api_service["get_course"].return_value = None
    response = client.get("/api/v1/courses/999")
    assert response.status_code == 404  # Router should raise 404
    mock_api_service["get_course"].assert_called_once_with(999)


@pytest.mark.unit
def test_get_course_by_code(client: TestClient, mock_api_service):
    """Test getting a single course by code."""
    target_code = sample_courses_base[1].code  # COURSE201
    # Test valid code
    response = client.get(f"/api/v1/courses/code/{target_code}")
    assert response.status_code == 200
    assert response.json()["code"] == target_code
    assert response.json()["id"] == sample_courses_base[1].id
    mock_api_service["get_course_by_code"].assert_called_once_with(target_code)

    # Test invalid code
    mock_api_service["get_course_by_code"].reset_mock()
    mock_api_service["get_course_by_code"].return_value = None
    response = client.get("/api/v1/courses/code/INVALID99")
    assert response.status_code == 404
    mock_api_service["get_course_by_code"].assert_called_once_with("INVALID99")


@pytest.mark.unit
def test_create_course(client: TestClient, mock_api_service):
    """Test creating a new course."""
    new_course_data = {
        "code": "NEW101",
        "title": "Newly Created Course",
        "department_id": 1,
        "level": "Graduate",
        "credits": 4,
        "professor_id": 2,
        "description": "A course created via API test",
        "lectures_per_week": 1,
        "total_weeks": 10,
        "topics": [],
    }
    # Mock configured to return ID 5
    expected_response_data = {"id": 5, **new_course_data}

    response = client.post("/api/v1/courses", json=new_course_data)
    assert response.status_code == 201
    assert response.json() == expected_response_data

    mock_api_service["create_course"].assert_called_once()
    call_args = mock_api_service["create_course"].call_args[0]
    assert isinstance(call_args[0], CourseCreate)
    assert call_args[0].model_dump() == new_course_data


@pytest.mark.unit
def test_update_course(client: TestClient, mock_api_service):
    """Test updating an existing course."""
    update_data = {"title": "Updated Course Title", "credits": 5}
    course_id_to_update = 2
    # Mock configured to return updated data for ID 2
    # We need the original data to merge with the update for the expected response
    original_data = next(c for c in sample_courses_base if c.id == course_id_to_update)
    expected_data = original_data.model_dump()
    expected_data.update(update_data)

    response = client.put(f"/api/v1/courses/{course_id_to_update}", json=update_data)
    assert response.status_code == 200
    # The mock needs to correctly merge and return a CourseResponse
    assert response.json() == CourseResponse(**expected_data).model_dump()

    mock_api_service["update_course"].assert_called_once()
    call_args, call_kwargs = mock_api_service["update_course"].call_args
    assert call_args[0] == course_id_to_update
    assert isinstance(call_args[1], CourseUpdate)
    assert call_args[1].model_dump(exclude_unset=True) == update_data

    # Test invalid ID
    mock_api_service["update_course"].reset_mock()
    mock_api_service["update_course"].return_value = None
    response = client.put("/api/v1/courses/999", json=update_data)
    assert response.status_code == 404
    mock_api_service["update_course"].assert_called_once()


@pytest.mark.unit
def test_delete_course(client: TestClient, mock_api_service):
    """Test deleting a course."""
    course_id_to_delete = 3

    # Test successful deletion
    response = client.delete(f"/api/v1/courses/{course_id_to_delete}")
    assert response.status_code == 204
    mock_api_service["delete_course"].assert_called_once_with(course_id_to_delete)

    # Test deleting non-existent course
    mock_api_service["delete_course"].reset_mock()
    mock_api_service["delete_course"].return_value = (
        False  # Mock service returns False for not found
    )
    response = client.delete("/api/v1/courses/999")
    assert response.status_code == 404  # Router converts False to 404
    mock_api_service["delete_course"].assert_called_once_with(999)


@pytest.mark.unit
def test_get_course_professor(client: TestClient, mock_api_service):
    """Test getting the professor for a course."""
    # Test valid ID (Course 1)
    response = client.get("/api/v1/courses/1/professor")
    assert response.status_code == 200
    # The router expects CourseProfessorBrief, but mock returns ProfessorBrief.
    # We assert against the data structure we expect the mock to return.
    assert response.json() == sample_professor_brief_base.model_dump()
    mock_api_service["get_course_professor"].assert_called_once_with(1)

    # Test invalid course ID
    mock_api_service["get_course_professor"].reset_mock()
    mock_api_service["get_course_professor"].return_value = None
    response = client.get("/api/v1/courses/999/professor")
    assert response.status_code == 404
    mock_api_service["get_course_professor"].assert_called_once_with(999)


@pytest.mark.unit
def test_get_course_department(client: TestClient, mock_api_service):
    """Test getting the department for a course."""
    # Test valid ID (Course 1)
    response = client.get("/api/v1/courses/1/department")
    assert response.status_code == 200
    # The router expects CourseDepartmentBrief, but mock returns DepartmentBrief.
    # Assert against the data structure we expect the mock to return.
    assert response.json() == sample_department_brief_base.model_dump()
    mock_api_service["get_course_department"].assert_called_once_with(1)

    # Test invalid course ID
    mock_api_service["get_course_department"].reset_mock()
    mock_api_service["get_course_department"].return_value = None
    response = client.get("/api/v1/courses/999/department")
    assert response.status_code == 404
    mock_api_service["get_course_department"].assert_called_once_with(999)


@pytest.mark.unit
def test_get_course_lectures(client: TestClient, mock_api_service):
    """Test getting the lectures for a course."""
    # Test valid ID (Course 1)
    response = client.get("/api/v1/courses/1/lectures")
    assert response.status_code == 200
    data = response.json()
    assert data["course_id"] == 1
    assert len(data["lectures"]) == len(sample_lectures_brief_base)
    assert data["total"] == len(sample_lectures_brief_base)
    assert data["lectures"][0]["title"] == sample_lectures_brief_base[0].title
    mock_api_service["get_course_lectures"].assert_called_once_with(1)

    # Test invalid course ID
    mock_api_service["get_course_lectures"].reset_mock()
    mock_api_service["get_course_lectures"].return_value = None
    response = client.get("/api/v1/courses/999/lectures")
    assert response.status_code == 404
    mock_api_service["get_course_lectures"].assert_called_once_with(999)


@pytest.mark.unit
def test_generate_course_partial_data(client: TestClient, mock_api_service: MagicMock):
    """Test generating course data where the AI might return partial information."""
    generation_request_data = {
        "partial_attributes": {"title": "AI Generated Course"},
        "freeform_prompt": "Make it introductory and about astrophysics.",
    }

    # Mock service to return partial data that is valid for GeneratedCourseData
    mock_partial_response_dict = {
        "id": -1,
        "title": "AI Generated Course",
        "code": "ASTRO100",
        "description": "An introductory course about astrophysics, generated by AI.",
        "level": "Introductory",
        # department_id and professor_id are intentionally missing
        # Other optional fields like credits, topics, etc., are also missing
    }
    # The service method is async, so the mock should be an AsyncMock returning the dict
    # The mock_api_service fixture already makes generate_course an AsyncMock
    mock_api_service["generate_course"].return_value = mock_partial_response_dict

    response = client.post("/api/v1/courses/generate", json=generation_request_data)
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == -1
    assert data["title"] == "AI Generated Course"
    assert data["code"] == "ASTRO100"
    assert data["level"] == "Introductory"
    assert data["description"] == "An introductory course about astrophysics, generated by AI."
    assert data["department_id"] is None  # Assert that fields can be missing or None
    assert data["professor_id"] is None
    assert data["credits"] is None  # Check another optional field

    mock_api_service["generate_course"].assert_called_once()
    # Check the arguments passed to the service method
    called_with_arg = mock_api_service["generate_course"].call_args[0][0]
    assert isinstance(called_with_arg, CourseGenerate)
    assert called_with_arg.partial_attributes == generation_request_data["partial_attributes"]
    assert called_with_arg.freeform_prompt == generation_request_data["freeform_prompt"]
