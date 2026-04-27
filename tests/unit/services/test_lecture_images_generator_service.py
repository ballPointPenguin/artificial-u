"""Unit tests for lecture image batch planning and per-slide generation."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.services.lecture_images_generator_service import LectureImagesGeneratorService


class FakeStorageService:
    def __init__(self):
        self.images_bucket = "images"
        self.uploads = {}
        self.existing_objects = set()

    async def upload_timeline_file(self, file_data, object_name, content_type):
        self.uploads[object_name] = file_data
        return True, f"https://storage.example/{object_name}"

    async def download_lecture_file(self, object_name):
        return self.uploads[object_name], "application/json"

    def generate_lecture_images_timeline_key(self, course_code, week_number, lecture_order):
        return f"{course_code}/{course_code}_{week_number}_{lecture_order}_images.json"

    def generate_lecture_image_key(self, course_code, week_number, lecture_order, slot_idx):
        return f"{course_code}/{course_code}_{week_number}_{lecture_order}_slide_{slot_idx}.png"

    async def object_exists(self, bucket, object_name):
        return (bucket, object_name) in self.existing_objects

    def get_file_url(self, bucket, object_name):
        return f"https://storage.example/{bucket}/{object_name}"


def make_service(*, storage=None, image_service=None):
    lecture = SimpleNamespace(
        id=123,
        course_id=7,
        topic_id=9,
        timeline_url="https://storage.example/timeline.json",
        content="First paragraph.\n\nSecond paragraph.\n\nThird paragraph.",
        summary="Lecture summary",
        duration=120,
    )
    course = SimpleNamespace(id=7, code="TST100", professor_id=4)
    topic = SimpleNamespace(id=9, week=2, order=3)
    professor = SimpleNamespace(id=4, image_url="https://storage.example/professor.png")

    lecture_service = MagicMock()
    lecture_service.get_lecture.return_value = lecture
    lecture_service.update_lecture = MagicMock()

    course_service = MagicMock()
    course_service.get_course.return_value = course

    topic_service = MagicMock()
    topic_service.get_topic.return_value = topic

    professor_service = MagicMock()
    professor_service.get_professor.return_value = professor

    storage = storage or FakeStorageService()
    if image_service is None:
        image_service = MagicMock()
        image_service.model_name = "gemini-test"
        image_service.generate_lecture_slide_image = AsyncMock()

    service = LectureImagesGeneratorService(
        lecture_service=lecture_service,
        course_service=course_service,
        topic_service=topic_service,
        professor_service=professor_service,
        storage_service=storage,
        image_service=image_service,
        logger=MagicMock(),
    )
    service._fetch_timeline = AsyncMock(return_value={"events": [{"end": 120.0}]})
    return service, storage, lecture_service, image_service


def words(prefix, count):
    return " ".join(f"{prefix}{i}" for i in range(count))


def timeline_events(tokens, *, start_at=0.0, step=0.5):
    return [
        {
            "type": "word",
            "content": token,
            "start": start_at + (idx * step),
            "end": start_at + ((idx + 1) * step),
        }
        for idx, token in enumerate(tokens)
    ]


def test_find_chunk_start_grows_prefix_for_repeated_phrase():
    service, _, _, _ = make_service()
    timeline = {
        "events": timeline_events(
            "common phrase repeated in lecture alpha filler common phrase repeated in lecture beta".split()
        )
    }
    timeline_words = service._timeline_words(timeline)

    match = service._find_chunk_start(
        "common phrase repeated in lecture beta".split(),
        timeline_words,
        cursor=0,
    )

    assert match == {"word_idx": 7, "prefix_len": 6}


@pytest.mark.asyncio
async def test_plan_lecture_images_uploads_scaffold_and_returns_slide_payloads():
    service, storage, lecture_service, _ = make_service()

    result = await service.plan_lecture_images(123, interval_sec=30, min_images=2, max_images=3)

    assert result["lecture_id"] == 123
    assert result["total"] == 3
    assert result["planned"] == 3
    assert len(result["slide_payloads"]) == 3
    assert result["slide_payloads"][0]["slot_idx"] == 0
    assert result["slide_payloads"][0]["batch_id"] == result["batch_id"]

    object_key = result["object_key"]
    timeline = json.loads(storage.uploads[object_key].decode("utf-8"))
    assert timeline["batch_id"] == result["batch_id"]
    assert [slot["status"] for slot in timeline["slots"]] == ["pending", "pending", "pending"]

    lecture_service.update_lecture.assert_called_once_with(
        lecture_id=123,
        update_data={"images_timeline_url": result["images_timeline_url"]},
    )


@pytest.mark.asyncio
async def test_plan_lecture_images_uses_timeline_word_matches_for_slot_times():
    service, storage, _, _ = make_service()
    lecture = service.lecture_service.get_lecture.return_value
    first_chunk = words("alpha", 85)
    second_chunk = words("beta", 85)
    lecture.content = f"{first_chunk}\n\n{second_chunk}"
    lecture.duration = 120
    service._fetch_timeline = AsyncMock(
        return_value={
            "events": timeline_events(["intro", "padding"], start_at=0.0)
            + timeline_events(first_chunk.split(), start_at=12.0)
            + timeline_events(["bridge"], start_at=60.0)
            + timeline_events(second_chunk.split(), start_at=72.0)
        }
    )

    result = await service.plan_lecture_images(123, interval_sec=60, min_images=2, max_images=2)

    timeline = json.loads(storage.uploads[result["object_key"]].decode("utf-8"))
    assert timeline["slots"][0]["start"] == 12.0
    assert timeline["slots"][0]["end"] == 72.0
    assert timeline["slots"][1]["start"] == 72.0
    assert timeline["slots"][1]["end"] == 120.0


@pytest.mark.asyncio
async def test_plan_lecture_images_falls_back_to_even_times_for_unmatched_chunks():
    service, storage, _, _ = make_service()
    lecture = service.lecture_service.get_lecture.return_value
    first_chunk = words("alpha", 85)
    second_chunk = words("beta", 85)
    lecture.content = f"{first_chunk}\n\n{second_chunk}"
    lecture.duration = 120
    service._fetch_timeline = AsyncMock(
        return_value={"events": timeline_events(["unrelated", "words"], start_at=10.0)}
    )

    result = await service.plan_lecture_images(123, interval_sec=60, min_images=2, max_images=2)

    timeline = json.loads(storage.uploads[result["object_key"]].decode("utf-8"))
    assert timeline["slots"][0]["start"] == 0.0
    assert timeline["slots"][0]["end"] == 60.0
    assert timeline["slots"][1]["start"] == 60.0
    assert timeline["slots"][1]["end"] == 120.0


@pytest.mark.asyncio
async def test_generate_lecture_slide_reuses_existing_uploaded_image():
    storage = FakeStorageService()
    service, storage, _, image_service = make_service(storage=storage)

    planned = await service.plan_lecture_images(123, interval_sec=60, min_images=2, max_images=2)
    object_key = planned["object_key"]
    image_key = "TST100/TST100_2_3_slide_1.png"
    storage.existing_objects.add(("images", image_key))

    result = await service.generate_lecture_slide(
        123,
        slot_idx=1,
        object_key=object_key,
        batch_id=planned["batch_id"],
        chunk_text="Second paragraph.",
        previous_chunk_text="First paragraph.",
        aspect_ratio="1:1",
        model_name_override=None,
    )

    assert result["status"] == "done"
    assert result["url"] == f"https://storage.example/images/{image_key}"
    image_service.generate_lecture_slide_image.assert_not_called()

    timeline = json.loads(storage.uploads[object_key].decode("utf-8"))
    assert timeline["slots"][1]["status"] == "done"
    assert timeline["slots"][1]["url"] == result["url"]


@pytest.mark.asyncio
async def test_generate_lecture_slide_passes_previous_slide_url_to_next_prompt():
    storage = FakeStorageService()
    service, _, _, image_service = make_service(storage=storage)
    first_url = "https://storage.example/slide-0.png"
    second_url = "https://storage.example/slide-1.png"
    image_service.generate_lecture_slide_image.side_effect = [first_url, second_url]

    planned = await service.plan_lecture_images(123, interval_sec=60, min_images=2, max_images=2)
    object_key = planned["object_key"]

    await service.generate_lecture_slide(
        123,
        slot_idx=0,
        object_key=object_key,
        batch_id=planned["batch_id"],
        chunk_text="First paragraph.",
        aspect_ratio="1:1",
        model_name_override=None,
    )
    result = await service.generate_lecture_slide(
        123,
        slot_idx=1,
        object_key=object_key,
        batch_id=planned["batch_id"],
        chunk_text="Second paragraph.",
        previous_chunk_text="First paragraph.",
        aspect_ratio="1:1",
        model_name_override=None,
    )

    assert result["status"] == "done"
    assert result["url"] == second_url
    second_call = image_service.generate_lecture_slide_image.await_args_list[1]
    assert second_call.kwargs["previous_slide_url"] == first_url
