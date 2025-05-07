"""
Tests for the Topics API endpoints.
"""

from unittest.mock import (  # Use MagicMock for sync, AsyncMock for async service methods
    AsyncMock,
    MagicMock,
)

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

# Removed: from artificial_u.api.dependencies import get_topic_api_service
from artificial_u.api.models.topics import (
    Topic,
    TopicCreate,
    TopicList,
    TopicsGenerate,
    TopicUpdate,
)
from artificial_u.api.services.topic_service import TopicApiService  # Keep for spec


@pytest.fixture
def mock_api_service(monkeypatch):
    """Mocks the TopicApiService methods using monkeypatch."""
    mock_service = MagicMock(spec=TopicApiService)
    mock_service.create_topic = MagicMock()
    mock_service.get_topic = MagicMock()
    mock_service.list_topics_by_course = MagicMock()
    mock_service.update_topic = MagicMock()
    mock_service.delete_topic = MagicMock()
    mock_service.generate_topics_for_course = AsyncMock()  # This one remains async

    base_path = "artificial_u.api.services.topic_service.TopicApiService"

    monkeypatch.setattr(f"{base_path}.create_topic", mock_service.create_topic)
    monkeypatch.setattr(f"{base_path}.get_topic", mock_service.get_topic)
    monkeypatch.setattr(f"{base_path}.list_topics_by_course", mock_service.list_topics_by_course)
    monkeypatch.setattr(f"{base_path}.update_topic", mock_service.update_topic)
    monkeypatch.setattr(f"{base_path}.delete_topic", mock_service.delete_topic)
    monkeypatch.setattr(
        f"{base_path}.generate_topics_for_course", mock_service.generate_topics_for_course
    )

    return mock_service


# Removed override_topic_dependency fixture

# Test data
BASE_TOPIC_URL = "/api/v1/topics"
SAMPLE_TOPIC_PAYLOAD = {
    "title": "Introduction to Quantum Physics",
    "course_id": 1,
    "week": 1,
    "order": 1,
}
SAMPLE_TOPIC_ID = 1
SAMPLE_COURSE_ID = 1


@pytest.mark.unit
def test_create_topic_success(client: TestClient, mock_api_service: MagicMock):
    """Test successful topic creation."""
    topic_create_data = TopicCreate(**SAMPLE_TOPIC_PAYLOAD)
    expected_topic = Topic(id=SAMPLE_TOPIC_ID, **topic_create_data.model_dump())
    mock_api_service.create_topic.return_value = expected_topic

    response = client.post(BASE_TOPIC_URL, json=topic_create_data.model_dump())

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_topic.model_dump()
    mock_api_service.create_topic.assert_called_once_with(topic_create_data)


@pytest.mark.unit
def test_create_topic_database_error(client: TestClient, mock_api_service: MagicMock):
    """Test topic creation when a database error occurs."""
    topic_create_data = TopicCreate(**SAMPLE_TOPIC_PAYLOAD)
    # Ensure the service mock raises HTTPException directly, as the router would re-raise it
    error_message = "Database error"
    status_code = status.HTTP_400_BAD_REQUEST
    mock_api_service.create_topic.side_effect = HTTPException(
        status_code=status_code, detail=error_message
    )

    response = client.post(BASE_TOPIC_URL, json=topic_create_data.model_dump())

    assert response.status_code == status_code
    assert response.json() == {
        "message": error_message,
        "details": None,  # Assuming details is None for these errors
        "error_code": "HTTP_ERROR",  # Assuming a generic error code
        "status_code": status_code,
    }


