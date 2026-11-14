"""Tests for the batch lecture generation endpoints on topics."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.dependencies import get_repository_factory


def _topic(topic_id, week, order):
    return SimpleNamespace(id=topic_id, course_id=5, week=week, order=order)


@pytest.fixture
def repository_factory():
    from artificial_u.api.app import app

    factory = MagicMock()
    topics = [_topic(1, 1, 1), _topic(2, 1, 2), _topic(3, 2, 1)]
    factory.topic.get.side_effect = lambda topic_id: next(
        (t for t in topics if t.id == topic_id), None
    )
    factory.topic.list_by_course.return_value = list(reversed(topics))
    factory.job.create.return_value = SimpleNamespace(
        id=77,
        kind="generate_lecture",
        status="queued",
        attempts=0,
        max_attempts=2,
        priority=0,
        run_after=None,
    )

    app.dependency_overrides[get_repository_factory] = lambda: factory
    yield factory
    app.dependency_overrides.pop(get_repository_factory, None)


@pytest.mark.unit
@pytest.mark.parametrize(
    "action,verb",
    [
        ("generate-remaining-lectures", "generation"),
        ("regenerate-remaining-lectures", "regeneration"),
    ],
)
def test_batch_lecture_chain_starts_at_topic_and_carries_creator(
    client: TestClient, repository_factory, action, verb
):
    response = client.post(f"/api/v1/topics/2/{action}")

    assert response.status_code == 202
    data = response.json()
    assert data["id"] == 77
    assert data["total_topics"] == 2
    assert data["message"] == f"Queued batch {verb} for 2 lectures"

    kwargs = repository_factory.job.create.call_args.kwargs
    assert kwargs["kind"] == "generate_lecture"
    payload = kwargs["payload"]
    # Starts at the requested topic and chains the later one; the earlier topic is skipped
    assert payload["partial_attributes"] == {"topic_id": 2, "course_id": 5, "created_by": 1}
    assert payload["follow_up"]["remaining_topic_ids"] == [3]
    # The creator's student ID travels with every lecture in the chain
    assert payload["follow_up"]["partial_attributes"] == {"course_id": 5, "created_by": 1}


@pytest.mark.unit
def test_batch_lecture_chain_unknown_topic(client: TestClient, repository_factory):
    response = client.post("/api/v1/topics/999/generate-remaining-lectures")

    assert response.status_code == 404
    repository_factory.job.create.assert_not_called()
