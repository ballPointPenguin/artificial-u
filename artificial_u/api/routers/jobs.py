import asyncio
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from artificial_u.api.dependencies import get_repository_factory
from artificial_u.api.events import JobEventHub, sse_stream
from artificial_u.api.security.auth0 import require_auth
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
    except TypeError, ValueError:
        return None


def _job_row_response(r) -> dict:
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
    }


def _active_job_snapshot(
    repo,
    *,
    lecture_id: Optional[int],
    topic_id: Optional[int],
    kinds: list[str],
    limit_per_status: int = 100,
) -> list[dict]:
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
    return [_job_row_response(row) for row in rows]


class EnqueueJob(BaseModel):
    kind: str
    payload: Dict[str, Any]
    priority: int = 0
    max_attempts: int = 2


@router.post("", dependencies=[Depends(require_auth)])
def enqueue(
    job: EnqueueJob,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    row = repo.create(
        kind=job.kind,
        payload=job.payload,
        priority=job.priority,
        max_attempts=job.max_attempts,
    )
    # Publish queued event to SSE hub (best-effort)
    try:
        # Attempt to access global app instance for event hub
        # FastAPI doesn't inject app here, so we import the app and use its state
        from artificial_u.api.app import app  # type: ignore

        hub = getattr(app.state, "job_events", None)
        if hub is not None:
            # Publish synchronously; hub.publish is async, schedule and forget
            import asyncio

            asyncio.create_task(
                hub.publish(
                    {
                        "id": row.id,
                        "kind": row.kind,
                        "status": "queued",
                        "payload": row.payload,
                    }
                )
            )
    except Exception:
        # Never fail the enqueue API due to SSE publish errors
        pass

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
    return [_job_row_response(r) for r in rows]


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
        repository_factory.job,
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
    return _job_row_response(row)


@router.get("/{job_id}/children", dependencies=[Depends(require_auth)])
def get_job_children(
    job_id: int,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    if not repo.get(job_id):
        raise HTTPException(404, "job not found")
    rows = repo.list(parent_id=job_id, limit=200)
    return [_job_row_response(r) for r in rows]


@router.post("/{job_id}/cancel", dependencies=[Depends(require_auth)])
def cancel_job(
    job_id: int,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    row = repo.get(job_id)
    if not row:
        raise HTTPException(404, "job not found")
    if row.status in ("done", "failed", "cancelled"):
        return {"id": row.id, "status": row.status}

    # Set status to cancelled
    repo.mark_cancelled(job_id)

    # Publish cancelled event
    try:
        from artificial_u.api.app import app  # type: ignore

        hub = getattr(app.state, "job_events", None)
        if hub is not None:
            import asyncio

            asyncio.create_task(
                hub.publish(
                    {
                        "id": job_id,
                        "kind": row.kind,
                        "status": "cancelled",
                        "payload": row.payload or {},
                    }
                )
            )
    except Exception:
        pass

    return {"id": job_id, "status": "cancelled"}