@pytest.mark.unit
def test_get_topic_success(client: TestClient, mock_api_service: MagicMock):
    """Test successfully retrieving a topic by ID."""
    expected_topic = Topic(id=SAMPLE_TOPIC_ID, **SAMPLE_TOPIC_PAYLOAD)
    mock_api_service.get_topic.return_value = expected_topic

    response = client.get(f"{BASE_TOPIC_URL}/{SAMPLE_TOPIC_ID}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_topic.model_dump()
    mock_api_service.get_topic.assert_called_once_with(SAMPLE_TOPIC_ID)


@pytest.mark.unit
def test_get_topic_not_found(client: TestClient, mock_api_service: MagicMock):
    """Test retrieving a topic that does not exist."""
    error_message = "Topic not found"
    status_code = status.HTTP_404_NOT_FOUND
    mock_api_service.get_topic.side_effect = HTTPException(
        status_code=status_code, detail=error_message
    )

    response = client.get(f"{BASE_TOPIC_URL}/{SAMPLE_TOPIC_ID}")

    assert response.status_code == status_code
    assert response.json() == {
        "message": error_message,
        "details": None,
        "error_code": "HTTP_ERROR",
        "status_code": status_code,
    }


@pytest.mark.unit
def test_list_topics_by_course_success(client: TestClient, mock_api_service: MagicMock):
    """Test successfully listing topics for a course."""
    topic_item = Topic(id=SAMPLE_TOPIC_ID, **SAMPLE_TOPIC_PAYLOAD)
    expected_topic_list = TopicList(items=[topic_item], total=1, page=1, page_size=10)
    mock_api_service.list_topics_by_course.return_value = expected_topic_list

    response = client.get(f"{BASE_TOPIC_URL}?course_id={SAMPLE_COURSE_ID}&page=1&size=10")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_topic_list.model_dump()
    mock_api_service.list_topics_by_course.assert_called_once_with(
        course_id=SAMPLE_COURSE_ID, page=1, size=10
    )


@pytest.mark.unit
def test_list_topics_by_course_course_not_found(client: TestClient, mock_api_service: MagicMock):
    """Test listing topics for a course that does not exist."""
    error_message = "Course not found"
    status_code = status.HTTP_404_NOT_FOUND
    mock_api_service.list_topics_by_course.side_effect = HTTPException(
        status_code=status_code, detail=error_message
    )

    response = client.get(f"{BASE_TOPIC_URL}?course_id={SAMPLE_COURSE_ID}")

    assert response.status_code == status_code
    assert response.json() == {
        "message": error_message,
        "details": None,
        "error_code": "HTTP_ERROR",
        "status_code": status_code,
    }


@pytest.mark.unit
def test_update_topic_success(client: TestClient, mock_api_service: MagicMock):
    """Test successfully updating a topic."""
    topic_update_data = TopicUpdate(title="Updated Quantum Physics")
    updated_payload = SAMPLE_TOPIC_PAYLOAD.copy()
    updated_payload["title"] = "Updated Quantum Physics"
    expected_topic = Topic(id=SAMPLE_TOPIC_ID, **updated_payload)

    mock_api_service.update_topic.return_value = expected_topic

    response = client.patch(
        f"{BASE_TOPIC_URL}/{SAMPLE_TOPIC_ID}", json=topic_update_data.model_dump(exclude_unset=True)
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_topic.model_dump()
    mock_api_service.update_topic.assert_called_once_with(SAMPLE_TOPIC_ID, topic_update_data)


@pytest.mark.unit
def test_update_topic_not_found(client: TestClient, mock_api_service: MagicMock):
    """Test updating a topic that does not exist."""
    topic_update_data = TopicUpdate(title="Updated Quantum Physics")
    error_message = "Topic not found"
    status_code = status.HTTP_404_NOT_FOUND
    mock_api_service.update_topic.side_effect = HTTPException(
        status_code=status_code, detail=error_message
    )

    response = client.patch(
        f"{BASE_TOPIC_URL}/{SAMPLE_TOPIC_ID}", json=topic_update_data.model_dump(exclude_unset=True)
    )

    assert response.status_code == status_code
    assert response.json() == {
        "message": error_message,
        "details": None,
        "error_code": "HTTP_ERROR",
        "status_code": status_code,
    }


@pytest.mark.unit
def test_delete_topic_success(client: TestClient, mock_api_service: MagicMock):
    """Test successfully deleting a topic."""
    mock_api_service.delete_topic.return_value = True  # Service returns True on success

    response = client.delete(f"{BASE_TOPIC_URL}/{SAMPLE_TOPIC_ID}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_api_service.delete_topic.assert_called_once_with(SAMPLE_TOPIC_ID)


@pytest.mark.unit
def test_delete_topic_not_found(client: TestClient, mock_api_service: MagicMock):
    """Test deleting a topic that does not exist."""
    error_message = "Topic not found for deletion"
    status_code = status.HTTP_404_NOT_FOUND
    mock_api_service.delete_topic.side_effect = HTTPException(
        status_code=status_code, detail=error_message
    )

    response = client.delete(f"{BASE_TOPIC_URL}/{SAMPLE_TOPIC_ID}")

    assert response.status_code == status_code
    assert response.json() == {
        "message": error_message,
        "details": None,
        "error_code": "HTTP_ERROR",
        "status_code": status_code,
    }


# Test data for generation endpoint
BASE_COURSE_TOPICS_URL = "/api/v1/courses"


# Tests for /courses/{course_id}/topics/generate
@pytest.mark.unit  # Added unit marker
def test_generate_topics_for_course_success(client: TestClient, mock_api_service: MagicMock):
    """Test successfully generating topics for a course."""
    freeform_prompt = "Focus on practical applications"
    generation_data_obj = TopicsGenerate(
        course_id=SAMPLE_COURSE_ID, freeform_prompt=freeform_prompt
    )

    topic_item_1 = Topic(
        id=1, title="Generated Topic 1", course_id=SAMPLE_COURSE_ID, week=1, order=1
    )
    topic_item_2 = Topic(
        id=2, title="Generated Topic 2", course_id=SAMPLE_COURSE_ID, week=1, order=2
    )
    expected_topics = [topic_item_1, topic_item_2]

    mock_api_service.generate_topics_for_course.return_value = expected_topics

    url = f"{BASE_COURSE_TOPICS_URL}/{SAMPLE_COURSE_ID}/topics/generate"
    params = {"freeform_prompt": freeform_prompt}
    response = client.post(url, params=params)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [topic.model_dump() for topic in expected_topics]
    mock_api_service.generate_topics_for_course.assert_called_once_with(generation_data_obj)


@pytest.mark.unit  # Added unit marker
def test_generate_topics_for_course_no_prompt(client: TestClient, mock_api_service: MagicMock):
    """Test generating topics for a course without an optional prompt."""
    generation_data_obj = TopicsGenerate(course_id=SAMPLE_COURSE_ID, freeform_prompt=None)
    expected_topic = Topic(
        id=1, title="Generated Topic No Prompt", course_id=SAMPLE_COURSE_ID, week=1, order=1
    )
    mock_api_service.generate_topics_for_course.return_value = [expected_topic]

    url = f"{BASE_COURSE_TOPICS_URL}/{SAMPLE_COURSE_ID}/topics/generate"
    # No params needed if freeform_prompt is None, as Query(None...) handles it
    response = client.post(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [expected_topic.model_dump()]
    mock_api_service.generate_topics_for_course.assert_called_once_with(generation_data_obj)


@pytest.mark.unit  # Added unit marker
def test_generate_topics_for_course_course_not_found(
    client: TestClient, mock_api_service: MagicMock
):
    """Test generating topics for a course that does not exist."""
    error_message = "Course not found"
    status_code = status.HTTP_404_NOT_FOUND
    mock_api_service.generate_topics_for_course.side_effect = HTTPException(
        status_code=status_code, detail=error_message
    )

    response = client.post(f"{BASE_COURSE_TOPICS_URL}/{SAMPLE_COURSE_ID}/topics/generate")

    assert response.status_code == status_code
    assert response.json() == {
        "message": error_message,
        "details": None,
        "error_code": "HTTP_ERROR",
        "status_code": status_code,
    }


@pytest.mark.unit  # Added unit marker
def test_generate_topics_for_course_generation_error(
    client: TestClient, mock_api_service: MagicMock
):
    """Test topic generation when a content generation error occurs."""
    error_message = "Content generation error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_api_service.generate_topics_for_course.side_effect = HTTPException(
        status_code=status_code, detail=error_message
    )

    response = client.post(f"{BASE_COURSE_TOPICS_URL}/{SAMPLE_COURSE_ID}/topics/generate")

    assert response.status_code == status_code
    assert response.json() == {
        "message": error_message,
        "details": None,
        "error_code": "HTTP_ERROR",
        "status_code": status_code,
    }
