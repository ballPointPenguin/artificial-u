"""
Unit Tests for the lecture API endpoints, mocking the service layer.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.models.lectures import (
    Lecture,
    LectureCreate,
    LectureGenerate,
    LectureList,
    LectureUpdate,
)

# Base data for mocking responses
sample_lectures_base = [
    Lecture(
        id=i,
        course_id=1 if i < 3 else 2,
        topic_id=i * 10,
        revision=1,
        content=f"Full content for lecture {i}",
        summary=f"Summary for lecture {i}",
        audio_url=f"https://example.com/audio/lecture_{i}.mp3" if i % 2 == 0 else None,
        transcript_url=f"https://example.com/transcript/lecture_{i}.txt" if i % 3 == 0 else None,
    )
    for i in range(1, 5)
]


@pytest.fixture
def mock_api_service(monkeypatch):
    """Mock the LectureApiService methods for unit testing the API router."""
    mock_service = {
        "list_lectures": MagicMock(),
        "get_lecture": MagicMock(),
        "create_lecture": MagicMock(),
        "update_lecture": MagicMock(),
        "delete_lecture": MagicMock(),
        "get_lecture_content": MagicMock(),
        "get_lecture_audio_url": MagicMock(),
        "generate_lecture": AsyncMock(),
    }

    # --- Configure Mock Return Values ---

    # LIST Lectures
    mock_service["list_lectures"].return_value = LectureList(
        items=sample_lectures_base, total=4, page=1, page_size=10
    )

    # GET Lecture by ID
    def _mock_get_lecture(lecture_id):
        return next((lecture for lecture in sample_lectures_base if lecture.id == lecture_id), None)

    mock_service["get_lecture"].side_effect = _mock_get_lecture

    # CREATE Lecture
    def _mock_create_lecture(lecture_data: LectureCreate):
        new_id = 5  # Simulate next ID
        return Lecture(
            id=new_id,
            course_id=lecture_data.course_id,
            topic_id=lecture_data.topic_id,
            revision=lecture_data.revision if lecture_data.revision is not None else 1,
            content=lecture_data.content,
            summary=lecture_data.summary,
            audio_url=lecture_data.audio_url,
            transcript_url=lecture_data.transcript_url,
        )

    mock_service["create_lecture"].side_effect = _mock_create_lecture

    # UPDATE Lecture
    def _mock_update_lecture(lecture_id: int, lecture_data: LectureUpdate):
        if lecture_id in [lecture.id for lecture in sample_lectures_base]:
            original_lecture = next(
                lecture for lecture in sample_lectures_base if lecture.id == lecture_id
            )
            updated_data = original_lecture.model_dump()
            update_payload = lecture_data.model_dump(exclude_unset=True)
            updated_data.update(update_payload)
            return Lecture(**updated_data)
        return None

    mock_service["update_lecture"].side_effect = _mock_update_lecture

    # DELETE Lecture
    def _mock_delete_lecture(lecture_id: int):
        return lecture_id in [lecture.id for lecture in sample_lectures_base]

    mock_service["delete_lecture"].side_effect = _mock_delete_lecture

    # GET Lecture Content
    def _mock_get_lecture_content(lecture_id: int):
        lecture = next(
            (lecture for lecture in sample_lectures_base if lecture.id == lecture_id), None
        )
        return lecture.content if lecture else None

    mock_service["get_lecture_content"].side_effect = _mock_get_lecture_content

    # GET Lecture Audio URL
    def _mock_get_lecture_audio_url(lecture_id: int):
        lecture = next(
            (lecture for lecture in sample_lectures_base if lecture.id == lecture_id), None
        )
        return lecture.audio_url if lecture else None

    mock_service["get_lecture_audio_url"].side_effect = _mock_get_lecture_audio_url

    # GENERATE Lecture
    generated_lecture_mock = Lecture(
        id=sample_lectures_base[0].id,
        course_id=sample_lectures_base[0].course_id,
        topic_id=sample_lectures_base[0].topic_id,
        revision=sample_lectures_base[0].revision,
        content=sample_lectures_base[0].content,
        summary=sample_lectures_base[0].summary,
        audio_url=sample_lectures_base[0].audio_url,
        transcript_url=sample_lectures_base[0].transcript_url,
    )
    mock_service["generate_lecture"].return_value = generated_lecture_mock

    # --- Apply Patches ---
    base_path = "artificial_u.api.services.LectureApiService"
    monkeypatch.setattr(f"{base_path}.list_lectures", mock_service["list_lectures"])
    monkeypatch.setattr(f"{base_path}.get_lecture", mock_service["get_lecture"])
    monkeypatch.setattr(f"{base_path}.create_lecture", mock_service["create_lecture"])
    monkeypatch.setattr(f"{base_path}.update_lecture", mock_service["update_lecture"])
    monkeypatch.setattr(f"{base_path}.delete_lecture", mock_service["delete_lecture"])
    monkeypatch.setattr(f"{base_path}.get_lecture_content", mock_service["get_lecture_content"])
    monkeypatch.setattr(f"{base_path}.get_lecture_audio_url", mock_service["get_lecture_audio_url"])
    monkeypatch.setattr(f"{base_path}.generate_lecture", mock_service["generate_lecture"])

    return mock_service


# --- Test Cases ---


@pytest.mark.unit
def test_list_lectures(client: TestClient, mock_api_service):
    """Test listing lectures endpoint relies on mocked service."""
    response = client.get("/api/v1/lectures")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert data["total"] == len(sample_lectures_base)
    assert len(data["items"]) == len(sample_lectures_base)
    assert data["items"][0]["content"] == sample_lectures_base[0].content
    assert data["items"][0]["topic_id"] == sample_lectures_base[0].topic_id

    mock_api_service["list_lectures"].assert_called_once_with(
        page=1, size=10, course_id=None, professor_id=None, search=None
    )


@pytest.mark.unit
def test_list_lectures_with_filters(client: TestClient, mock_api_service):
    """Test listing lectures with various filters."""
    filtered_lectures = [lecture for lecture in sample_lectures_base if lecture.course_id == 1]
    mock_api_service["list_lectures"].return_value = LectureList(
        items=filtered_lectures, total=len(filtered_lectures), page=1, page_size=10
    )

    response = client.get("/api/v1/lectures?course_id=1&search=Test")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == len(filtered_lectures)
    assert data["total"] == len(filtered_lectures)

    mock_api_service["list_lectures"].assert_called_once_with(
        page=1, size=10, course_id=1, professor_id=None, search="Test"
    )


@pytest.mark.unit
def test_get_lecture(client: TestClient, mock_api_service):
    """Test getting a single lecture by ID."""
    # Test valid ID
    response = client.get("/api/v1/lectures/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["content"] == sample_lectures_base[0].content
    assert response.json()["topic_id"] == sample_lectures_base[0].topic_id
    mock_api_service["get_lecture"].assert_called_once_with(1)

    # Test invalid ID
    mock_api_service["get_lecture"].reset_mock()
    mock_api_service["get_lecture"].return_value = None
    response = client.get("/api/v1/lectures/999")
    assert response.status_code == 404
    mock_api_service["get_lecture"].assert_called_once_with(999)


@pytest.mark.unit
def test_get_lecture_content(client: TestClient, mock_api_service):
    """Test getting lecture content."""
    # Test valid ID
    response = client.get("/api/v1/lectures/1/content")
    assert response.status_code == 200
    assert response.text == sample_lectures_base[0].content
    mock_api_service["get_lecture_content"].assert_called_once_with(1)

    # Test invalid ID
    mock_api_service["get_lecture_content"].reset_mock()
    mock_api_service["get_lecture_content"].return_value = None
    response = client.get("/api/v1/lectures/999/content")
    assert response.status_code == 404
    mock_api_service["get_lecture_content"].assert_called_once_with(999)


@pytest.mark.unit
def test_get_lecture_audio(client: TestClient, mock_api_service):
    """Test getting lecture audio URL."""
    # Currently the audio endpoint returns 404 for all requests as it's not fully implemented
    mock_api_service["get_lecture_audio_url"].return_value = None

    response = client.get("/api/v1/lectures/1/audio")
    assert response.status_code == 404
    mock_api_service["get_lecture_audio_url"].assert_called_once_with(1)

    # Test another ID to ensure consistent behavior
    mock_api_service["get_lecture_audio_url"].reset_mock()
    response = client.get("/api/v1/lectures/2/audio")
    assert response.status_code == 404
    mock_api_service["get_lecture_audio_url"].assert_called_once_with(2)


@pytest.mark.unit
def test_create_lecture(client: TestClient, mock_api_service):
    """Test creating a new lecture."""
    new_lecture_data = {
        "course_id": 1,
        "topic_id": 50,
        "content": "Full content for the new test lecture",
        "summary": "A new test lecture summary",
        "audio_url": "https://example.com/audio/new_lecture.mp3",
        "transcript_url": "https://example.com/transcript/new_lecture.txt",
        "revision": 1,
    }
    expected_response_data = {
        "id": 5,
        "course_id": new_lecture_data["course_id"],
        "topic_id": new_lecture_data["topic_id"],
        "revision": new_lecture_data["revision"],
        "content": new_lecture_data["content"],
        "summary": new_lecture_data["summary"],
        "audio_url": new_lecture_data["audio_url"],
        "transcript_url": new_lecture_data["transcript_url"],
    }

    response = client.post("/api/v1/lectures", json=new_lecture_data)
    assert response.status_code == 201
    assert response.json() == expected_response_data

    mock_api_service["create_lecture"].assert_called_once()
    call_args = mock_api_service["create_lecture"].call_args[0]
    assert isinstance(call_args[0], LectureCreate)
    assert call_args[0].model_dump() == new_lecture_data


@pytest.mark.unit
def test_update_lecture(client: TestClient, mock_api_service):
    """Test updating an existing lecture."""
    update_data = {"summary": "Updated Lecture Summary", "content": "Updated content"}
    lecture_id_to_update = 2

    response = client.patch(f"/api/v1/lectures/{lecture_id_to_update}", json=update_data)
    assert response.status_code == 200
    assert response.json()["summary"] == update_data["summary"]
    assert response.json()["content"] == update_data["content"]
    assert response.json()["id"] == lecture_id_to_update

    mock_api_service["update_lecture"].assert_called_once()
    call_args = mock_api_service["update_lecture"].call_args[0]
    assert call_args[0] == lecture_id_to_update
    assert isinstance(call_args[1], LectureUpdate)
    assert call_args[1].model_dump(exclude_unset=True) == update_data

    # Test invalid ID
    mock_api_service["update_lecture"].reset_mock()
    mock_api_service["update_lecture"].return_value = None
    response = client.patch("/api/v1/lectures/999", json=update_data)
    assert response.status_code == 404
    mock_api_service["update_lecture"].assert_called_once()


@pytest.mark.unit
def test_delete_lecture(client: TestClient, mock_api_service):
    """Test deleting a lecture."""
    # Test successful deletion
    response = client.delete("/api/v1/lectures/3")
    assert response.status_code == 204
    mock_api_service["delete_lecture"].assert_called_once_with(3)

    # Test deleting non-existent lecture
    mock_api_service["delete_lecture"].reset_mock()
    mock_api_service["delete_lecture"].return_value = False
    response = client.delete("/api/v1/lectures/999")
    assert response.status_code == 404
    mock_api_service["delete_lecture"].assert_called_once_with(999)


@pytest.mark.unit
def test_download_lecture_content(client: TestClient, mock_api_service):
    """Test downloading lecture content as text file."""
    # Test valid ID
    response = client.get("/api/v1/lectures/1/content/download")
    assert response.status_code == 200
    assert response.text == sample_lectures_base[0].content
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    mock_api_service["get_lecture_content"].assert_called_once_with(1)

    # Test invalid ID
    mock_api_service["get_lecture_content"].reset_mock()
    mock_api_service["get_lecture_content"].return_value = None
    response = client.get("/api/v1/lectures/999/content/download")
    assert response.status_code == 404
    mock_api_service["get_lecture_content"].assert_called_once_with(999)


@pytest.mark.unit
def test_generate_lecture(client: TestClient, mock_api_service):
    """Test generating lecture data using AI."""
    generation_data = {
        "partial_attributes": {"course_id": 1, "topic_id": 50},
        "freeform_prompt": "Generate a lecture about testing",
    }

    response = client.post("/api/v1/lectures/generate", json=generation_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "content" in data
    assert "summary" in data
    assert "topic_id" in data
    assert data["topic_id"] == sample_lectures_base[0].topic_id

    mock_api_service["generate_lecture"].assert_called_once()
    call_args = mock_api_service["generate_lecture"].call_args[0]
    assert isinstance(call_args[0], LectureGenerate)
    assert call_args[0].model_dump() == generation_data
