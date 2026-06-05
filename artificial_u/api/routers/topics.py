"""
Topic router for handling topic-related API endpoints.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from artificial_u.api.dependencies import (  # Will be created later
    ensure_student,
    get_repository_factory,
    get_topic_api_service,
)
from artificial_u.api.models.topics import (
    Topic,
    TopicCreate,
    TopicDraft,
    TopicGenerate,
    TopicGenerateSingle,
    TopicListResponse,
    TopicUpdate,
)
from artificial_u.api.security.auth0 import require_coins, require_role
from artificial_u.api.services.topic_service import TopicApiService
from artificial_u.config.settings import get_settings
from artificial_u.models.core import Student
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
    dependencies=[require_role("creator")],
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
    description="Update an existing topic. Only the creator or an admin can modify a topic.",
    responses={
        404: {"description": "Topic not found"},
        403: {"description": "Forbidden - user doesn't own this topic"},
    },
    dependencies=[require_role("creator")],
)
def update_topic(
    topic_data: TopicUpdate,
    topic_id: int = Path(..., description="The ID of the topic to update"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
    student: Student = Depends(ensure_student),
):
    """
    Update an existing topic's information.
    Requires ownership verification - only the topic creator or admin can update.
    """
    return topic_service.update_topic(topic_id, topic_data, student.id, student.role)


@router.delete(
    "/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete topic",
    description="Delete a topic by its ID. Only the creator or an admin can delete a topic.",
    responses={
        404: {"description": "Topic not found"},
        403: {"description": "Forbidden - user doesn't own this topic"},
    },
    dependencies=[require_role("creator")],
)
def delete_topic(
    topic_id: int = Path(..., description="The ID of the topic to delete"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
    student: Student = Depends(ensure_student),
):
    """
    Delete a specific topic.
    Requires ownership verification - only the topic creator or admin can delete.
    """
    topic_service.delete_topic(topic_id, student.id, student.role)
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
    dependencies=[require_coins(cost=get_settings().COIN_COST_TOPIC_GENERATION)],
)
async def generate_topics_for_course(
    course_id: int = Path(..., description="The ID of the course to generate topics for"),
    freeform_prompt: Optional[str] = Query(None, description="Optional prompt for generation"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
    student=Depends(ensure_student),
):
    """Generate and save topics for a given course ID."""
    # The API model TopicGenerate includes course_id, but path param is more RESTful here.
    # We can construct the TopicGenerate object in the service or pass params directly
    # if core service allows.
    # Current TopicApiService.generate_topics_for_course expects a TopicGenerate object.
    generation_data = TopicGenerate(course_id=course_id, freeform_prompt=freeform_prompt)
    return await topic_service.generate_topics_for_course(generation_data, created_by=student.id)


@course_topics_router.post(
    "/generate-single",
    response_model=TopicDraft,
    status_code=status.HTTP_200_OK,
    summary="Generate a single topic draft",
    description="Generates a single unsaved topic draft for a specific week/order slot.",
    dependencies=[require_coins(cost=get_settings().COIN_COST_TOPIC_GENERATION)],
)
async def generate_single_topic_for_course(
    generation_data: TopicGenerateSingle,
    course_id: int = Path(..., description="The ID of the course to generate a topic for"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
    student=Depends(ensure_student),
):
    """Generate a single topic draft for a given course slot."""
    return await topic_service.generate_topic_for_course_slot(
        course_id=course_id,
        generation_data=generation_data,
        created_by=student.id,
    )


@course_topics_router.post(
    "/generate/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue topic generation job",
    description=(
        "Enqueue an async job to generate topics for a course. Returns a job id to poll via "
        "GET /api/v1/jobs/{id}."
    ),
    dependencies=[require_coins(cost=get_settings().COIN_COST_TOPIC_GENERATION)],
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


# Batch generation endpoints (admin-only)


def get_remaining_topic_ids(repository_factory: RepositoryFactory, topic) -> List[int]:
    """
    Returns a list of topic IDs from this topic forward (sorted by week and order).

    Args:
        repository_factory: Repository factory for database access
        topic: The starting topic object

    Returns:
        List of topic IDs for remaining topics (same week/order or later)
    """
    all_topics = repository_factory.topic.list_by_course(topic.course_id)
    remaining = [
        t.id
        for t in sorted(all_topics, key=lambda t: (t.week, t.order))
        if (t.week > topic.week) or (t.week == topic.week and t.order >= topic.order)
    ]
    return remaining


def get_remaining_topic_ids_with_lectures(
    repository_factory: RepositoryFactory, topic
) -> List[int]:
    """
    Returns a list of topic IDs from this topic forward (sorted), only including topics that have lectures.

    Args:
        repository_factory: Repository factory for database access
        topic: The starting topic object

    Returns:
        List of topic IDs for remaining topics that have lectures
    """
    all_topics = repository_factory.topic.list_by_course(topic.course_id)
    remaining_topics = [
        t
        for t in sorted(all_topics, key=lambda t: (t.week, t.order))
        if (t.week > topic.week) or (t.week == topic.week and t.order >= topic.order)
    ]

    topic_ids_with_lectures = []
    for t in remaining_topics:
        lectures = repository_factory.lecture.list_by_topic(t.id)
        if lectures:
            topic_ids_with_lectures.append(t.id)

    return topic_ids_with_lectures


def get_remaining_topic_ids_with_audio(repository_factory: RepositoryFactory, topic) -> List[int]:
    """
    Returns a list of topic IDs from this topic forward (sorted), only including topics whose
    latest lecture has an audio_url (required for timeline generation).

    Notes:
    - Topics with no lecture are skipped.
    - Topics whose lecture has no audio_url are skipped.
    - Topics whose lecture already has a timeline_url are still included (this endpoint regenerates).
    """
    all_topics = repository_factory.topic.list_by_course(topic.course_id)
    remaining_topics = [
        t
        for t in sorted(all_topics, key=lambda t: (t.week, t.order))
        if (t.week > topic.week) or (t.week == topic.week and t.order >= topic.order)
    ]

    topic_ids_with_audio: List[int] = []
    for t in remaining_topics:
        lectures = repository_factory.lecture.list_by_topic(t.id)
        if not lectures:
            continue
        lecture = lectures[0]
        if getattr(lecture, "audio_url", None):
            topic_ids_with_audio.append(t.id)

    return topic_ids_with_audio


@router.post(
    "/{topic_id}/generate-remaining-lectures",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate remaining lectures starting from this topic",
    description=(
        "Generate lectures for this topic and all subsequent topics in the course. "
        "Admin only. Jobs execute serially to maintain narrative continuity. "
        "Returns the first job; subsequent jobs are automatically chained."
    ),
    dependencies=[require_role("admin")],
)
def generate_remaining_lectures(
    topic_id: int = Path(..., description="The starting topic ID"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Generate lectures for this topic and all subsequent topics in the course.
    Executes serially, one at a time, to maintain narrative continuity.
    """
    # 1. Get the topic and validate
    topic = repository_factory.topic.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 2. Get all topics from this one forward (same week/order or later)
    remaining = get_remaining_topic_ids(repository_factory, topic)

    if not remaining:
        raise HTTPException(status_code=400, detail="No topics to generate lectures for")

    # 3. Create first job with follow_up chain
    first_topic_id = remaining[0]
    follow_up_ids = remaining[1:]

    payload: Dict[str, Any] = {
        "partial_attributes": {"topic_id": first_topic_id, "course_id": topic.course_id},
        "created_by": student.email,
    }

    if follow_up_ids:
        payload["follow_up"] = {
            "action": "generate_lecture",
            "remaining_topic_ids": follow_up_ids,
            "course_id": topic.course_id,
            "created_by": student.email,
            "partial_attributes": {"course_id": topic.course_id},
        }

    row = repository_factory.job.create(
        kind="generate_lecture",
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
        "total_topics": len(remaining),
        "message": f"Queued batch generation for {len(remaining)} lectures",
    }


