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
