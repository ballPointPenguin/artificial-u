from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from artificial_u.api.dependencies import get_repository_factory
from artificial_u.models.repositories.factory import RepositoryFactory

router = APIRouter(prefix="/jobs", tags=["jobs"])


class EnqueueJob(BaseModel):
    kind: str
    payload: Dict[str, Any]
    priority: int = 0
    max_attempts: int = 5


@router.post("")
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
    return {
        "id": row.id,
        "kind": row.kind,
        "status": row.status,
        "attempts": row.attempts,
        "max_attempts": row.max_attempts,
        "priority": row.priority,
        "run_after": row.run_after,
    }


@router.get("")
def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    rows = repo.list(status=status, limit=limit)
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
        }
        for r in rows
    ]


@router.get("/summary")
def jobs_summary(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    repo = repository_factory.job
    counts = repo.summary_counts()
    return {k: v for k, v in counts}


@router.get("/{job_id}")
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