@router.post(
    "/{topic_id}/regenerate-remaining-audio",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Regenerate audio for remaining lectures starting from this topic",
    description=(
        "Regenerate audio files for existing lectures from this topic forward. "
        "Admin only. Only processes topics that already have lectures. "
        "Jobs execute serially to respect API rate limits."
    ),
    dependencies=[require_role("admin")],
)
def regenerate_remaining_audio(
    topic_id: int = Path(..., description="The starting topic ID"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Regenerate audio files for existing lectures from this topic forward.
    Skips topics that don't have lectures.
    """
    # 1. Get the topic and validate
    topic = repository_factory.topic.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 2. Get all topics from this one forward and filter to only topics that have lectures
    topic_ids_with_lectures = get_remaining_topic_ids_with_lectures(repository_factory, topic)

    if not topic_ids_with_lectures:
        raise HTTPException(status_code=400, detail="No lectures found for these topics")

    # 3. Create first job with follow_up chain
    first_topic_id = topic_ids_with_lectures[0]
    follow_up_ids = topic_ids_with_lectures[1:]

    # Get the lecture for the first topic
    first_lectures = repository_factory.lecture.list_by_topic(first_topic_id)
    if not first_lectures:
        raise HTTPException(status_code=400, detail="No lecture found for first topic")

    payload: Dict[str, Any] = {
        "lecture_id": first_lectures[0].id,
        "topic_id": first_topic_id,
    }

    if follow_up_ids:
        payload["follow_up"] = {
            "action": "generate_lecture_audio",
            "remaining_topic_ids": follow_up_ids,
            "course_id": topic.course_id,
            "created_by": student.email,
        }

    row = repository_factory.job.create(
        kind="generate_lecture_audio",
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
        "total_lectures": len(topic_ids_with_lectures),
        "message": f"Queued batch audio regeneration for {len(topic_ids_with_lectures)} lectures",
    }


@router.post(
    "/{topic_id}/generate-remaining-timelines",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate remaining timelines starting from this topic",
    description=(
        "Generate (or regenerate) forced-alignment timelines for lectures from this topic forward. "
        "Admin only. Only processes topics whose latest lecture has audio. "
        "Lectures that already have timelines are regenerated. "
        "Jobs execute serially to respect API rate limits."
    ),
    dependencies=[require_role("admin")],
)
def generate_remaining_timelines(
    topic_id: int = Path(..., description="The starting topic ID"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    # 1. Get the topic and validate
    topic = repository_factory.topic.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 2. Get all topics from this one forward and filter to only topics that have lectures with audio
    topic_ids_with_audio = get_remaining_topic_ids_with_audio(repository_factory, topic)
    if not topic_ids_with_audio:
        raise HTTPException(status_code=400, detail="No lecture audio found for these topics")

    # 3. Create first job with follow_up chain (serial)
    first_topic_id = topic_ids_with_audio[0]
    follow_up_ids = topic_ids_with_audio[1:]

    first_lectures = repository_factory.lecture.list_by_topic(first_topic_id)
    if not first_lectures:
        raise HTTPException(status_code=400, detail="No lecture found for first topic")

    first_lecture = first_lectures[0]
    if not getattr(first_lecture, "audio_url", None):
        raise HTTPException(status_code=400, detail="First lecture has no audio")

    payload: Dict[str, Any] = {
        "lecture_id": first_lecture.id,
        "topic_id": first_topic_id,
    }

    if follow_up_ids:
        payload["follow_up"] = {
            "action": "generate_lecture_timeline",
            "remaining_topic_ids": follow_up_ids,
            "course_id": topic.course_id,
            "created_by": student.email,
        }

    row = repository_factory.job.create(
        kind="generate_lecture_timeline",
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
        "total_lectures": len(topic_ids_with_audio),
        "message": f"Queued batch timeline generation for {len(topic_ids_with_audio)} lectures",
    }


@router.post(
    "/{topic_id}/regenerate-remaining-lectures",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Fully regenerate remaining lectures (content + audio) starting from this topic",
    description=(
        "Completely regenerate lectures (content, summary, and audio) from this topic forward. "
        "Admin only. Overwrites existing lectures. "
        "Jobs execute serially to maintain narrative continuity."
    ),
    dependencies=[require_role("admin")],
)
def regenerate_remaining_lectures(
    topic_id: int = Path(..., description="The starting topic ID"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Fully regenerate all lectures from this topic forward.
    This will overwrite existing lectures with new content, summaries, and audio.
    """
    # 1. Get the topic and validate
    topic = repository_factory.topic.get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # 2. Get all topics from this one forward
    remaining = get_remaining_topic_ids(repository_factory, topic)

    if not remaining:
        raise HTTPException(status_code=400, detail="No topics to regenerate lectures for")

    # 3. Create first job with follow_up chain
    # Same as generate-remaining-lectures, but we're explicitly regenerating
    first_topic_id = remaining[0]
    follow_up_ids = remaining[1:]

    payload: Dict[str, Any] = {
        "partial_attributes": {"topic_id": first_topic_id, "course_id": topic.course_id},
        "created_by": student.email,
    }

    if follow_up_ids:
        payload["follow_up"] = {
            "action": "generate_lecture",
            "remaining_topic_ids": follow_up_ids,
            "course_id": topic.course_id,
            "created_by": student.email,
            "partial_attributes": {"course_id": topic.course_id},
        }

    row = repository_factory.job.create(
        kind="generate_lecture",
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
        "total_topics": len(remaining),
        "message": f"Queued batch regeneration for {len(remaining)} lectures",
    }
