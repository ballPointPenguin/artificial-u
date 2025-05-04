"""
Lecture router for handling lecture-related API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse, PlainTextResponse

from artificial_u.api.dependencies import get_lecture_api_service
from artificial_u.api.models import (
    Lecture,
    LectureCreate,
    LectureGenerate,
    LectureList,
    LectureUpdate,
)
from artificial_u.api.services import LectureApiService

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
    return lecture_service.list_lectures(
        page=page,
        size=size,
        course_id=course_id,
        professor_id=professor_id,
        search=search,
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
    response_class=PlainTextResponse,
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
    """
    content = lecture_service.get_lecture_content(lecture_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content for lecture with ID {lecture_id} not found",
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

    # If audio_url exists but is not a valid http/https url, treat as not found/invalid
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
    responses={
        404: {"description": "Lecture not found"},
        400: {"description": "Failed due to database issue (e.g., constraints)"},
    },
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
            detail=f"Lecture with ID {lecture_id} not found (delete operation failed).",
        )
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@router.get(
    "/{lecture_id}/content/download",
    response_class=PlainTextResponse,
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
    content = lecture_service.get_lecture_content(lecture_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content for lecture with ID {lecture_id} not found",
        )

    # Return the content string directly
    return content


@router.post(
    "/generate",
    response_model=Lecture,
    status_code=status.HTTP_200_OK,
    summary="Generate lecture data",
    description="Generates lecture data using AI based on partial attributes.",
    responses={
        500: {"description": "Lecture generation failed"},
    },
)
async def generate_lecture(
    generation_data: LectureGenerate,
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Generate lecture data using AI.

    Accepts optional partial attributes and a freeform prompt to guide generation.

    Args:
        generation_data: Contains optional partial_attributes and freeform_prompt.

    Returns:
        The generated lecture data (not saved to the database).
    """
    return await lecture_service.generate_lecture(generation_data)
