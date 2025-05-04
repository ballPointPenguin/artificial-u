"""
Unit Tests for the professor API endpoints, mocking the service layer.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.models.professors import (
    CourseBrief,
    LectureBrief,
    ProfessorCoursesResponse,
    ProfessorCreate,
    ProfessorGenerate,
    ProfessorLecturesResponse,
    ProfessorResponse,
    ProfessorsListResponse,
    ProfessorUpdate,
)

# Base data for mocking responses
sample_professors_base = [
    ProfessorResponse(
        id=i,
        name=f"Dr. Test Professor {i}",
        title=f"Professor of Test {i}",
        department_id=1 if i < 3 else 2,
        specialization=f"Test Specialization {i}",
        background=f"Academic background {i}",
        personality=f"Engaging and enthusiastic {i}",
        teaching_style=f"Interactive and hands-on {i}",
        gender="non-binary",
        accent="neutral",
        description=f"Description for professor {i}",
        age=40 + i,
        image_url=f"https://example.com/professors/{i}.jpg" if i % 2 == 0 else None,
        voice_id=i if i % 2 == 0 else None,
    )
    for i in range(1, 5)
]

sample_courses_brief_base = [
    CourseBrief(
        id=i,
        code=f"TEST{i}01",
        title=f"Test Course {i}",
        department_id=1,
        level="Undergraduate",
        credits=3,
    )
    for i in range(1, 4)
]

sample_lectures_brief_base = [
    LectureBrief(
        id=i,
        title=f"Test Lecture {i}",
        course_id=1,
        week_number=i,
        order_in_week=1,
        description=f"Description for lecture {i}",
    )
    for i in range(1, 4)
]


@pytest.fixture
def mock_api_service(monkeypatch):
    """Mock the ProfessorApiService methods for unit testing the API router."""
    mock_service = {
        "get_professors": AsyncMock(),
        "get_professor": AsyncMock(),
        "create_professor": AsyncMock(),
        "update_professor": AsyncMock(),
        "delete_professor": AsyncMock(),
        "get_professor_courses": AsyncMock(),
        "get_professor_lectures": AsyncMock(),
        "generate_professor_image": AsyncMock(),
        "generate_professor": AsyncMock(),
    }

    # --- Configure Mock Return Values ---

    # LIST Professors
    mock_service["get_professors"].return_value = ProfessorsListResponse(
        items=sample_professors_base, total=4, page=1, size=10, pages=1
    )

    # GET Professor by ID
    def _mock_get_professor(professor_id):
        return next((p for p in sample_professors_base if p.id == professor_id), None)

    mock_service["get_professor"].side_effect = _mock_get_professor

    # CREATE Professor
    def _mock_create_professor(professor_data: ProfessorCreate):
        new_id = 5  # Simulate next ID
        return ProfessorResponse(id=new_id, **professor_data.model_dump())

    mock_service["create_professor"].side_effect = _mock_create_professor

    # UPDATE Professor
    def _mock_update_professor(professor_id: int, professor_data: ProfessorUpdate):
        if professor_id in [p.id for p in sample_professors_base]:
            original_professor = next(p for p in sample_professors_base if p.id == professor_id)
            updated_data = original_professor.model_dump()
            updated_data.update(professor_data.model_dump(exclude_unset=True))
            return ProfessorResponse(**updated_data)
        return None

    mock_service["update_professor"].side_effect = _mock_update_professor

    # DELETE Professor
    def _mock_delete_professor(professor_id: int):
        return professor_id in [p.id for p in sample_professors_base]

    mock_service["delete_professor"].side_effect = _mock_delete_professor

    # GET Professor Courses
    def _mock_get_professor_courses(professor_id: int):
        if professor_id in [p.id for p in sample_professors_base]:
            return ProfessorCoursesResponse(
                professor_id=professor_id,
                courses=sample_courses_brief_base,
                total=len(sample_courses_brief_base),
            )
        return None

    mock_service["get_professor_courses"].side_effect = _mock_get_professor_courses

    # GET Professor Lectures
    def _mock_get_professor_lectures(professor_id: int):
        if professor_id in [p.id for p in sample_professors_base]:
            return ProfessorLecturesResponse(
                professor_id=professor_id,
                lectures=sample_lectures_brief_base,
                total=len(sample_lectures_brief_base),
            )
        return None

    mock_service["get_professor_lectures"].side_effect = _mock_get_professor_lectures

    # GENERATE Professor Image
    def _mock_generate_professor_image(professor_id: int):
        if professor_id in [p.id for p in sample_professors_base]:
            professor = next(p for p in sample_professors_base if p.id == professor_id)
            updated_data = professor.model_dump()
            updated_data["image_url"] = f"https://example.com/professors/{professor_id}_new.jpg"
            return ProfessorResponse(**updated_data)
        return None

    mock_service["generate_professor_image"].side_effect = _mock_generate_professor_image

    # GENERATE Professor
    mock_service["generate_professor"].return_value = sample_professors_base[0]

    # --- Apply Patches ---
    base_path = "artificial_u.api.services.ProfessorApiService"
    monkeypatch.setattr(f"{base_path}.get_professors", mock_service["get_professors"])
    monkeypatch.setattr(f"{base_path}.get_professor", mock_service["get_professor"])
    monkeypatch.setattr(f"{base_path}.create_professor", mock_service["create_professor"])
    monkeypatch.setattr(f"{base_path}.update_professor", mock_service["update_professor"])
    monkeypatch.setattr(f"{base_path}.delete_professor", mock_service["delete_professor"])
    monkeypatch.setattr(f"{base_path}.get_professor_courses", mock_service["get_professor_courses"])
    monkeypatch.setattr(
        f"{base_path}.get_professor_lectures", mock_service["get_professor_lectures"]
    )
    monkeypatch.setattr(
        f"{base_path}.generate_professor_image", mock_service["generate_professor_image"]
    )
    monkeypatch.setattr(f"{base_path}.generate_professor", mock_service["generate_professor"])

    return mock_service


# --- Test Cases ---


@pytest.mark.unit
def test_list_professors(client: TestClient, mock_api_service):
    """Test listing professors endpoint relies on mocked service."""
    response = client.get("/api/v1/professors")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert data["total"] == len(sample_professors_base)
    assert len(data["items"]) == len(sample_professors_base)
    assert data["items"][0]["name"] == sample_professors_base[0].name

    mock_api_service["get_professors"].assert_called_once_with(
        page=1, size=10, department_id=None, name=None, specialization=None
    )


@pytest.mark.unit
def test_list_professors_with_filters(client: TestClient, mock_api_service):
    """Test listing professors with various filters."""
    filtered_professors = [p for p in sample_professors_base if p.department_id == 1]
    mock_api_service["get_professors"].return_value = ProfessorsListResponse(
        items=filtered_professors, total=len(filtered_professors), page=1, size=10, pages=1
    )

    response = client.get("/api/v1/professors?department_id=1&name=Test")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == len(filtered_professors)
    assert data["total"] == len(filtered_professors)

    mock_api_service["get_professors"].assert_called_once_with(
        page=1, size=10, department_id=1, name="Test", specialization=None
    )


@pytest.mark.unit
def test_get_professor(client: TestClient, mock_api_service):
    """Test getting a single professor by ID."""
    # Test valid ID
    response = client.get("/api/v1/professors/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == sample_professors_base[0].name
    mock_api_service["get_professor"].assert_called_once_with(1)

    # Test invalid ID
    mock_api_service["get_professor"].reset_mock()
    mock_api_service["get_professor"].return_value = None
    response = client.get("/api/v1/professors/999")
    assert response.status_code == 404
    mock_api_service["get_professor"].assert_called_once_with(999)


@pytest.mark.unit
def test_create_professor(client: TestClient, mock_api_service):
    """Test creating a new professor."""
    new_professor_data = {
        "name": "Dr. New Professor",
        "title": "Professor of Testing",
        "department_id": 1,
        "specialization": "Test Creation",
        "background": "Extensive testing background",
        "personality": "Detail-oriented",
        "teaching_style": "Test-driven",
        "gender": "non-binary",
        "accent": "neutral",
        "description": "A new test professor",
        "age": 45,
        "image_url": None,
        "voice_id": None,
    }
    expected_response_data = {"id": 5, "image_url": None, "voice_id": None, **new_professor_data}

    response = client.post("/api/v1/professors", json=new_professor_data)
    assert response.status_code == 201
    assert response.json() == expected_response_data

    mock_api_service["create_professor"].assert_called_once()
    call_args = mock_api_service["create_professor"].call_args[0]
    assert isinstance(call_args[0], ProfessorCreate)
    assert call_args[0].model_dump() == new_professor_data


@pytest.mark.unit
def test_update_professor(client: TestClient, mock_api_service):
    """Test updating an existing professor."""
    update_data = {"title": "Updated Professor Title", "specialization": "Updated Specialization"}
    professor_id_to_update = 2

    response = client.put(f"/api/v1/professors/{professor_id_to_update}", json=update_data)
    assert response.status_code == 200
    assert response.json()["title"] == update_data["title"]
    assert response.json()["specialization"] == update_data["specialization"]

    mock_api_service["update_professor"].assert_called_once()
    call_args = mock_api_service["update_professor"].call_args[0]
    assert call_args[0] == professor_id_to_update
    assert isinstance(call_args[1], ProfessorUpdate)
    assert call_args[1].model_dump(exclude_unset=True) == update_data

    # Test invalid ID
    mock_api_service["update_professor"].reset_mock()
    mock_api_service["update_professor"].return_value = None
    response = client.put("/api/v1/professors/999", json=update_data)
    assert response.status_code == 404
    mock_api_service["update_professor"].assert_called_once()


@pytest.mark.unit
def test_delete_professor(client: TestClient, mock_api_service):
    """Test deleting a professor."""
    # Test successful deletion
    response = client.delete("/api/v1/professors/3")
    assert response.status_code == 204
    mock_api_service["delete_professor"].assert_called_once_with(3)

    # Test deleting non-existent professor
    mock_api_service["delete_professor"].reset_mock()
    mock_api_service["delete_professor"].return_value = False
    response = client.delete("/api/v1/professors/999")
    assert response.status_code == 404
    mock_api_service["delete_professor"].assert_called_once_with(999)


@pytest.mark.unit
def test_get_professor_courses(client: TestClient, mock_api_service):
    """Test getting courses for a professor."""
    # Test valid ID
    response = client.get("/api/v1/professors/1/courses")
    assert response.status_code == 200
    data = response.json()
    assert data["professor_id"] == 1
    assert len(data["courses"]) == len(sample_courses_brief_base)
    assert data["total"] == len(sample_courses_brief_base)
    assert data["courses"][0]["code"] == sample_courses_brief_base[0].code
    mock_api_service["get_professor_courses"].assert_called_once_with(1)

    # Test invalid ID
    mock_api_service["get_professor_courses"].reset_mock()
    mock_api_service["get_professor_courses"].return_value = None
    response = client.get("/api/v1/professors/999/courses")
    assert response.status_code == 404
    mock_api_service["get_professor_courses"].assert_called_once_with(999)


@pytest.mark.unit
def test_get_professor_lectures(client: TestClient, mock_api_service):
    """Test getting lectures for a professor."""
    # Test valid ID
    response = client.get("/api/v1/professors/1/lectures")
    assert response.status_code == 200
    data = response.json()
    assert data["professor_id"] == 1
    assert len(data["lectures"]) == len(sample_lectures_brief_base)
    assert data["total"] == len(sample_lectures_brief_base)
    assert data["lectures"][0]["title"] == sample_lectures_brief_base[0].title
    mock_api_service["get_professor_lectures"].assert_called_once_with(1)

    # Test invalid ID
    mock_api_service["get_professor_lectures"].reset_mock()
    mock_api_service["get_professor_lectures"].return_value = None
    response = client.get("/api/v1/professors/999/lectures")
    assert response.status_code == 404
    mock_api_service["get_professor_lectures"].assert_called_once_with(999)


@pytest.mark.unit
def test_generate_professor_image(client: TestClient, mock_api_service):
    """Test generating an image for a professor."""
    # Test successful generation
    response = client.post("/api/v1/professors/2/generate-image")
    assert response.status_code == 200
    assert "image_url" in response.json()
    assert response.json()["image_url"].endswith("_new.jpg")
    mock_api_service["generate_professor_image"].assert_called_once_with(2)

    # Test generation for non-existent professor
    mock_api_service["generate_professor_image"].reset_mock()
    mock_api_service["generate_professor_image"].return_value = None
    mock_api_service["get_professor"].return_value = None  # For 404 check
    response = client.post("/api/v1/professors/999/generate-image")
    assert response.status_code == 404
    mock_api_service["generate_professor_image"].assert_called_once_with(999)


@pytest.mark.unit
def test_generate_professor(client: TestClient, mock_api_service):
    """Test generating professor data using AI."""
    generation_data = {
        "partial_attributes": {"department_id": 1, "specialization": "Testing"},
        "freeform_prompt": "Generate a professor specializing in software testing",
    }

    response = client.post("/api/v1/professors/generate", json=generation_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert "name" in response.json()
    assert "specialization" in response.json()

    mock_api_service["generate_professor"].assert_called_once()
    call_args = mock_api_service["generate_professor"].call_args[0]
    assert isinstance(call_args[0], ProfessorGenerate)
    assert call_args[0].model_dump() == generation_data
