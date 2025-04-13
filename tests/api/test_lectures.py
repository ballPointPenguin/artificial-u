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
from artificial_u.models.core import Course, Lecture, Professor
from artificial_u.models.database import Repository


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture(scope="function")
def temp_assets_dir():
    """Create a temporary assets directory for testing content file generation."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    assets_dir = os.path.join(temp_dir, "assets", "lectures")
    os.makedirs(assets_dir, exist_ok=True)

    # Monkeypatch the path in the service
    # (In a real test, you would use monkeypatch to override the asset directory path)
    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_repository(monkeypatch, temp_assets_dir):
    """Mock repository for testing."""
    from artificial_u.api.routers.lectures import get_repository
    from artificial_u.models.database import Repository

    app.dependency_overrides[get_repository] = lambda: Repository()
    # Sample lecture data
    sample_lectures = [
        {
            "id": i,
            "title": f"Test Lecture {i}",
            "course_id": i % 3 + 1,  # Assign to courses 1-3
            "week_number": (i % 7) + 1,  # Weeks 1-7
            "order_in_week": (i % 2) + 1,  # Order 1-2
            "description": f"Description for lecture {i}",
            "content": f"Full content for lecture {i}. This is a test lecture content.",
            "audio_url": (
                f"mock_storage://audio_files/course_{i % 3 + 1}/lecture_{i}.mp3"
                if i % 2 == 0
                else None
            ),
            "created_at": datetime.now(),
        }
        for i in range(1, 11)
    ]

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

    # Mock content asset paths
    def mock_content_asset_path(cls, lecture_id, *args, **kwargs):
        """Mock to get the content asset path."""
        for lecture in sample_lectures:
            if lecture["id"] == lecture_id:
                # Ensure course_id is an integer
                course_id = (
                    int(lecture["course_id"])
                    if lecture["course_id"] is not None
                    else None
                )
                week = lecture["week_number"]
                order = lecture["order_in_week"]

                # Create directory structure
                content_dir = os.path.join(
                    temp_assets_dir, "assets", "lectures", str(course_id)
                )
                os.makedirs(content_dir, exist_ok=True)

                # Generate filename
                filename = f"w{week}_l{order}_{lecture_id}.txt"
                return os.path.join(content_dir, filename)
        return None

    async def mock_ensure_content_asset(cls, lecture_id, *args, **kwargs):
        """Mock to ensure content asset exists."""
        for lecture in sample_lectures:
            if lecture["id"] == lecture_id:
                # Ensure correct type handling for course_id
                lecture_copy = lecture.copy()
                lecture_copy["course_id"] = (
                    int(lecture_copy["course_id"])
                    if lecture_copy["course_id"] is not None
                    else None
                )

                # Get asset path using the properly typed lecture
                asset_path = mock_content_asset_path(cls, lecture_id)

                # Create the file with content
                with open(asset_path, "w", encoding="utf-8") as f:
                    f.write(lecture["content"])

                return asset_path
        return None

    # Mock the repository methods
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
        for lecture in sample_lectures:
            lecture_course_id = (
                int(lecture["course_id"]) if lecture["course_id"] is not None else None
            )
            if course_id is not None and lecture_course_id != course_id:
                continue
            course = next(
                (c for c in sample_courses if c.id == lecture_course_id), None
            )
            if not course:
                continue
            if professor_id is not None and course.professor_id != professor_id:
                continue
            if search_query is not None:
                if (
                    search_query.lower() not in lecture["title"].lower()
                    and search_query.lower() not in lecture["description"].lower()
                ):
                    continue
            entry = lecture.copy()
            if "generated_at" not in entry:
                entry["generated_at"] = entry.get("created_at")
            filtered.append(Lecture(**entry))
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        page_data = filtered[start_idx:end_idx]

        # Build response models
        response_items = []
        for lecture_core in page_data:
            response_items.append(Lecture.model_validate(lecture_core))

        return response_items

    def mock_get_lecture(self, lecture_id, *args, **kwargs):
        for lecture in sample_lectures:
            if lecture["id"] == lecture_id:
                # Make a copy of the lecture to avoid modifying the original
                lecture_copy = lecture.copy()
                # Ensure course_id is an integer
                lecture_copy["course_id"] = (
                    int(lecture_copy["course_id"])
                    if lecture_copy["course_id"] is not None
                    else None
                )
                if "generated_at" not in lecture_copy:
                    lecture_copy["generated_at"] = lecture_copy.get("created_at")
                return Lecture(
                    **lecture_copy
                )  # Convert the dictionary to a Lecture object
        return None

    def mock_get_lecture_content(self, lecture_id, *args, **kwargs):
        for lecture in sample_lectures:
            if lecture["id"] == lecture_id:
                return {
                    "id": lecture["id"],
                    "title": lecture["title"],
                    "content": lecture["content"],
                    "sections": None,  # In a real system, this would have sections
                }
        return None

    def mock_get_lecture_audio_url(self, lecture_id, *args, **kwargs):
        for lecture in sample_lectures:
            if lecture["id"] == lecture_id:
                return lecture["audio_url"]
        return None

    def mock_create_lecture(self, lecture_data, *args, **kwargs):
        # Create a new ID
        new_id = len(sample_lectures) + 1

        # Create lecture with simplified fields matching the current model
        new_lecture = {
            "id": new_id,
            "title": lecture_data.title,
            "course_id": lecture_data.course_id,
            "week_number": lecture_data.week_number,
            "order_in_week": lecture_data.order_in_week,
            "description": lecture_data.description,
            "content": lecture_data.content,
            "audio_url": None,  # No audio initially
            "created_at": datetime.now(),
        }

        # Add to sample data
        sample_lectures.append(new_lecture)

        # Return detail view with simplified model
        return Lecture(**new_lecture)

    def mock_update_lecture(self, lecture_object, *args, **kwargs):
        # Extract lecture_id and update data from the passed object
        lecture_id = lecture_object.id

        for i, lecture in enumerate(sample_lectures):
            if lecture["id"] == lecture_id:
                # Make a copy to avoid modifying the original directly
                lecture_copy = lecture.copy()

                # Update fields from the lecture_object
                lecture_copy["title"] = lecture_object.title
                lecture_copy["description"] = lecture_object.description
                lecture_copy["content"] = lecture_object.content
                lecture_copy["week_number"] = lecture_object.week_number
                lecture_copy["order_in_week"] = lecture_object.order_in_week
                lecture_copy["audio_url"] = lecture_object.audio_url  # Update audio url

                # Ensure course_id is an integer (if needed, though it shouldn't change)
                lecture_copy["course_id"] = (
                    int(lecture_copy["course_id"])
                    if lecture_copy["course_id"] is not None
                    else None
                )

                # Ensure generated_at exists
                if "generated_at" not in lecture_copy:
                    lecture_copy["generated_at"] = lecture_copy.get("created_at")

                # Update the lecture in the list
                sample_lectures[i] = lecture_copy

                # Return the updated Lecture object
                return Lecture(**lecture_copy)
        return None

    def mock_delete_lecture(self, lecture_id, *args, **kwargs):
        """Mock delete lecture method that prevents recursion"""
        # Use a direct indexing approach instead of iterating during deletion
        lecture_to_delete = None
        lecture_index = None

        # First find the lecture
        for i, lecture in enumerate(sample_lectures):
            if lecture["id"] == lecture_id:
                lecture_to_delete = lecture
                lecture_index = i
                break

        # Then delete it if found
        if lecture_index is not None:
            del sample_lectures[lecture_index]
            return True

        return False

    def mock_build_lecture_summary(self, lecture, courses, professors):
        # Ensure course_id is an integer
        course_id = (
            int(lecture["course_id"]) if lecture["course_id"] is not None else None
        )

        # Create a simplified lecture summary compatible with the current API
        return {
            "id": lecture["id"],
            "title": lecture["title"],
            "course_id": course_id,
            "week_number": lecture["week_number"],
            "order_in_week": lecture["order_in_week"],
            "description": lecture["description"],
            "has_audio": bool(lecture.get("audio_url")),
            "audio_url": lecture.get("audio_url"),
        }

    def mock_build_lecture_detail(self, lecture, courses, professors):
        # Create a simplified lecture detail compatible with the current API
        # Ensure course_id is an integer
        course_id = (
            int(lecture["course_id"]) if lecture["course_id"] is not None else None
        )

        return {
            "id": lecture["id"],
            "title": lecture["title"],
            "description": lecture["description"],
            "content": lecture["content"],
            "course_id": course_id,
            "week_number": lecture["week_number"],
            "order_in_week": lecture["order_in_week"],
            "audio_url": lecture.get("audio_url"),
            "generated_at": lecture.get("generated_at", lecture.get("created_at")),
        }

    def mock_count_lectures(
        self,
        course_id=None,
        professor_id=None,
        search_query=None,
        *args,
        **kwargs,
    ):
        filtered = []
        for lecture in sample_lectures:
            lecture_course_id = (
                int(lecture["course_id"]) if lecture["course_id"] is not None else None
            )
            if course_id is not None and lecture_course_id != course_id:
                continue
            course = next(
                (c for c in sample_courses if c.id == lecture_course_id), None
            )
            if not course:
                continue
            if professor_id is not None and course.professor_id != professor_id:
                continue
            if search_query is not None:
                if (
                    search_query.lower() not in lecture["title"].lower()
                    and search_query.lower() not in lecture["description"].lower()
                ):
                    continue
            filtered.append(lecture)
        return len(filtered)

    def mock_get_course(self, course_id, *args, **kwargs):
        return next((c for c in sample_courses if c.id == course_id), None)

    # Patch the Repository methods
    monkeypatch.setattr(Repository, "list_lectures", mock_list_lectures)
    monkeypatch.setattr(Repository, "count_lectures", mock_count_lectures)
    monkeypatch.setattr(Repository, "get_course", mock_get_course)
    monkeypatch.setattr(Repository, "get_lecture", mock_get_lecture)
    monkeypatch.setattr(Repository, "get_lecture_content", mock_get_lecture_content)
    monkeypatch.setattr(Repository, "get_lecture_audio_url", mock_get_lecture_audio_url)
    monkeypatch.setattr(Repository, "create_lecture", mock_create_lecture)
    monkeypatch.setattr(Repository, "update_lecture", mock_update_lecture)
    monkeypatch.setattr(Repository, "delete_lecture", mock_delete_lecture)
    monkeypatch.setattr(
        Repository, "_build_lecture_summary", mock_build_lecture_summary
    )
    monkeypatch.setattr(Repository, "_build_lecture_detail", mock_build_lecture_detail)

    # Patch the lecture service methods for content assets
    from artificial_u.api.services.lecture_service import LectureApiService

    monkeypatch.setattr(
        LectureApiService, "get_lecture_content_asset_path", mock_content_asset_path
    )
    monkeypatch.setattr(
        LectureApiService, "ensure_content_asset_exists", mock_ensure_content_asset
    )

    # Custom implementation of LectureApiService.get_lecture to handle mocked repository
    def mock_service_get_lecture(self, lecture_id):
        # Get lecture from repository
        lecture = self.repository.get_lecture(lecture_id)
        if not lecture:
            return None

        # The mocked repository.get_lecture now returns a Lecture object directly.
        # We just need to return it.
        return lecture

    # Patch the Lecture service methods
    monkeypatch.setattr(LectureApiService, "get_lecture", mock_service_get_lecture)

    # Store original os.path.exists before patching
    original_path_exists = os.path.exists

    # Mock os.path.exists for audio file checking
    def mock_path_exists(path):
        # For audio files
        if "audio_files" in path and path in [
            lecture["audio_url"] for lecture in sample_lectures if lecture["audio_url"]
        ]:
            return True

        # For text content files (checking if in temporary directory)
        if temp_assets_dir in path:
            # Call the original os.path.exists to avoid recursion
            return original_path_exists(path)

        # For other paths, delegate to the original function
        return original_path_exists(path)

    monkeypatch.setattr(os.path, "exists", mock_path_exists)

    return sample_lectures


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
    lecture_with_audio = next((l for l in mock_repository if l["id"] == 2), None)
    if lecture_with_audio:
        # Set the audio path to be a URL
        lecture_with_audio["audio_url"] = "https://example.com/storage/lecture_2.mp3"
    else:
        # If lecture 2 doesn't exist, find any lecture and set its audio path
        lecture_with_audio = next((l for l in mock_repository), None)
        lecture_with_audio["audio_url"] = (
            "https://example.com/storage/lecture_audio.mp3"
        )

    # Test with lecture that has audio
    response = client.get(
        f"/api/v1/lectures/{lecture_with_audio['id']}/audio", follow_redirects=False
    )
    assert response.status_code == 307  # Temporary redirect
    assert "Location" in response.headers
    assert response.headers["Location"] == lecture_with_audio["audio_url"]

    # Test with lecture that has no audio
    lecture_without_audio = next(
        (l for l in mock_repository if not l["audio_url"]), None
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
