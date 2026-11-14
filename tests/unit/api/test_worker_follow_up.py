"""Unit tests for the worker's follow-up payload builders (batch chaining)."""

from types import SimpleNamespace

import pytest

from artificial_u.api.worker import Worker


class FakeLectureRepository:
    def __init__(self, lectures_by_topic):
        self._lectures_by_topic = lectures_by_topic

    def list_by_topic(self, topic_id):
        return self._lectures_by_topic.get(topic_id, [])


class FakeRepositoryFactory:
    def __init__(self, lectures_by_topic):
        self.lecture = FakeLectureRepository(lectures_by_topic)


def _make_worker(lectures_by_topic):
    return Worker(FakeRepositoryFactory(lectures_by_topic))


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_audio_payload_resolves_lecture_and_chains_remaining():
    worker = _make_worker({7: [SimpleNamespace(id=42)]})

    payload = await worker._build_audio_payload(
        next_topic_id=7,
        follow_up={"action": "generate_lecture_audio", "course_id": 3},
        new_remaining=[8, 9],
    )

    assert payload is not None
    assert payload["lecture_id"] == 42
    assert payload["topic_id"] == 7
    # The remaining topics are carried forward so the chain continues.
    assert payload["follow_up"]["remaining_topic_ids"] == [8, 9]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_audio_payload_no_follow_up_when_chain_complete():
    worker = _make_worker({7: [SimpleNamespace(id=42)]})

    payload = await worker._build_audio_payload(
        next_topic_id=7,
        follow_up={"action": "generate_lecture_audio", "course_id": 3},
        new_remaining=[],
    )

    assert payload == {"lecture_id": 42, "topic_id": 7}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_audio_payload_returns_none_without_course_id():
    worker = _make_worker({7: [SimpleNamespace(id=42)]})

    payload = await worker._build_audio_payload(
        next_topic_id=7,
        follow_up={"action": "generate_lecture_audio"},
        new_remaining=[8],
    )

    assert payload is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_audio_payload_returns_none_when_no_lecture_for_topic():
    worker = _make_worker({})

    payload = await worker._build_audio_payload(
        next_topic_id=7,
        follow_up={"action": "generate_lecture_audio", "course_id": 3},
        new_remaining=[8],
    )

    assert payload is None


async def _fail_job(exc: Exception, *, attempts: int = 1, max_attempts: int = 3):
    """Run the worker's failure handling for a job and return (repo, published events)."""
    from unittest.mock import AsyncMock, MagicMock

    worker = _make_worker({})
    worker._publish_event = AsyncMock()
    repo = MagicMock()

    await worker._handle_exception(
        repo, 7, "create_course", {}, attempts, max_attempts, exc, duration_ms=12
    )
    return repo, worker._publish_event


@pytest.mark.unit
@pytest.mark.asyncio
async def test_failed_job_with_attempts_left_is_requeued():
    repo, publish = await _fail_job(RuntimeError("provider timeout"))

    job_id, attempts, max_attempts = repo.mark_failed_or_retry.call_args.args
    assert (job_id, attempts, max_attempts) == (7, 1, 3)
    assert publish.call_args.args[2] == "queued"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_non_retryable_failure_fails_the_job_immediately():
    from artificial_u.utils import NonRetryableJobError

    repo, publish = await _fail_job(NonRetryableJobError("course created, topics were not"))

    # Reported as out of attempts, so the repository marks it failed instead of requeueing
    job_id, attempts, max_attempts = repo.mark_failed_or_retry.call_args.args
    assert (job_id, attempts, max_attempts) == (7, 3, 3)
    assert repo.mark_failed_or_retry.call_args.kwargs["last_error"].startswith("course created")
    assert publish.call_args.args[2] == "failed"
