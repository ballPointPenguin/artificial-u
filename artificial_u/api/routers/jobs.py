import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from artificial_u.api.dependencies import get_repository_factory
from artificial_u.api.events import JobEventHub, sse_stream
from artificial_u.api.security.auth0 import require_auth
from artificial_u.config import get_settings
from artificial_u.models.repositories.factory import RepositoryFactory

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _duration_ms_from_result(result: Any) -> Any:
    if not result or not isinstance(result, dict):
        return None
    telem = result.get("_job_telemetry")
    if not isinstance(telem, dict):
        return None
    d = telem.get("duration_ms")
    if d is None:
        return None
    try:
        return int(d)
    except (TypeError, ValueError):
        return None


def _tts_model_name(settings) -> Optional[str]:
    """Best-effort TTS model name for the configured backend."""
    backend = (settings.tts_backend or "").lower()
    if backend == "mistral":
        return settings.TTS_MISTRAL_MODEL
    if backend == "xai":
        # xAI's TTS endpoint does not expose a tunable model name; show the backend.
        return "xai"
    return settings.TTS_VOICE_MODEL


def _job_model_name(kind: str, payload: Any, factory=None) -> Optional[str]:
    """
    Best-effort model name for a job. Payload-level overrides take precedence,
    then global preference overrides (admin settings), then environment defaults.

    Note: per-professor / per-voice overrides applied at runtime are not resolved here.
    """
    payload = payload if isinstance(payload, dict) else {}
    override = payload.get("model_name_override")
    if override:
        return str(override)

    settings = get_settings()
    if kind == "generate_lecture_audio":
        return _tts_model_name(settings)

    # Map job kind to (preference_scope, settings_fallback)
    kind_map = {
        "generate_course": ("COURSE_GENERATION_MODEL", settings.COURSE_GENERATION_MODEL),
        "generate_department": ("DEPARTMENT_GENERATION_MODEL", settings.DEPARTMENT_GENERATION_MODEL),
        "generate_professor": ("PROFESSOR_GENERATION_MODEL", settings.PROFESSOR_GENERATION_MODEL),
        "generate_topics_for_course": ("TOPICS_GENERATION_MODEL", settings.TOPICS_GENERATION_MODEL),
        "generate_lecture": ("LECTURE_GENERATION_MODEL", settings.LECTURE_GENERATION_MODEL),
        "generate_lecture_text_only": ("LECTURE_GENERATION_MODEL", settings.LECTURE_GENERATION_MODEL),
        "generate_lecture_summary": ("LECTURE_SUMMARY_MODEL", settings.LECTURE_SUMMARY_MODEL),
        "generate_lecture_images": ("IMAGE_GENERATION_MODEL", settings.IMAGE_GENERATION_MODEL),
        "resume_lecture_images": ("IMAGE_GENERATION_MODEL", settings.IMAGE_GENERATION_MODEL),
        "generate_lecture_slide": ("IMAGE_GENERATION_MODEL", settings.IMAGE_GENERATION_MODEL),
        "remap_lecture_images_timeline": ("IMAGE_GENERATION_MODEL", settings.IMAGE_GENERATION_MODEL),
        "generate_professor_image": ("IMAGE_GENERATION_MODEL", settings.IMAGE_GENERATION_MODEL),
        "generate_course_image": ("IMAGE_GENERATION_MODEL", settings.IMAGE_GENERATION_MODEL),
    }

    entry = kind_map.get(kind)
    if entry is None:
        return None

    scope, default = entry
    if factory is not None:
        pref = factory.preference.get_global(scope)
        if pref:
            return pref.value

    return default


def _coerce_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    return None


def _job_link_path(payload: Any, result: Any, factory=None) -> Optional[str]:
    """
    Resolve a relative frontend path to the lecture or topic a job concerns.

    Prefers the lecture when both a lecture and topic are present. The lecture /
    topic detail routes are nested under a course, so a course id is required; it
    is taken from the payload/result when available and otherwise resolved via a
    single primary-key lookup.
    """
    payload = payload if isinstance(payload, dict) else {}
    result = result if isinstance(result, dict) else {}
    partial = payload.get("partial_attributes") if isinstance(payload, dict) else {}
    partial = partial if isinstance(partial, dict) else {}

    def _pick(key: str) -> Optional[int]:
        for source in (payload, partial, result):
            val = _coerce_int(source.get(key))
            if val is not None:
                return val
        return None

    lecture_id = _pick("lecture_id")
    topic_id = _pick("topic_id")
    course_id = _pick("course_id")

    if lecture_id is not None:
        if course_id is None and factory is not None:
            lecture = factory.lecture.get(lecture_id)
            course_id = getattr(lecture, "course_id", None)
        if course_id is not None:
            return f"/courses/{course_id}/lectures/{lecture_id}"

    if topic_id is not None:
        if course_id is None and factory is not None:
            topic = factory.topic.get(topic_id)
            course_id = getattr(topic, "course_id", None)
        if course_id is not None:
            return f"/courses/{course_id}/topics/{topic_id}"

    return None


def _job_row_response(r, factory=None) -> dict:
    return {
        "id": r.id,
        "kind": r.kind,
        "status": r.status,
        "attempts": r.attempts,
        "max_attempts": r.max_attempts,
        "priority": r.priority,
        "run_after": r.run_after,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
        "last_error": r.last_error,
        "payload": r.payload,
        "result": r.result,
        "duration_ms": _duration_ms_from_result(r.result),
        "parent_job_id": getattr(r, "parent_job_id", None),
        "model": _job_model_name(r.kind, r.payload, factory),
        "link_path": _job_link_path(r.payload, r.result, factory),
    }


