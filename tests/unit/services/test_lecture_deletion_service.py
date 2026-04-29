"""Unit tests for LectureService deletion behavior."""

import json
from unittest.mock import MagicMock

import pytest

from artificial_u.models.core import Lecture
from artificial_u.services.lecture_service import LectureService


class FakeStorageService:
    def __init__(self, failing_objects=None):
        self.audio_bucket = "audio"
        self.lectures_bucket = "lectures"
        self.images_bucket = "images"
        self.uploads = {}
        self.deleted = []
        self.failing_objects = set(failing_objects or [])

    def parse_storage_url(self, url):
        prefix = "https://storage.example/"
        if not url.startswith(prefix):
            return None, None
        path = url.removeprefix(prefix)
        bucket, object_name = path.split("/", 1)
        return bucket, object_name

    def download_file_sync(self, bucket, object_name):
        return self.uploads.get((bucket, object_name)), "application/json"

    def delete_file_sync(self, bucket, object_name):
        self.deleted.append((bucket, object_name))
        return (bucket, object_name) not in self.failing_objects


@pytest.fixture
def repository_factory():
    factory = MagicMock()
    factory.lecture = MagicMock()
    return factory


@pytest.fixture
def lecture_with_assets():
    return Lecture(
        id=1,
        revision=1,
        title="Lecture with assets",
        course_id=10,
        topic_id=20,
        audio_url="https://storage.example/audio/course/lecture.mp3",
        transcript_url="https://storage.example/lectures/course/lecture.txt",
        timeline_url="https://storage.example/lectures/course/lecture_timeline.json",
        images_timeline_url="https://storage.example/lectures/course/lecture_images.json",
    )


@pytest.mark.unit
def test_delete_lecture_cleans_up_storage_assets(repository_factory, lecture_with_assets):
    storage_service = FakeStorageService()
    storage_service.uploads[("lectures", "course/lecture_images.json")] = json.dumps(
        {
            "slots": [
                {"index": 0, "status": "done", "url": "https://storage.example/images/0.png"},
                {"index": 1, "status": "done", "url": "https://storage.example/images/1.png"},
                {"index": 2, "status": "pending", "url": None},
            ]
        }
    ).encode("utf-8")
    repository_factory.lecture.get.return_value = lecture_with_assets
    repository_factory.lecture.delete.return_value = True

    service = LectureService(
        repository_factory=repository_factory,
        storage_service=storage_service,
    )

    assert service.delete_lecture(lecture_with_assets.id) is True
    assert storage_service.deleted == [
        ("images", "0.png"),
        ("images", "1.png"),
        ("audio", "course/lecture.mp3"),
        ("lectures", "course/lecture.txt"),
        ("lectures", "course/lecture_timeline.json"),
        ("lectures", "course/lecture_images.json"),
    ]
    repository_factory.lecture.delete.assert_called_once_with(lecture_with_assets.id)


@pytest.mark.unit
def test_delete_lecture_continues_when_storage_cleanup_fails(
    repository_factory,
    lecture_with_assets,
):
    storage_service = FakeStorageService(failing_objects={("audio", "course/lecture.mp3")})
    repository_factory.lecture.get.return_value = lecture_with_assets
    repository_factory.lecture.delete.return_value = True

    service = LectureService(
        repository_factory=repository_factory,
        storage_service=storage_service,
    )

    assert service.delete_lecture(lecture_with_assets.id) is True
    assert ("audio", "course/lecture.mp3") in storage_service.deleted
    repository_factory.lecture.delete.assert_called_once_with(lecture_with_assets.id)
