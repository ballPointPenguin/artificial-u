"""
Tests for the lecture API endpoints.
"""

import os
import shutil
import tempfile
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.app import app
from artificial_u.models.core import Course, Lecture

# Sample data used by mocks
sample_lectures_data = [
    {
        "id": i,
        "title": f"Test Lecture {i}",
        "course_id": i % 3 + 1,  # Assign to courses 1-3
        "week_number": (i % 7) + 1,  # Weeks 1-7
        "order_in_week": (i % 2) + 1,  # Order 1-2
        "description": f"Description for lecture {i}",
        "content": f"Full content for lecture {i}. This is a test lecture content.",
        "audio_url": (
            f"mock_storage://audio_files/course_{i % 3 + 1}/lecture_{i}.mp3" if i % 2 == 0 else None
        ),
        "created_at": datetime.now(),
    }
    for i in range(1, 11)
]

sample_courses_data = [
    Course(
        id=i,
        code=f"CS{i}01",
        title=f"Test Course {i}",
        department_id=1,
        level="Undergraduate" if i % 2 == 0 else "Graduate",
        credits=3,
        professor_id=i,
        description=f"Description for course {i}",
        lectures_per_week=2,
        total_weeks=14,
    )
    for i in range(1, 4)
]


# Mock repository functions
def mock_list_lectures(
    self,
    page=1,
    size=10,
    course_id=None,
    professor_id=None,
    search_query=None,
    *args,
    **kwargs,
):
    filtered = []
    for lecture_dict in sample_lectures_data:
        lecture_course_id = lecture_dict.get("course_id")
        if course_id is not None and lecture_course_id != course_id:
            continue
        course = next((c for c in sample_courses_data if c.id == lecture_course_id), None)
        if not course:
            continue
        if professor_id is not None and course.professor_id != professor_id:
            continue
        if search_query is not None:
            if (
                search_query.lower() not in lecture_dict.get("title", "").lower()
                and search_query.lower() not in lecture_dict.get("description", "").lower()
            ):
                continue
        filtered.append(Lecture(**lecture_dict))
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    return filtered[start_idx:end_idx]


def mock_get_lecture(self, lecture_id, *args, **kwargs):
    for lecture_dict in sample_lectures_data:
        if lecture_dict.get("id") == lecture_id:
            return Lecture(**lecture_dict)
    return None


def mock_get_lecture_content(self, lecture_id, *args, **kwargs):
    for lecture_dict in sample_lectures_data:
        if lecture_dict.get("id") == lecture_id:
            return lecture_dict.get("content")  # Return just content
    return None


def mock_get_lecture_audio_url(self, lecture_id, *args, **kwargs):
    for lecture_dict in sample_lectures_data:
        if lecture_dict.get("id") == lecture_id:
            return lecture_dict.get("audio_url")
    return None


def mock_create_lecture(self, lecture_data, *args, **kwargs):
    new_id = len(sample_lectures_data) + 1
    new_lecture_dict = {
        "id": new_id,
        "title": lecture_data.title,
        "course_id": lecture_data.course_id,
        "week_number": lecture_data.week_number,
        "order_in_week": lecture_data.order_in_week,
        "description": lecture_data.description,
        "content": lecture_data.content,
        "audio_url": lecture_data.audio_url,
        "created_at": datetime.now(),
    }
    sample_lectures_data.append(new_lecture_dict)
    return Lecture(**new_lecture_dict)


def mock_update_lecture(self, lecture_object, *args, **kwargs):
    for i, lecture_dict in enumerate(sample_lectures_data):
        if lecture_dict.get("id") == lecture_object.id:
            # Update the dictionary
            updated_dict = lecture_dict.copy()
            updated_dict.update(lecture_object.model_dump(exclude_unset=True))
            sample_lectures_data[i] = updated_dict
            return Lecture(**updated_dict)
    return None


def mock_delete_lecture(self, lecture_id, *args, **kwargs):
    global sample_lectures_data
    initial_len = len(sample_lectures_data)
    sample_lectures_data = [
        lec_dict for lec_dict in sample_lectures_data if lec_dict.get("id") != lecture_id
    ]
    return len(sample_lectures_data) < initial_len


def mock_count_lectures(
    self,
    course_id=None,
    professor_id=None,
    search_query=None,
    *args,
    **kwargs,
):
    # Simplified count based on filtered list from mock_list_lectures logic
    # This avoids duplicating the complex filtering logic here
    filtered = []
    for lecture_dict in sample_lectures_data:
        lecture_course_id = lecture_dict.get("course_id")
        if course_id is not None and lecture_course_id != course_id:
            continue
        course = next((c for c in sample_courses_data if c.id == lecture_course_id), None)
        if not course:
            continue
        if professor_id is not None and course.professor_id != professor_id:
            continue
        if search_query is not None:
            if (
                search_query.lower() not in lecture_dict.get("title", "").lower()
                and search_query.lower() not in lecture_dict.get("description", "").lower()
            ):
                continue
        filtered.append(Lecture(**lecture_dict))
    return len(filtered)


