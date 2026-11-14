"""Shared helpers for job-related API responses."""

from typing import Any, Dict


def job_summary(row: Any) -> Dict[str, Any]:
    """Return the queue-state fields of a job row, as sent back when a job is enqueued."""
    return {
        "id": row.id,
        "kind": row.kind,
        "status": row.status,
        "attempts": row.attempts,
        "max_attempts": row.max_attempts,
        "priority": row.priority,
        "run_after": row.run_after,
    }
