"""
Integration tests for course export -> import round trips.

Uses the test database and an in-memory storage backend.
"""

import io
import json
import zipfile
from typing import Dict, Optional, Tuple

import pytest

from artificial_u.models.core import (
    Course,
    Department,
    Faculty,
    Lecture,
    Professor,
    Topic,
    Voice,
)
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.course_export_service import CourseExportService
from artificial_u.services.course_import_service import (
    CourseImportService,
    ImportArchiveError,
    ImportCancelled,
    ImportConflictError,
)
from artificial_u.services.course_purge_service import CoursePurgeService
from artificial_u.services.storage_service import StorageService


class FakeStorage(StorageService):
    """StorageService with an in-memory object store."""

    def __init__(self):  # noqa: super().__init__ would build an S3 client
        import logging

        from artificial_u.config import get_settings

        self.logger = logging.getLogger("fake-storage")
        self.settings = get_settings()
        self.audio_bucket = "audio"
        self.lectures_bucket = "lectures"
        self.images_bucket = "images"
        self.exports_bucket = "exports"
        self.content_logs_bucket = "logs"
        self.objects: Dict[Tuple[str, str], bytes] = {}

    async def upload_file(self, file_data, bucket, object_name, content_type=None):
        self.objects[(bucket, object_name)] = file_data
        return True, self.get_file_url(bucket, object_name)

    def get_file_url(self, bucket, object_name, download=False):
        return f"{self.settings.STORAGE_PUBLIC_URL}/{bucket}/{object_name}"

    async def download_file(self, bucket, object_name) -> Tuple[Optional[bytes], Optional[str]]:
        return self.objects.get((bucket, object_name)), None

    async def delete_file(self, bucket, object_name) -> bool:
        return self.objects.pop((bucket, object_name), None) is not None

    def put(self, bucket: str, key: str, data: bytes) -> str:
        self.objects[(bucket, key)] = data
        return self.get_file_url(bucket, key)


@pytest.fixture
def repos():
    return RepositoryFactory()


@pytest.fixture
def storage():
    return FakeStorage()


@pytest.fixture
def seeded(repos, storage):
    """A course with department, professor+voice, tags, 2 topics, 2 lectures and all assets."""
    faculty = repos.faculty.create(Faculty(name="Faculty of Testing", language="en"))
    dept = repos.department.create(
        Department(name="Testing Dept", code="TST", faculty_id=faculty.id, language="en")
    )
    voice = repos.voice.create(
        Voice(el_voice_id="el-abc", name="Test Voice", gender="female", accent="american")
    )
    prof = repos.professor.create(
        Professor(
            name="Dr. Round Trip",
            department_id=dept.id,
            voice_id=voice.id,
            language="en",
            tts_backend="elevenlabs",
            image_url=storage.put("images", "prof.png", b"profimg"),
        )
    )
    other = repos.course.create(Course(code="TST000", title="Other", department_id=dept.id))
    course = repos.course.create(
        Course(
            code="TST101",
            title="Testing 101",
            department_id=dept.id,
            professor_id=prof.id,
            language="en",
            status="published",
            notes="note",
            image_url=storage.put("images", "course.png", b"courseimg"),
        )
    )
    repos.course.set_connected_courses(course.id, [other.id])
    repos.tag.set_course_tags(
        course.id, [t.id for t in repos.tag.get_or_create_by_names(["Testing", "QA"], "en")]
    )

    lectures = []
    for week in (1, 2):
        topic = repos.topic.create(
            Topic(title=f"Week {week}", week=week, order=1, course_id=course.id, language="en")
        )
        lecture = repos.lecture.create(
            Lecture(
                title=f"Lecture {week}",
                content="word " * 10,
                language="en",
                duration=60,
                course_id=course.id,
                topic_id=topic.id,
            )
        )
        slide = storage.put("images", f"slide{week}.png", f"slide-{week}".encode())
        images_timeline = {"version": 1, "slots": [{"index": 0, "url": slide, "status": "done"}]}
        repos.lecture.update_fields(
            lecture.id,
            {
                "voice_id": voice.id,
                "audio_url": storage.put("audio", f"a{week}.mp3", b"audio%d" % week),
                "transcript_url": storage.put("lectures", f"t{week}.md", b"transcript"),
                "timeline_url": storage.put("lectures", f"tl{week}.json", b'{"words": []}'),
                "images_timeline_url": storage.put(
                    "lectures", f"im{week}.json", json.dumps(images_timeline).encode()
                ),
            },
        )
        lectures.append(lecture)
    return {"course": course, "professor": prof, "department": dept, "other": other}


