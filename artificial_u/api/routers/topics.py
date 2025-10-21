"""
Topic router for handling topic-related API endpoints.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query, status

from artificial_u.api.dependencies import (  # Will be created later
    ensure_student,
    get_repository_factory,
    get_topic_api_service,
)
from artificial_u.api.models.topics import (
    Topic,
    TopicCreate,
    TopicGenerate,
    TopicListResponse,
    TopicUpdate,
)
from artificial_u.api.security.auth0 import require_auth
from artificial_u.api.services.topic_service import TopicApiService
from artificial_u.models.repositories.factory import RepositoryFactory

router = APIRouter(
    prefix="/topics",
    tags=["topics"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "",
    response_model=Topic,
    status_code=status.HTTP_201_CREATED,
    summary="Create topic",
    description="Create a new topic.",
    dependencies=[Depends(require_auth)],
)
def create_topic(
    topic_data: TopicCreate,
    topic_service: TopicApiService = Depends(get_topic_api_service),
    student=Depends(ensure_student),
):
    """Create a new topic for a course."""
    return topic_service.create_topic(topic_data, created_by=student.id)


@router.get(
    "/{topic_id}",
    response_model=Topic,
    summary="Get topic by ID",
    description="Get detailed information about a specific topic.",
)
def get_topic(
    topic_id: int = Path(..., description="The ID of the topic to retrieve"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
):
    """Get a specific topic by its ID."""
    return topic_service.get_topic(topic_id)


@router.get(
    "",
    response_model=TopicListResponse,
    summary="List topics by course",
    description="Get a paginated list of topics, primarily filtered by course ID.",
)
def list_topics_by_course(
    course_id: int = Query(..., description="Filter topics by this course ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
):
    """Retrieve topics for a given course with pagination."""
    return topic_service.list_topics_by_course(course_id=course_id, page=page, size=size)


@router.patch(
    "/{topic_id}",
    response_model=Topic,
    summary="Update topic",
    description="Update an existing topic.",
    dependencies=[Depends(require_auth)],
)
def update_topic(
    topic_data: TopicUpdate,
    topic_id: int = Path(..., description="The ID of the topic to update"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
):
    """Update an existing topic's information."""
    return topic_service.update_topic(topic_id, topic_data)


@router.delete(
    "/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete topic",
    description="Delete a topic by its ID.",
    dependencies=[Depends(require_auth)],
)
def delete_topic(
    topic_id: int = Path(..., description="The ID of the topic to delete"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
):
    """Delete a specific topic."""
    topic_service.delete_topic(topic_id)
    # For 204 No Content, we should not return any response body
    # FastAPI will handle the 204 status code automatically based on the decorator


# Note: Generation endpoint is often placed under the parent resource (courses)
# e.g., POST /courses/{course_id}/topics/generate
# This keeps individual topic CRUD under /topics/
# and course-specific batch operations like generation under /courses/{course_id}/topics/

course_topics_router = APIRouter(
    prefix="/courses/{course_id}/topics",
    tags=["topics", "courses"],
    responses={404: {"description": "Course or Topic not found"}},
)


@course_topics_router.post(
    "/generate",
    response_model=List[Topic],
    status_code=status.HTTP_200_OK,
    summary="Generate topics for a course",
    description="Generates a list of topics for a specified course using AI.",
    dependencies=[Depends(require_auth)],
)
async def generate_topics_for_course(
    course_id: int = Path(..., description="The ID of the course to generate topics for"),
    freeform_prompt: Optional[str] = Query(None, description="Optional prompt for generation"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
):
    """Generate and save topics for a given course ID."""
    # The API model TopicGenerate includes course_id, but path param is more RESTful here.
    # We can construct the TopicGenerate object in the service or pass params directly
    # if core service allows.
    # Current TopicApiService.generate_topics_for_course expects a TopicGenerate object.
    generation_data = TopicGenerate(course_id=course_id, freeform_prompt=freeform_prompt)
    return await topic_service.generate_topics_for_course(generation_data)


@course_topics_router.post(
    "/generate/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue topic generation job",
    description=(
        "Enqueue an async job to generate topics for a course. Returns a job id to poll via "
        "GET /api/v1/jobs/{id}."
    ),
    dependencies=[Depends(require_auth)],
)
async def enqueue_generate_topics_for_course(
    course_id: int = Path(..., description="The ID of the course to generate topics for"),
    freeform_prompt: Optional[str] = Query(None, description="Optional prompt for generation"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    payload: Dict[str, Any] = {"course_id": course_id}
    if freeform_prompt:
        payload["freeform_prompt"] = freeform_prompt
    row = repository_factory.job.create(
        kind="generate_topics_for_course",
        payload=payload,
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