def mock_get_course(self, course_id, *args, **kwargs):
    return next((c for c in sample_courses_data if c.id == course_id), None)


# Mock content asset path generation (remains in the test setup as it depends on temp_assets_dir)
def get_mock_content_asset_path(temp_dir, lecture_id):
    for lecture in sample_lectures_data:
        if lecture["id"] == lecture_id:
            course_id = lecture["course_id"]
            week = lecture["week_number"]
            order = lecture["order_in_week"]
            content_dir = os.path.join(temp_dir, "assets", "lectures", str(course_id))
            os.makedirs(content_dir, exist_ok=True)
            filename = f"w{week}_l{order}_{lecture_id}.txt"
            return os.path.join(content_dir, filename)
    return None


async def mock_ensure_content_asset(temp_dir, lecture_id):
    asset_path = get_mock_content_asset_path(temp_dir, lecture_id)
    if not asset_path:
        return None
    for lecture in sample_lectures_data:
        if lecture["id"] == lecture_id:
            with open(asset_path, "w", encoding="utf-8") as f:
                f.write(lecture["content"])
            return asset_path
    return None


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture(scope="function")
def temp_assets_dir():
    """Create a temporary assets directory for testing content file generation."""
    temp_dir = tempfile.mkdtemp()
    assets_dir = os.path.join(temp_dir, "assets", "lectures")
    os.makedirs(assets_dir, exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_repository(monkeypatch, temp_assets_dir):
    """Mock repository for testing by patching nested repository methods."""
    # Patch repository methods
    monkeypatch.setattr(
        "artificial_u.models.repositories.lecture.LectureRepository.list",
        mock_list_lectures,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.lecture.LectureRepository.count",
        mock_count_lectures,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.lecture.LectureRepository.get",
        mock_get_lecture,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.lecture.LectureRepository.get_content",
        mock_get_lecture_content,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.lecture.LectureRepository.get_audio_url",
        mock_get_lecture_audio_url,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.lecture.LectureRepository.create",
        mock_create_lecture,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.lecture.LectureRepository.update",
        mock_update_lecture,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.lecture.LectureRepository.delete",
        mock_delete_lecture,
    )
    monkeypatch.setattr(
        "artificial_u.models.repositories.course.CourseRepository.get", mock_get_course
    )

    # Patch service methods related to file handling
    from artificial_u.api.services import LectureApiService

    # Use lambda to pass temp_assets_dir to the mock functions
    monkeypatch.setattr(
        LectureApiService,
        "get_lecture_content_asset_path",
        lambda self, lid: get_mock_content_asset_path(temp_assets_dir, lid),
    )
    monkeypatch.setattr(
        LectureApiService,
        "ensure_content_asset_exists",
        lambda self, lid: mock_ensure_content_asset(temp_assets_dir, lid),
    )

    # Mock os.path.exists to handle temp asset paths and known audio URLs
    original_path_exists = os.path.exists

    def mock_path_exists(path):
        if temp_assets_dir in path:
            return original_path_exists(path)  # Check actual temp file
        if path in [
            lec_dict.get("audio_url")
            for lec_dict in sample_lectures_data
            if lec_dict.get("audio_url")
        ]:
            return True  # Assume mock audio URLs exist
        return original_path_exists(path)

    monkeypatch.setattr(os.path, "exists", mock_path_exists)

    return sample_lectures_data  # Return sample data if needed by tests


@pytest.mark.api
def test_list_lectures(client, mock_repository):
    """Test listing lectures endpoint."""
    response = client.get("/api/v1/lectures")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 10  # All 10 test lectures
    assert data["total"] == 10


@pytest.mark.api
def test_filter_lectures_by_course(client, mock_repository):
    """Test filtering lectures by course ID."""
    response = client.get("/api/v1/lectures?course_id=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert item["course_id"] == 1


@pytest.mark.api
def test_get_lecture(client, mock_repository):
    """Test getting a single lecture by ID."""
    # Test with valid ID
    response = client.get("/api/v1/lectures/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "title" in data
    assert "content" in data

    # Test with invalid ID
    response = client.get("/api/v1/lectures/999")
    assert response.status_code == 404


@pytest.mark.api
def test_get_lecture_content(client, mock_repository):
    """Test getting lecture content."""
    # Test with valid ID
    response = client.get("/api/v1/lectures/1/content")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "content" in data
    assert "Full content for lecture 1" in data["content"]

    # Test with invalid ID
    response = client.get("/api/v1/lectures/999/content")
    assert response.status_code == 404


@pytest.mark.api
def test_download_lecture_content(client, mock_repository):
    """Test downloading lecture content as a file."""
    # Test with valid ID
    response = client.get("/api/v1/lectures/1/content/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "lecture_1_Test_Lecture_1.txt" in response.headers["content-disposition"]
    assert "Full content for lecture 1" in response.text

    # Test with invalid ID
    response = client.get("/api/v1/lectures/999/content/download")
    assert response.status_code == 404


@pytest.mark.api
def test_get_lecture_audio(client, mock_repository):
    """Test getting lecture audio."""
    # Find a lecture with audio path that's a URL
    lecture_with_audio = next((lecture for lecture in mock_repository if lecture["id"] == 2), None)
    if lecture_with_audio:
        # Set the audio path to be a URL
        lecture_with_audio["audio_url"] = "https://example.com/storage/lecture_2.mp3"
    else:
        # If lecture 2 doesn't exist, find any lecture and set its audio path
        lecture_with_audio = next((lecture for lecture in mock_repository), None)
        lecture_with_audio["audio_url"] = "https://example.com/storage/lecture_audio.mp3"

    # Test with lecture that has audio
    response = client.get(
        f"/api/v1/lectures/{lecture_with_audio['id']}/audio", follow_redirects=False
    )
    assert response.status_code == 307  # Temporary redirect
    assert "Location" in response.headers
    assert response.headers["Location"] == lecture_with_audio["audio_url"]

    # Test with lecture that has no audio
    lecture_without_audio = next(
        (lecture for lecture in mock_repository if not lecture["audio_url"]), None
    )
    assert lecture_without_audio is not None

    response = client.get(f"/api/v1/lectures/{lecture_without_audio['id']}/audio")
    assert response.status_code == 404


@pytest.mark.api
def test_create_lecture(client, mock_repository):
    """Test creating a new lecture."""
    new_lecture = {
        "title": "New Test Lecture",
        "course_id": 1,
        "week_number": 8,
        "order_in_week": 1,
        "description": "Description for the new test lecture",
        "content": "This is the content for the new test lecture.",
        "audio_url": None,
    }

    response = client.post("/api/v1/lectures", json=new_lecture)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 11  # Should be the 11th lecture
    assert data["title"] == "New Test Lecture"
    assert data["course_id"] == 1
    assert data["audio_url"] is None


@pytest.mark.api
def test_update_lecture(client, mock_repository):
    """Test updating an existing lecture."""
    # First, check that lecture 1 exists
    check_response = client.get("/api/v1/lectures/1")
    assert check_response.status_code == 200

    update_data = {
        "title": "Updated Lecture Title",
        "description": "Updated lecture description",
    }

    # Test with valid ID
    response = client.patch("/api/v1/lectures/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Updated Lecture Title"
    assert data["description"] == "Updated lecture description"
    assert data["audio_url"] is None

    # Test updating audio_url
    update_data_with_audio = {"audio_url": "https://new.storage.com/audio.mp3"}
    response = client.patch("/api/v1/lectures/1", json=update_data_with_audio)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Updated Lecture Title"
    assert data["description"] == "Updated lecture description"
    assert data["audio_url"] == "https://new.storage.com/audio.mp3"

    # Test with invalid ID
    response = client.patch("/api/v1/lectures/999", json=update_data)
    assert response.status_code == 404


@pytest.mark.api
def test_update_lecture_content(client, mock_repository):
    """Test updating lecture content and validating content file is updated."""
    # First, download the original content to compare later
    download_response = client.get("/api/v1/lectures/1/content/download")
    assert download_response.status_code == 200
    original_content = download_response.text

    # Update the lecture content
    update_data = {"content": "This is updated content for testing purposes."}

    response = client.patch("/api/v1/lectures/1", json=update_data)
    assert response.status_code == 200

    # Download the updated content file
    updated_download = client.get("/api/v1/lectures/1/content/download")
    assert updated_download.status_code == 200
    updated_content = updated_download.text

    # Verify the content was updated
    assert updated_content != original_content
    assert "This is updated content for testing purposes." == updated_content


@pytest.mark.api
def test_delete_lecture(client, mock_repository):
    """Test deleting a lecture."""
    # Test with valid ID
    response = client.delete("/api/v1/lectures/1")
    assert response.status_code == 204

    # Verify it's deleted
    check_response = client.get("/api/v1/lectures/1")
    assert check_response.status_code == 404

    # Test with invalid ID
    response = client.delete("/api/v1/lectures/999")
    assert response.status_code == 404


@pytest.mark.api
def test_get_lecture_by_id(client, mock_repository):
    """Test getting a lecture by ID directly."""
    response = client.get("/api/v1/lectures/2")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert "title" in data
    assert "description" in data
