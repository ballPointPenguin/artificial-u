from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.models.job_priorities import priority_for_kind
from artificial_u.services.job_service import JobService


class FakeJobRepository:
    def __init__(self):
        self.created = []

    def create(
        self,
        *,
        kind,
        payload,
        priority=None,
        run_after=None,
        max_attempts=2,
        parent_job_id=None,
    ):
        # Mirror the real repository: derive priority from the kind when unset.
        if priority is None:
            priority = priority_for_kind(kind)
        row = SimpleNamespace(id=len(self.created) + 1)
        self.created.append(
            {
                "kind": kind,
                "payload": payload,
                "priority": priority,
                "run_after": run_after,
                "max_attempts": max_attempts,
                "parent_job_id": parent_job_id,
            }
        )
        return row


class FakeLectureRepository:
    def __init__(self):
        self.lecture = SimpleNamespace(
            id=123,
            topic_id=9,
            images_timeline_url="https://storage.example/TST100_images.json",
        )

    def get(self, lecture_id):
        return self.lecture


class FakeRepositoryFactory:
    def __init__(self):
        self.job = FakeJobRepository()
        self.lecture = FakeLectureRepository()


@pytest.mark.asyncio
async def test_generate_lecture_images_enqueues_only_first_chained_slide():
    repository_factory = FakeRepositoryFactory()
    service = JobService(repository_factory=repository_factory, logger=MagicMock())
    images_service = MagicMock()
    images_service.delete_existing_lecture_images = AsyncMock()
    images_service.plan_lecture_images = AsyncMock(
        return_value={
            "lecture_id": 123,
            "total": 3,
            "slide_payloads": [
                {"slot_idx": 0, "chunk_text": "first"},
                {"slot_idx": 1, "chunk_text": "second"},
                {"slot_idx": 2, "chunk_text": "third"},
            ],
        }
    )
    service._lecture_images_generator_service_instance = MagicMock(return_value=images_service)

    result = await service._handle_generate_lecture_images({"lecture_id": 123})

    assert result["enqueued"] == 1
    assert result["chain_remaining"] == 2
    assert result["slide_job_ids"] == [1]
    assert len(repository_factory.job.created) == 1

    created = repository_factory.job.created[0]
    assert created["kind"] == "generate_lecture_slide"
    # Slides inherit the neutral priority for their kind (no longer demoted).
    assert created["priority"] == priority_for_kind("generate_lecture_slide")
    assert created["payload"]["slot_idx"] == 0
    assert created["payload"]["next_slide_payload"]["slot_idx"] == 1
    assert created["payload"]["next_slide_payload"]["next_slide_payload"]["slot_idx"] == 2
    images_service.delete_existing_lecture_images.assert_not_called()


@pytest.mark.asyncio
async def test_generate_lecture_images_deletes_existing_images_when_requested():
    repository_factory = FakeRepositoryFactory()
    service = JobService(repository_factory=repository_factory, logger=MagicMock())
    images_service = MagicMock()
    images_service.delete_existing_lecture_images = AsyncMock(
        return_value={"lecture_id": 123, "deleted": 2}
    )
    images_service.plan_lecture_images = AsyncMock(
        return_value={
            "lecture_id": 123,
            "total": 1,
            "slide_payloads": [{"slot_idx": 0, "chunk_text": "first"}],
        }
    )
    service._lecture_images_generator_service_instance = MagicMock(return_value=images_service)

    result = await service._handle_generate_lecture_images(
        {"lecture_id": 123, "delete_existing_images": True}
    )

    assert result["deleted_existing_images"] == 2
    images_service.delete_existing_lecture_images.assert_awaited_once_with(123)


@pytest.mark.asyncio
async def test_resume_lecture_images_enqueues_only_unfinished_chained_slides():
    repository_factory = FakeRepositoryFactory()
    service = JobService(repository_factory=repository_factory, logger=MagicMock())
    images_service = MagicMock()
    images_service.resume_lecture_images = AsyncMock(
        return_value={
            "lecture_id": 123,
            "total": 3,
            "completed": 1,
            "resume_planned": 2,
            "slide_payloads": [
                {"slot_idx": 1, "chunk_text": "second"},
                {"slot_idx": 2, "chunk_text": "third"},
            ],
        }
    )
    service._lecture_images_generator_service_instance = MagicMock(return_value=images_service)

    result = await service._handle_resume_lecture_images({"lecture_id": 123})

    assert result["completed"] == 1
    assert result["resume_planned"] == 2
    assert result["enqueued"] == 1
    assert result["chain_remaining"] == 1
    created = repository_factory.job.created[0]
    assert created["kind"] == "generate_lecture_slide"
    assert created["priority"] == priority_for_kind("generate_lecture_slide")
    assert created["payload"]["slot_idx"] == 1
    assert created["payload"]["next_slide_payload"]["slot_idx"] == 2


@pytest.mark.asyncio
async def test_generate_lecture_timeline_enqueues_image_timeline_remap_when_images_exist():
    repository_factory = FakeRepositoryFactory()
    service = JobService(repository_factory=repository_factory, logger=MagicMock())
    lecture_service = MagicMock()
    lecture_service.generate_lecture_timeline = AsyncMock(
        return_value={"lecture_id": 123, "timeline_url": "https://storage.example/timeline.json"}
    )
    service._lecture_generator_service_instance = MagicMock(return_value=lecture_service)

    result = await service._handle_generate_lecture_timeline({"lecture_id": 123, "topic_id": 9})

    assert result["remap_images_timeline_job_id"] == 1
    assert repository_factory.job.created[0]["kind"] == "remap_lecture_images_timeline"
    assert repository_factory.job.created[0]["payload"] == {"lecture_id": 123, "topic_id": 9}


