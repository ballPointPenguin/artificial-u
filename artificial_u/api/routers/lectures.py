"""
Lecture router for handling lecture-related API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from artificial_u.api.dependencies import get_lecture_api_service
from artificial_u.api.models.lectures import (
    Lecture,
    LectureCreate,
    LectureList,
    LectureUpdate,
)
from artificial_u.api.services.lecture_service import LectureApiService

# Create the router with dependencies that will be applied to all routes
router = APIRouter(
    prefix="/lectures",
    tags=["lectures"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_lecture_api_service)],
)


@router.get(
    "",
    response_model=LectureList,
    summary="List lectures",
    description="Get a paginated list of lectures with optional filtering.",
)
async def list_lectures(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    course_id: Optional[int] = Query(None, description="Filter by course ID"),
    professor_id: Optional[int] = Query(None, description="Filter by professor ID"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Get a paginated list of lectures with filtering options.

    - **page**: Page number (starting from 1)
    - **size**: Number of items per page (1-100)
    - **course_id**: Filter by course ID
    - **professor_id**: Filter by professor ID
    - **search**: Search in title and description
    """
    return lecture_service.get_lectures(
        page=page,
        size=size,
        course_id=course_id,
        professor_id=professor_id,
        search_query=search,
    )


@router.get(
    "/{lecture_id}",
    response_model=Lecture,
    summary="Get lecture by ID",
    description="Get detailed information about a specific lecture.",
    responses={404: {"description": "Lecture not found"}},
)
async def get_lecture(
    lecture_id: int = Path(..., description="The ID of the lecture to retrieve"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Get detailed information about a specific lecture.

    - **lecture_id**: The unique identifier of the lecture
    """
    lecture = lecture_service.get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lecture with ID {lecture_id} not found",
        )
    return lecture


@router.get(
    "/{lecture_id}/content",
    response_model=Lecture,
    summary="Get lecture content",
    description="Get the full text content of a specific lecture.",
    responses={404: {"description": "Lecture not found"}},
)
async def get_lecture_content(
    lecture_id: int = Path(..., description="The ID of the lecture"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Get the full text content of a specific lecture.

    - **lecture_id**: The unique identifier of the lecture
    """
    content = lecture_service.get_lecture_content(lecture_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lecture content with ID {lecture_id} not found",
        )
    return content


@router.get(
    "/{lecture_id}/audio",
    summary="Get lecture audio",
    description="Get the audio version of a specific lecture.",
    responses={
        404: {"description": "Lecture not found or has no audio"},
        307: {"description": "Temporary redirect to storage URL"},
    },
)
async def get_lecture_audio(
    lecture_id: int = Path(..., description="The ID of the lecture"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Get the audio version of a specific lecture.

    - **lecture_id**: The unique identifier of the lecture
    - Returns a redirect to the storage URL where the audio file is stored
    """
    audio_url = lecture_service.get_lecture_audio_url(lecture_id)
    if not audio_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio for lecture with ID {lecture_id} not found",
        )

    # If it's a storage URL (starting with http:// or https://), redirect to it
    if audio_url.startswith("http://") or audio_url.startswith("https://"):
        return JSONResponse(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            content={"url": audio_url},
            headers={"Location": audio_url},
        )

    # Audio URL exists but is not a valid URL - indicates an issue
    # (We no longer support local file paths here)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Audio URL for lecture {lecture_id} is invalid or not found.",
    )


@router.post(
    "",
    response_model=Lecture,
    status_code=status.HTTP_201_CREATED,
    summary="Create lecture",
    description="Create a new lecture.",
)
async def create_lecture(
    lecture_data: LectureCreate,
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Create a new lecture.

    - Request body contains all required lecture information
    - Returns the created lecture with its assigned ID
    """
    # Create lecture
    lecture = lecture_service.create_lecture(lecture_data)
    return lecture


@router.patch(
    "/{lecture_id}",
    response_model=Lecture,
    summary="Update lecture",
    description="Update an existing lecture.",
    responses={404: {"description": "Lecture not found"}},
)
async def update_lecture(
    lecture_data: LectureUpdate,
    lecture_id: int = Path(..., description="The ID of the lecture to update"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Update an existing lecture.

    - **lecture_id**: The unique identifier of the lecture to update
    - Request body contains the updated lecture information (all fields optional)
    - Returns the updated lecture
    """
    updated_lecture = lecture_service.update_lecture(lecture_id, lecture_data)
    if not updated_lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lecture with ID {lecture_id} not found",
        )
    return updated_lecture


@router.delete(
    "/{lecture_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete lecture",
    description="Delete a lecture.",
    responses={404: {"description": "Lecture not found"}},
)
async def delete_lecture(
    lecture_id: int = Path(..., description="The ID of the lecture to delete"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Delete a lecture.

    - **lecture_id**: The unique identifier of the lecture to delete
    - Returns no content on successful deletion
    """
    success = lecture_service.delete_lecture(lecture_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lecture with ID {lecture_id} not found",
        )
    return None


@router.get(
    "/{lecture_id}/content/download",
    summary="Download lecture content as text file",
    description="Download the full text content of a specific lecture as a text file.",
    responses={
        404: {"description": "Lecture not found"},
        200: {"content": {"text/plain": {}}},
    },
)
async def download_lecture_content(
    lecture_id: int = Path(..., description="The ID of the lecture"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Download the full text content of a specific lecture as a text file.

    - **lecture_id**: The unique identifier of the lecture
    - Returns the lecture content as plain text
    """
    # Get the lecture details including title
    lecture = lecture_service.get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lecture with ID {lecture_id} not found",
        )

    # Get content
    content = lecture_service.get_lecture_content(lecture_id)
    if not content or not content.content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content for lecture with ID {lecture_id} not found",
        )

    # Return the content directly as a string
    return content.content