async def _export(repos, storage, course_id) -> bytes:
    result = await CourseExportService(repos, storage).export_course(course_id)
    assert result["warnings"] == []
    _, key = storage.parse_storage_url(result["url"])
    return storage.objects[("exports", key)]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_round_trip_rename(repos, storage, seeded):
    archive = await _export(repos, storage, seeded["course"].id)
    importer = CourseImportService(repos, storage)

    plan = importer.analyze(archive)
    assert plan["export_version"] == "2.0"
    assert plan["course_code_conflict"]["same_title"] is True
    assert plan["department"]["action"] == "match"
    assert plan["professor"]["action"] == "reuse"
    assert plan["voices"] == [
        {"name": "Test Voice", "tts_backend": "elevenlabs", "action": "match"}
    ]
    assert plan["assets"]["audio"] == 2 and plan["assets"]["lecture_images"] == 2
    assert plan["connected_courses"] == {"found": ["TST000"], "missing": []}

    with pytest.raises(ImportConflictError):
        await importer.execute(archive)
    with pytest.raises(ImportCancelled):
        await importer.execute(archive, {"course_code": "cancel"})

    result = await importer.execute(
        archive, {"course_code": "rename", "new_code": "TST101-2"}, student_id=None
    )
    new = repos.course.get(result["course_id"])
    assert new.code == "TST101-2"
    assert new.status == "published" and new.notes == "note"
    assert new.professor_id == seeded["professor"].id  # reused, not duplicated
    assert len(repos.professor.list()) == 1
    assert new.image_url and new.image_url != seeded["course"].image_url
    assert sorted(t.name for t in repos.tag.list_for_course(new.id)) == ["QA", "Testing"]
    assert [c for c in new.connected_course_ids] == [seeded["other"].id]

    lectures = repos.lecture.list_by_course(new.id)
    assert len(lectures) == 2 and len(repos.topic.list_by_course(new.id)) == 2
    for lecture in lectures:
        assert lecture.duration == 60 and lecture.voice_id
        bucket, key = storage.parse_storage_url(lecture.audio_url)
        assert key.startswith("TST101-2/") and storage.objects[(bucket, key)].startswith(b"audio")
        assert lecture.transcript_url and lecture.timeline_url
        bucket, key = storage.parse_storage_url(lecture.images_timeline_url)
        timeline = json.loads(storage.objects[(bucket, key)])
        slide_url = timeline["slots"][0]["url"]
        assert slide_url.startswith(storage.settings.STORAGE_PUBLIC_URL)
        assert "TST101-2" in slide_url
        assert storage.objects[storage.parse_storage_url(slide_url)].startswith(b"slide-")

    # original untouched
    assert len(repos.lecture.list_by_course(seeded["course"].id)) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_replace_swaps_in_new_copy_and_cleans_old_assets(repos, storage, seeded):
    archive = await _export(repos, storage, seeded["course"].id)
    old_id = seeded["course"].id
    old_lectures = repos.lecture.list_by_course(old_id)
    old_slide = storage.parse_storage_url(
        json.loads(storage.objects[storage.parse_storage_url(old_lectures[0].images_timeline_url)])[
            "slots"
        ][0]["url"]
    )

    result = await CourseImportService(repos, storage).execute(archive, {"course_code": "replace"})

    assert repos.course.get(old_id) is None
    new = repos.course.get(result["course_id"])
    assert new.code == "TST101" and result["replaced_course_id"] == old_id
    assert len(repos.lecture.list_by_course(new.id)) == 2
    assert old_slide not in storage.objects  # old orphan slide cleaned up
    assert new.connected_course_ids == [seeded["other"].id]
    for lecture in repos.lecture.list_by_course(new.id):
        assert storage.parse_storage_url(lecture.audio_url) in storage.objects