def _active_job_snapshot(
    factory,
    *,
    lecture_id: Optional[int],
    topic_id: Optional[int],
    kinds: list[str],
    limit_per_status: int = 100,
) -> list[dict]:
    repo = factory.job
    kinds_set = set(kinds)
    rows = []
    for status in ("queued", "running"):
        rows.extend(
            repo.list(
                status=status,
                limit=limit_per_status,
                lecture_id=lecture_id,
                topic_id=topic_id,
            )
        )
    if kinds_set:
        rows = [row for row in rows if row.kind in kinds_set]
    rows.sort(key=lambda row: row.created_at, reverse=True)
    return [_job_row_response(row, factory) for row in rows]


class EnqueueJob(BaseModel):
    kind: str
    payload: Dict[str, Any]
    # When omitted, the priority is derived from the job kind (see job_priorities).
    priority: Optional[int] = None
    max_attempts: int = 2


async def _publish_job_event(request: Request, event: Dict[str, Any]) -> None:
    """Best-effort publish of a job event to the SSE hub.

    Reads the hub from app state (the same place ``jobs_stream`` uses) and awaits
    the publish on the running event loop. Never raises: SSE delivery is
    non-critical and must not fail the request.
    """
    hub: Optional[JobEventHub] = getattr(request.app.state, "job_events", None)
    if hub is None:
        return
    try:
        await hub.publish(event)
    except Exception:  # noqa: BLE001
        logging.getLogger(__name__).debug("Failed to publish job event", exc_info=True)


@router.post("", dependencies=[Depends(require_auth)])
async def enqueue(
    job: EnqueueJob,
    request: Request,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    row = await asyncio.to_thread(
        repo.create,
        kind=job.kind,
        payload=job.payload,
        priority=job.priority,
        max_attempts=job.max_attempts,
    )
    await _publish_job_event(
        request,
        {
            "id": row.id,
            "kind": row.kind,
            "status": "queued",
            "payload": row.payload,
        },
    )

    return {
        "id": row.id,
        "kind": row.kind,
        "status": row.status,
        "attempts": row.attempts,
        "max_attempts": row.max_attempts,
        "priority": row.priority,
        "run_after": row.run_after,
    }


@router.get("", dependencies=[Depends(require_auth)])
def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    kind: Optional[str] = None,
    lecture_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    course_id: Optional[int] = None,
    parent_id: Optional[int] = None,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    rows = repo.list(
        status=status,
        limit=limit,
        kind=kind,
        lecture_id=lecture_id,
        topic_id=topic_id,
        course_id=course_id,
        parent_id=parent_id,
    )
    return [_job_row_response(r, repository_factory) for r in rows]


@router.get("/summary", dependencies=[Depends(require_auth)])
def jobs_summary(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    counts = repo.summary_counts()
    return {k: v for k, v in counts}


@router.get("/stream")
async def jobs_stream(
    request: Request,
    lecture_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """SSE stream for job events.

    Query params:
      - kinds: can be provided multiple times (kinds=a&kinds=b) or once (kinds=a).
      - access_token: JWT access token for authentication (query param for SSE compatibility)
    """
    # Check for access token in query params (for SSE compatibility)
    access_token = request.query_params.get("access_token")
    if access_token:
        # Validate the token
        try:
            require_auth(HTTPAuthorizationCredentials(scheme="Bearer", credentials=access_token))
            # Token is valid, continue
        except Exception:
            raise HTTPException(401, "Invalid access token")
    else:
        # No token provided, require auth header
        try:
            require_auth(HTTPAuthorizationCredentials(scheme="Bearer", credentials=""))
        except Exception:
            raise HTTPException(401, "Authentication required")

    # Parse kinds robustly to avoid validation quirks
    kinds_list = request.query_params.getlist("kinds")
    hub: JobEventHub = request.app.state.job_events
    snapshot = await asyncio.to_thread(
        _active_job_snapshot,
        repository_factory,
        lecture_id=lecture_id,
        topic_id=topic_id,
        kinds=kinds_list,
    )

    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Disable Nginx buffering
        "Content-Type": "text/event-stream",
    }

    # Pass the generator directly without wrapper
    generator = sse_stream(
        hub,
        request=request,
        initial_snapshot=snapshot,
        lecture_id=lecture_id,
        topic_id=topic_id,
        kinds=kinds_list,
    )

    return StreamingResponse(generator, media_type="text/event-stream", headers=headers)


@router.get("/{job_id}", dependencies=[Depends(require_auth)])
def get_job(
    job_id: int,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    row = repo.get(job_id)
    if not row:
        raise HTTPException(404, "job not found")
    return _job_row_response(row, repository_factory)


@router.get("/{job_id}/children", dependencies=[Depends(require_auth)])
def get_job_children(
    job_id: int,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    if not repo.get(job_id):
        raise HTTPException(404, "job not found")
    rows = repo.list(parent_id=job_id, limit=200)
    return [_job_row_response(r, repository_factory) for r in rows]


@router.post("/{job_id}/cancel", dependencies=[Depends(require_auth)])
async def cancel_job(
    job_id: int,
    request: Request,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    row = await asyncio.to_thread(repo.get, job_id)
    if not row:
        raise HTTPException(404, "job not found")
    if row.status in ("done", "failed", "cancelled"):
        return {"id": row.id, "status": row.status}

    # Set status to cancelled
    await asyncio.to_thread(repo.mark_cancelled, job_id)

    await _publish_job_event(
        request,
        {
            "id": job_id,
            "kind": row.kind,
            "status": "cancelled",
            "payload": row.payload or {},
        },
    )

    return {"id": job_id, "status": "cancelled"}
