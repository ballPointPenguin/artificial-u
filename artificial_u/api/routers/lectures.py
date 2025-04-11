"""
Lecture router for handling lecture-related API endpoints.
"""

import os
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Path,
    status,
)
from fastapi.responses import JSONResponse, FileResponse

from artificial_u.models.database import Repository
from artificial_u.api.services.lecture_service import LectureApiService
from artificial_u.api.config import get_settings, Settings
from artificial_u.api.models.lectures import (
    LectureCreate,
    LectureUpdate,
    Lecture,
    LectureList,
)


router = APIRouter(
    prefix="/lectures",
    tags=["lectures"],
    responses={404: {"description": "Not found"}},
)


def get_repository(settings: Settings = Depends(get_settings)) -> Repository:
    """Dependency for getting repository instance."""
    return Repository(db_url=settings.DATABASE_URL)


def get_lecture_service(
    repository: Repository = Depends(get_repository),
) -> LectureApiService:
    """Dependency for getting lecture service."""
    return LectureApiService(repository)


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
    service: LectureApiService = Depends(get_lecture_service),
):
    """
    Get a paginated list of lectures with filtering options.

    - **page**: Page number (starting from 1)
    - **size**: Number of items per page (1-100)
    - **course_id**: Filter by course ID
    - **professor_id**: Filter by professor ID
    - **search**: Search in title and description
    """
    return service.get_lectures(
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
    service: LectureApiService = Depends(get_lecture_service),
):
    """
    Get detailed information about a specific lecture.

    - **lecture_id**: The unique identifier of the lecture
    """
    lecture = service.get_lecture(lecture_id)
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
    service: LectureApiService = Depends(get_lecture_service),
):
    """
    Get the full text content of a specific lecture.

    - **lecture_id**: The unique identifier of the lecture
    """
    content = service.get_lecture_content(lecture_id)
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
    service: LectureApiService = Depends(get_lecture_service),
):
    """
    Get the audio version of a specific lecture.

    - **lecture_id**: The unique identifier of the lecture
    - Returns a redirect to the storage URL where the audio file is stored
    """
    audio_path = service.get_lecture_audio_path(lecture_id)
    if not audio_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio for lecture with ID {lecture_id} not found",
        )

    # If it's a storage URL (starting with http:// or https://), redirect to it
    if audio_path.startswith("http://") or audio_path.startswith("https://"):
        return JSONResponse(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            content={"url": audio_path},
            headers={"Location": audio_path},
        )

    # Otherwise treat it as a local file path - this is for backward compatibility
    # This branch should be removed in the future as all audio should be in storage
    if os.path.exists(audio_path):
        return FileResponse(
            audio_path,
            media_type="audio/mpeg",
            filename=f"lecture_{lecture_id}.mp3",
        )

    # If we get here, the path is invalid
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Audio file for lecture with ID {lecture_id} not found at path {audio_path}",
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
    service: LectureApiService = Depends(get_lecture_service),
):
    """
    Create a new lecture.

    - Request body contains all required lecture information
    - Returns the created lecture with its assigned ID
    """
    # Create lecture
    lecture = service.create_lecture(lecture_data)
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
    service: LectureApiService = Depends(get_lecture_service),
):
    """
    Update an existing lecture.

    - **lecture_id**: The unique identifier of the lecture to update
    - Request body contains the updated lecture information (all fields optional)
    - Returns the updated lecture
    """
    updated_lecture = service.update_lecture(lecture_id, lecture_data)
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
    service: LectureApiService = Depends(get_lecture_service),
):
    """
    Delete a lecture.

    - **lecture_id**: The unique identifier of the lecture to delete
    - Returns no content on successful deletion
    """
    success = service.delete_lecture(lecture_id)
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
    service: LectureApiService = Depends(get_lecture_service),
):
    """
    Download the full text content of a specific lecture as a text file.

    - **lecture_id**: The unique identifier of the lecture
    - Returns the text content as a downloadable file
    """
    # Ensure lecture exists
    lecture = service.get_lecture(lecture_id)
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lecture with ID {lecture_id} not found",
        )

    # Ensure content asset file exists (lazy generation)
    asset_path = await service.ensure_content_asset_exists(lecture_id)
    if not asset_path or not os.path.exists(asset_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to generate content file for lecture with ID {lecture_id}",
        )

    # Return the file for download
    return FileResponse(
        asset_path,
        media_type="text/plain",
        filename=f"lecture_{lecture_id}_{lecture.title.replace(' ', '_')}.txt",
    )
