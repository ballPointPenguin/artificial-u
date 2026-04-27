from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.services.job_service import JobService


class FakeJobRepository:
    def __init__(self):
        self.created = []

    def create(self, *, kind, payload, priority=0, run_after=None, max_attempts=2):
        row = SimpleNamespace(id=len(self.created) + 1)
        self.created.append(
            {
                "kind": kind,
                "payload": payload,
                "priority": priority,
                "run_after": run_after,
                "max_attempts": max_attempts,
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

    result = await service._handle_generate_lecture_images(
        {"lecture_id": 123, "slide_priority": -20}
    )

    assert result["enqueued"] == 1
    assert result["chain_remaining"] == 2
    assert result["slide_job_ids"] == [1]
    assert len(repository_factory.job.created) == 1

    created = repository_factory.job.created[0]
    assert created["kind"] == "generate_lecture_slide"
    assert created["priority"] == -20
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
            "slide_priority": -20,
            "next_slide_payload": {
                "lecture_id": 123,
                "slot_idx": 1,
                "object_key": "TST100/images.json",
                "chunk_text": "second",
                "slide_priority": -20,
            },
        }
    )

    assert result["next_slide_job_id"] == 1
    assert len(repository_factory.job.created) == 1
    created = repository_factory.job.created[0]
    assert created["kind"] == "generate_lecture_slide"
    assert created["priority"] == -20
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
    assert repository_factory.job.created == []
