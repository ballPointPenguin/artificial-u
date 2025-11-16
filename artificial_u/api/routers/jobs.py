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
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    rows = repo.list(
        status=status,
        limit=limit,
        kind=kind,
        lecture_id=lecture_id,
        topic_id=topic_id,
    )
    return [
        {
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
        }
        for r in rows
    ]


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

    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Disable Nginx buffering
        "Content-Type": "text/event-stream",
    }

    # Pass the generator directly without wrapper
    generator = sse_stream(
        hub,
        request=None,  # Don't pass request to avoid disconnect issues
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
    return {
        "id": row.id,
        "kind": row.kind,
        "payload": row.payload,
        "status": row.status,
        "priority": row.priority,
        "run_after": row.run_after,
        "attempts": row.attempts,
        "max_attempts": row.max_attempts,
        "last_error": row.last_error,
        "result": row.result,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


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