@pytest.mark.integration
@pytest.mark.asyncio
async def test_import_into_empty_instance_creates_dependencies(repos, storage, seeded):
    archive = await _export(repos, storage, seeded["course"].id)
    await CoursePurgeService(repos, storage).purge_course(seeded["course"].id)
    repos.professor.delete(seeded["professor"].id)
    repos.course.delete(seeded["other"].id)
    repos.department.delete(seeded["department"].id)

    plan = CourseImportService(repos, storage).analyze(archive)
    assert plan["course_code_conflict"] is None
    assert plan["department"]["action"] == "create"
    assert plan["professor"]["action"] == "create"
    assert plan["connected_courses"]["missing"] == ["TST000"]

    result = await CourseImportService(repos, storage).execute(archive)
    course = repos.course.get(result["course_id"])
    professor = repos.professor.get(course.professor_id)
    assert professor.name == "Dr. Round Trip" and professor.image_url
    assert repos.department.get(course.department_id).code == "TST"
    assert repos.voice.get(professor.voice_id).el_voice_id == "el-abc"
    assert course.connected_course_ids == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_failed_import_rolls_back(repos, storage, seeded, monkeypatch):
    archive = await _export(repos, storage, seeded["course"].id)
    importer = CourseImportService(repos, storage)
    before = len(storage.objects)

    calls = {"n": 0}
    real_upload = storage.upload_file

    async def flaky_upload(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 5:
            return False, None
        return await real_upload(*args, **kwargs)

    monkeypatch.setattr(storage, "upload_file", flaky_upload)
    with pytest.raises(RuntimeError):
        await importer.execute(archive, {"course_code": "rename", "new_code": "TST101-X"})

    assert repos.course.get_by_code("TST101-X") is None
    assert len(storage.objects) == before


@pytest.mark.integration
@pytest.mark.asyncio
async def test_imports_legacy_v1_archive(repos, storage):
    """Format 1.0 had fixed asset paths, no assets map, and fewer fields."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("manifest.json", json.dumps({"export_version": "1.0"}))
        z.writestr("course.json", json.dumps({"id": 7, "code": "OLD101", "title": "Old"}))
        z.writestr("professor.json", json.dumps({"id": 3, "name": "Prof Legacy", "voice": None}))
        z.writestr(
            "topics.json",
            json.dumps([{"id": 11, "title": "T", "week": 1, "order": 1, "course_id": 7}]),
        )
        z.writestr(
            "lectures.json",
            json.dumps(
                [
                    {
                        "id": 21,
                        "title": "L",
                        "revision": 1,
                        "content": "hi",
                        "topic_id": 11,
                        "audio_url": "http://old/audio/x.mp3",
                        "transcript_url": "http://old/lectures/x.txt",
                        "unknown_future_field": True,
                    }
                ]
            ),
        )
        z.writestr("assets/audio/lecture_21.mp3", b"legacy-audio")
        z.writestr("assets/transcripts/lecture_21.txt", b"legacy-transcript")

    importer = CourseImportService(repos, storage)
    plan = importer.analyze(buf.getvalue())
    assert plan["assets"]["audio"] == 1 and plan["warnings"] == []

    result = await importer.execute(buf.getvalue())
    lecture = repos.lecture.list_by_course(result["course_id"])[0]
    assert storage.objects[storage.parse_storage_url(lecture.audio_url)] == b"legacy-audio"
    assert (
        storage.objects[storage.parse_storage_url(lecture.transcript_url)] == b"legacy-transcript"
    )


@pytest.mark.integration
def test_rejects_bad_archives(repos, storage):
    importer = CourseImportService(repos, storage)
    with pytest.raises(ImportArchiveError):
        importer.analyze(b"not a zip")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("manifest.json", json.dumps({"export_version": "99.0"}))
        z.writestr("course.json", json.dumps({"code": "X", "title": "X"}))
    with pytest.raises(ImportArchiveError, match="newer"):
        importer.analyze(buf.getvalue())