@pytest.mark.asyncio
async def test_remap_lecture_images_timeline_dispatches_to_image_service():
    repository_factory = FakeRepositoryFactory()
    service = JobService(repository_factory=repository_factory, logger=MagicMock())
    images_service = MagicMock()
    images_service.remap_lecture_images_timeline = AsyncMock(
        return_value={"lecture_id": 123, "remapped": 3, "preserved_images": 3}
    )
    service._lecture_images_generator_service_instance = MagicMock(return_value=images_service)

    result = await service._handle_remap_lecture_images_timeline({"lecture_id": 123})

    assert result["remapped"] == 3
    images_service.remap_lecture_images_timeline.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_lecture_slide_enqueues_next_slide_after_success():
    repository_factory = FakeRepositoryFactory()
    service = JobService(repository_factory=repository_factory, logger=MagicMock())
    images_service = MagicMock()
    images_service.generate_lecture_slide = AsyncMock(
        return_value={
            "lecture_id": 123,
            "slot_idx": 0,
            "status": "done",
            "url": "https://storage.example/slide-0.png",
        }
    )
    service._lecture_images_generator_service_instance = MagicMock(return_value=images_service)

    result = await service._handle_generate_lecture_slide(
        {
            "lecture_id": 123,
            "slot_idx": 0,
            "object_key": "TST100/images.json",
            "chunk_text": "first",
            "next_slide_payload": {
                "lecture_id": 123,
                "slot_idx": 1,
                "object_key": "TST100/images.json",
                "chunk_text": "second",
            },
        }
    )

    assert result["next_slide_job_id"] == 1
    assert len(repository_factory.job.created) == 1
    created = repository_factory.job.created[0]
    assert created["kind"] == "generate_lecture_slide"
    assert created["priority"] == priority_for_kind("generate_lecture_slide")
    assert created["payload"]["slot_idx"] == 1


@pytest.mark.asyncio
async def test_generate_lecture_slide_does_not_enqueue_next_slide_after_failure():
    repository_factory = FakeRepositoryFactory()
    service = JobService(repository_factory=repository_factory, logger=MagicMock())
    images_service = MagicMock()
    images_service.generate_lecture_slide = AsyncMock(
        return_value={"lecture_id": 123, "slot_idx": 0, "status": "failed"}
    )
    service._lecture_images_generator_service_instance = MagicMock(return_value=images_service)

    result = await service._handle_generate_lecture_slide(
        {
            "lecture_id": 123,
            "slot_idx": 0,
            "object_key": "TST100/images.json",
            "chunk_text": "first",
            "next_slide_payload": {"lecture_id": 123, "slot_idx": 1},
        }
    )

    assert result["status"] == "failed"
    assert repository_factory.job.created[0]["kind"] == "generate_lecture_slide"
    assert repository_factory.job.created[0]["payload"]["slot_idx"] == 1


@pytest.mark.asyncio
async def test_generate_lecture_slide_does_not_continue_stale_batch():
    repository_factory = FakeRepositoryFactory()
    service = JobService(repository_factory=repository_factory, logger=MagicMock())
    images_service = MagicMock()
    images_service.generate_lecture_slide = AsyncMock(
        return_value={
            "lecture_id": 123,
            "slot_idx": 0,
            "status": "skipped",
            "reason": "stale_batch",
        }
    )
    service._lecture_images_generator_service_instance = MagicMock(return_value=images_service)

    result = await service._handle_generate_lecture_slide(
        {
            "lecture_id": 123,
            "slot_idx": 0,
            "object_key": "TST100/images.json",
            "chunk_text": "first",
            "next_slide_payload": {"lecture_id": 123, "slot_idx": 1},
        }
    )

    assert result["reason"] == "stale_batch"
    assert repository_factory.job.created == []


@pytest.mark.asyncio
async def test_generate_tags_for_course_dispatches_to_tag_generator():
    repository_factory = FakeRepositoryFactory()
    service = JobService(repository_factory=repository_factory, logger=MagicMock())
    tags_service = MagicMock()
    tags_service.generate_tags_for_course = AsyncMock(
        return_value=[
            SimpleNamespace(id=1, slug="ethics", name="Ethics"),
            SimpleNamespace(id=2, slug="logic", name="Logic"),
        ]
    )
    service._tag_generator_service_instance = MagicMock(return_value=tags_service)

    handler = service._get_handler("generate_tags_for_course")
    assert handler is not None

    result = await handler({"course_id": 7})

    tags_service.generate_tags_for_course.assert_awaited_once_with(7)
    assert result == {
        "course_id": 7,
        "tags": [
            {"id": 1, "slug": "ethics", "name": "Ethics"},
            {"id": 2, "slug": "logic", "name": "Logic"},
        ],
    }


@pytest.mark.asyncio
async def test_generate_tags_for_course_requires_course_id():
    service = JobService(repository_factory=FakeRepositoryFactory(), logger=MagicMock())
    with pytest.raises(ValueError):
        await service._handle_generate_tags_for_course({})
