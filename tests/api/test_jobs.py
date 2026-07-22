"""
Unit tests for the jobs API endpoints, mocking the repository factory.
"""

import datetime as dt
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from artificial_u.api.dependencies import get_repository_factory


def _job_row(job_id, *, kind="generate_lecture", status="done", payload=None, result=None):
    now = dt.datetime(2026, 7, 22, 12, 0, 0)
    return SimpleNamespace(
        id=job_id,
        kind=kind,
        status=status,
        attempts=1,
        max_attempts=2,
        priority=0,
        run_after=now,
        created_at=now,
        updated_at=now,
        last_error=None,
        payload=payload or {},
        result=result,
        parent_job_id=None,
    )


@pytest.fixture
def mock_repository_factory():
    from artificial_u.api.app import app

    factory = MagicMock()
    factory.preference.get_global.return_value = None
    factory.lecture.get.return_value = SimpleNamespace(course_id=7)
    factory.topic.get.return_value = SimpleNamespace(course_id=7)

    app.dependency_overrides[get_repository_factory] = lambda: factory
    yield factory
    app.dependency_overrides.pop(get_repository_factory, None)


@pytest.mark.unit
def test_list_jobs_envelope_and_has_more(client: TestClient, mock_repository_factory):
    """The list endpoint fetches limit+1 rows and reports has_more/next_before_id."""
    rows = [_job_row(i) for i in range(30, 19, -1)]  # 11 rows for limit=10
    mock_repository_factory.job.list.return_value = rows

    response = client.get("/api/v1/jobs?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["jobs"]) == 10
    assert data["has_more"] is True
    assert data["next_before_id"] == 21
    mock_repository_factory.job.list.assert_called_once_with(
        status=None,
        limit=11,
        kind=None,
        lecture_id=None,
        topic_id=None,
        course_id=None,
        parent_id=None,
        before_id=None,
    )


@pytest.mark.unit
def test_list_jobs_last_page(client: TestClient, mock_repository_factory):
    mock_repository_factory.job.list.return_value = [_job_row(3), _job_row(2)]

    response = client.get("/api/v1/jobs?limit=10")
    data = response.json()
    assert len(data["jobs"]) == 2
    assert data["has_more"] is False
    assert data["next_before_id"] is None


@pytest.mark.unit
def test_list_jobs_forwards_filters(client: TestClient, mock_repository_factory):
    mock_repository_factory.job.list.return_value = []

    response = client.get(
        "/api/v1/jobs?status=done&kind=generate_lecture_slide&before_id=100&limit=5"
    )
    assert response.status_code == 200
    mock_repository_factory.job.list.assert_called_once_with(
        status="done",
        limit=6,
        kind="generate_lecture_slide",
        lecture_id=None,
        topic_id=None,
        course_id=None,
        parent_id=None,
        before_id=100,
    )


@pytest.mark.unit
def test_audio_job_model_prefers_recorded_backend(client: TestClient, mock_repository_factory):
    """The tts backend recorded in the job result wins over the global default."""
    mock_repository_factory.job.list.return_value = [
        _job_row(1, kind="generate_lecture_audio", result={"tts_backend": "mistral"}),
        _job_row(2, kind="generate_lecture_audio", result=None),
    ]

    data = client.get("/api/v1/jobs").json()
    from artificial_u.config import get_settings

    assert data["jobs"][0]["model"] == "mistral"
    # Without a recorded backend the configured default still applies.
    expected_default = (get_settings().tts_backend or "").strip().lower() or None
    assert data["jobs"][1]["model"] == expected_default


@pytest.mark.unit
def test_job_model_payload_override(client: TestClient, mock_repository_factory):
    mock_repository_factory.job.list.return_value = [
        _job_row(1, payload={"model_name_override": "custom-model"}),
    ]

    data = client.get("/api/v1/jobs").json()
    assert data["jobs"][0]["model"] == "custom-model"


@pytest.mark.unit
def test_list_jobs_memoizes_preference_and_link_lookups(
    client: TestClient, mock_repository_factory
):
    """Preference and lecture->course lookups run once per request, not once per row."""
    payload = {"lecture_id": 5}
    mock_repository_factory.job.list.return_value = [
        _job_row(i, kind="generate_lecture", payload=payload) for i in range(10, 0, -1)
    ]

    response = client.get("/api/v1/jobs?limit=5")
    assert response.status_code == 200
    assert mock_repository_factory.preference.get_global.call_count == 1
    assert mock_repository_factory.lecture.get.call_count == 1
    assert response.json()["jobs"][0]["link_path"] == "/courses/7/lectures/5"


@pytest.mark.unit
def test_jobs_summary_returns_dashboard_stats(client: TestClient, mock_repository_factory):
    stats = {
        "counts": {"done": 5, "failed": 1},
        "avg_wait_seconds": 2.5,
        "failed_last_hour": 1,
        "window_hours": 24,
        "kinds_recent": [
            {
                "kind": "generate_lecture_slide",
                "count": 4,
                "avg_duration_ms": 63000.0,
                "p50_duration_ms": 60000.0,
            }
        ],
    }
    mock_repository_factory.job.dashboard_stats.return_value = stats

    response = client.get("/api/v1/jobs/summary")
    assert response.status_code == 200
    assert response.json() == stats
    mock_repository_factory.job.dashboard_stats.assert_called_once_with(window_hours=24)


@pytest.mark.unit
def test_jobs_summary_clamps_window(client: TestClient, mock_repository_factory):
    mock_repository_factory.job.dashboard_stats.return_value = {}

    client.get("/api/v1/jobs/summary?window_hours=9999")
    mock_repository_factory.job.dashboard_stats.assert_called_once_with(window_hours=168)
