"""
Tag endpoints.

Public endpoint lists the tag vocabulary of a content-language universe with
published-course counts. Admin endpoint enqueues tag-generation backfill jobs.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from artificial_u.api.dependencies import get_repository_factory
from artificial_u.api.security.auth0 import require_role
from artificial_u.models.repositories import RepositoryFactory

router = APIRouter(prefix="/tags", tags=["Tags"])

TAGS_GENERATION_JOB_KIND = "generate_tags_for_course"


# --- Response Models --- #


class TagResponse(BaseModel):
    """A tag with its published-course count."""

    id: int
    slug: str = Field(..., description="URL-safe tag identifier, unique per language")
    name: str = Field(..., description="Display name in the tag's content language")
    language: str = Field(..., description="Content language of the tag (e.g., 'en', 'fr')")
    course_count: int = Field(..., description="Number of published courses carrying the tag")


class TagsListResponse(BaseModel):
    """List of tags ordered by course count descending."""

    items: List[TagResponse]


class TagsBackfillResponse(BaseModel):
    """Result of enqueueing tag-generation backfill jobs."""

    enqueued: int
    job_ids: List[int]


# --- Public Endpoints --- #


@router.get(
    "",
    response_model=TagsListResponse,
    summary="List tags",
    description=(
        "List the tag vocabulary of a content language with published-course "
        "counts, most-used first. Tags without published courses are omitted."
    ),
)
async def list_tags(
    language: str = Query("en", description="Content language sandbox (e.g., 'en', 'fr')"),
    q: Optional[str] = Query(None, description="Optional name prefix filter"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of tags"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    rows = repository_factory.tag.list_with_counts(language=language, q=q, limit=limit)
    return TagsListResponse(
        items=[
            TagResponse(
                id=tag.id,
                slug=tag.slug,
                name=tag.name,
                language=tag.language,
                course_count=count,
            )
            for tag, count in rows
        ]
    )


# --- Admin Endpoints --- #


@router.post(
    "/backfill/enqueue",
    response_model=TagsBackfillResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue tag generation for the course library",
    description=(
        "Admin-only. Enqueues one tag-generation job per published course "
        "without tags. Use force=true to re-tag all published courses. "
        "Poll job progress via GET /api/v1/jobs."
    ),
    dependencies=[require_role("admin")],
)
async def enqueue_tags_backfill(
    force: bool = Query(False, description="Re-tag courses that already have tags"),
    include_hidden: bool = Query(False, description="Also tag non-published courses"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    course_ids = repository_factory.tag.list_backfill_course_ids(
        force=force, include_hidden=include_hidden
    )
    job_ids = []
    for course_id in course_ids:
        row = repository_factory.job.create(
            kind=TAGS_GENERATION_JOB_KIND,
            payload={"course_id": course_id},
        )
        job_ids.append(row.id)
    return TagsBackfillResponse(enqueued=len(job_ids), job_ids=job_ids)
