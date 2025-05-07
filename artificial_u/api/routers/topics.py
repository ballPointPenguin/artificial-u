"""
Topic router for handling topic-related API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import JSONResponse

from artificial_u.api.dependencies import get_topic_api_service  # Will be created later
from artificial_u.api.models.topics import (
    Topic,
    TopicCreate,
    TopicList,
    TopicsGenerate,
    TopicUpdate,
)
from artificial_u.api.services.topic_service import TopicApiService

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
)
def create_topic(
    topic_data: TopicCreate,
    topic_service: TopicApiService = Depends(get_topic_api_service),
):
    """Create a new topic for a course."""
    return topic_service.create_topic(topic_data)


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
    response_model=TopicList,
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
)
def delete_topic(
    topic_id: int = Path(..., description="The ID of the topic to delete"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
):
    """Delete a specific topic."""
    topic_service.delete_topic(topic_id)
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


# Note: Generation endpoint is often placed under the parent resource (courses)
# e.g., POST /courses/{course_id}/topics/generate
# This keeps individual topic CRUD under /topics/
# and course-specific batch operations like generation under /courses/{course_id}/topics/

router_for_course_topics = APIRouter(
    prefix="/courses/{course_id}/topics",
    tags=["topics", "courses"],
    responses={404: {"description": "Course or Topic not found"}},
)


@router_for_course_topics.post(
    "/generate",
    response_model=List[Topic],
    status_code=status.HTTP_200_OK,
    summary="Generate topics for a course",
    description="Generates a list of topics for a specified course using AI.",
)
async def generate_topics_for_course(
    course_id: int = Path(..., description="The ID of the course to generate topics for"),
    freeform_prompt: Optional[str] = Query(None, description="Optional prompt for generation"),
    topic_service: TopicApiService = Depends(get_topic_api_service),
):
    """Generate and save topics for a given course ID."""
    # The API model TopicsGenerate includes course_id, but path param is more RESTful here.
    # We can construct the TopicsGenerate object in the service or pass params directly
    # if core service allows.
    # Current TopicApiService.generate_topics_for_course expects a TopicsGenerate object.
    generation_data = TopicsGenerate(course_id=course_id, freeform_prompt=freeform_prompt)
    return await topic_service.generate_topics_for_course(generation_data)
