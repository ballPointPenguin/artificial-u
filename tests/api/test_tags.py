"""
Unit tests for the tags API endpoints, mocking the repository factory.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.dependencies import get_repository_factory
from artificial_u.models.core import Tag


@pytest.fixture
def mock_repository_factory():
    """Mock the repository factory used directly by the tags router."""
    from artificial_u.api.app import app

    factory = MagicMock()
    factory.tag.list_with_counts.return_value = [
        (Tag(id=1, slug="machine-learning", name="Machine Learning", language="en"), 5),
        (Tag(id=2, slug="ethics", name="Ethics", language="en"), 3),
    ]
    factory.tag.list_backfill_course_ids.return_value = [10, 11, 12]

    created_jobs = []

    def create_job(
        *, kind, payload, priority=None, run_after=None, max_attempts=2, parent_job_id=None
    ):
        created_jobs.append({"kind": kind, "payload": payload})
        return SimpleNamespace(id=len(created_jobs))

    factory.job.create.side_effect = create_job
    factory.created_jobs = created_jobs

    app.dependency_overrides[get_repository_factory] = lambda: factory
    yield factory
    app.dependency_overrides.pop(get_repository_factory, None)


@pytest.mark.unit
def test_list_tags_public(client: TestClient, mock_repository_factory):
    """GET /tags is public and returns counts ordered by the repository."""
    response = client.get("/api/v1/tags?language=en&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert [item["slug"] for item in data["items"]] == ["machine-learning", "ethics"]
    assert data["items"][0]["course_count"] == 5
    assert data["items"][0]["language"] == "en"
    mock_repository_factory.tag.list_with_counts.assert_called_once_with(
        language="en", q=None, limit=50
    )


@pytest.mark.unit
def test_list_tags_prefix_filter(client: TestClient, mock_repository_factory):
    response = client.get("/api/v1/tags?q=mach")
    assert response.status_code == 200
    mock_repository_factory.tag.list_with_counts.assert_called_once_with(
        language="en", q="mach", limit=100
    )


@pytest.mark.unit
def test_backfill_enqueues_one_job_per_course(client: TestClient, mock_repository_factory):
    """Admin backfill enqueues a generate_tags_for_course job per course."""
    response = client.post("/api/v1/tags/backfill/enqueue")
    assert response.status_code == 202
    data = response.json()
    assert data["enqueued"] == 3
    assert data["job_ids"] == [1, 2, 3]
    kinds = {job["kind"] for job in mock_repository_factory.created_jobs}
    assert kinds == {"generate_tags_for_course"}
    payload_course_ids = [
        job["payload"]["course_id"] for job in mock_repository_factory.created_jobs
    ]
    assert payload_course_ids == [10, 11, 12]
    mock_repository_factory.tag.list_backfill_course_ids.assert_called_once_with(
        force=False, include_hidden=False
    )


@pytest.mark.unit
def test_backfill_force_flag_forwarded(client: TestClient, mock_repository_factory):
    response = client.post("/api/v1/tags/backfill/enqueue?force=true&include_hidden=true")
    assert response.status_code == 202
    mock_repository_factory.tag.list_backfill_course_ids.assert_called_once_with(
        force=True, include_hidden=True
    )


@pytest.mark.unit
def test_backfill_requires_auth(client: TestClient, mock_repository_factory):
    """Unauthenticated requests cannot trigger the backfill."""
    from fastapi import HTTPException, status

    from artificial_u.api.app import app
    from artificial_u.api.dependencies import ensure_student

    def mock_no_auth():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    app.dependency_overrides[ensure_student] = mock_no_auth
    try:
        response = client.post("/api/v1/tags/backfill/enqueue")
        assert response.status_code == 401
    finally:
        from tests.api.conftest import mock_ensure_student

        app.dependency_overrides[ensure_student] = mock_ensure_student


@pytest.mark.unit
def test_backfill_requires_admin_role(client: TestClient, mock_repository_factory):
    """A creator-role student is rejected by require_role('admin')."""
    from artificial_u.api.app import app
    from artificial_u.api.dependencies import ensure_student
    from artificial_u.models.core import Student

    def mock_creator():
        return Student(
            id=2,
            name="Creator",
            email="creator@example.com",
            auth0_sub="creator-123",
            role="creator",
            coins=10,
            is_active=True,
        )

    app.dependency_overrides[ensure_student] = mock_creator
    try:
        response = client.post("/api/v1/tags/backfill/enqueue")
        assert response.status_code == 403
    finally:
        from tests.api.conftest import mock_ensure_student

        app.dependency_overrides[ensure_student] = mock_ensure_student
