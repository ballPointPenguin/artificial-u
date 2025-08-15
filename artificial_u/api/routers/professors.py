"""
Professor router for handling professor-related API endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from artificial_u.api.dependencies import get_professor_api_service, get_repository_factory
from artificial_u.api.models import (
    ProfessorCoursesResponse,
    ProfessorCreate,
    ProfessorGenerate,
    ProfessorLecturesResponse,
    ProfessorResponse,
    ProfessorsListResponse,
    ProfessorUpdate,
)
from artificial_u.api.services import ProfessorApiService
from artificial_u.models.repositories.factory import RepositoryFactory

# Create the router with dependencies that will be applied to all routes
router = APIRouter(
    prefix="/professors",
    tags=["professors"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/featured",
    response_model=List[ProfessorResponse],
    summary="Get featured professors",
    description="Get a list of up to 3 randomly selected featured professors.",
)
async def get_featured_professors(
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Get up to 3 featured professors.
    The selection is random for this version.
    """
    return service.get_featured_professors()


@router.get(
    "",
    response_model=ProfessorsListResponse,
    summary="List professors",
    description="Get a paginated list of professors with optional filtering.",
)
async def list_professors(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    specialization: Optional[str] = Query(
        None, description="Filter by specialization (partial match)"
    ),
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Get a paginated list of professors with filtering options.

    - **page**: Page number (starting from 1)
    - **size**: Number of items per page (1-100)
    - **department_id**: Filter by department ID (exact match)
    - **name**: Filter by professor name (partial match)
    - **specialization**: Filter by specialization (partial match)
    """
    return service.get_professors(
        page=page,
        size=size,
        department_id=department_id,
        name=name,
        specialization=specialization,
    )


@router.get(
    "/{professor_id}",
    response_model=ProfessorResponse,
    summary="Get professor by ID",
    description="Get detailed information about a specific professor.",
    responses={404: {"description": "Professor not found"}},
)
async def get_professor(
    professor_id: int = Path(..., description="The ID of the professor to retrieve"),
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Get detailed information about a specific professor.

    - **professor_id**: The unique identifier of the professor
    """
    professor = service.get_professor(professor_id)
    if not professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor with ID {professor_id} not found",
        )
    return professor


@router.post(
    "",
    response_model=ProfessorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create professor",
    description="Create a new professor.",
)
async def create_professor(
    professor_data: ProfessorCreate,
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Create a new professor.

    - Request body contains all required professor information
    - Returns the created professor with its assigned ID
    """
    return service.create_professor(professor_data)


@router.put(
    "/{professor_id}",
    response_model=ProfessorResponse,
    summary="Update professor",
    description="Update an existing professor.",
    responses={404: {"description": "Professor not found"}},
)
async def update_professor(
    professor_data: ProfessorUpdate,
    professor_id: int = Path(..., description="The ID of the professor to update"),
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Update an existing professor.

    - **professor_id**: The unique identifier of the professor to update
    - Request body contains the updated professor information
    - Returns the updated professor
    """
    updated_professor = service.update_professor(professor_id, professor_data)
    if not updated_professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor with ID {professor_id} not found",
        )
    return updated_professor


@router.post(
    "/{professor_id}/assign-voice",
    response_model=ProfessorResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign voice to professor",
    description="Assigns a voice to an existing professor based on their profile attributes.",
    responses={
        404: {"description": "Professor not found"},
        500: {"description": "Voice assignment failed"},
    },
)
async def assign_voice_to_professor(
    professor_id: int = Path(..., description="The ID of the professor to assign a voice to"),
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Assign a voice to an existing professor.

    - **professor_id**: The unique identifier of the professor
    - Automatically selects an appropriate voice based on the professor's profile
    - Skips assignment if the professor already has a voice
    - Returns the updated professor data with the assigned voice information
    """
    updated_professor = service.assign_voice_to_professor(professor_id)
    if not updated_professor:
        # Check if professor exists first to return 404 vs 500
        existing_professor = service.get_professor(professor_id)
        if not existing_professor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Professor with ID {professor_id} not found",
            )
        else:
            # Professor exists, but voice assignment failed
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to assign voice to professor {professor_id}",
            )

    return updated_professor


@router.delete(
    "/{professor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete professor",
    description="Delete a professor.",
    responses={
        404: {"description": "Professor not found"},
        409: {"description": "Cannot delete professor with associated courses"},
    },
)
async def delete_professor(
    professor_id: int = Path(..., description="The ID of the professor to delete"),
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Delete a professor.

    - **professor_id**: The unique identifier of the professor to delete
    - Returns no content on successful deletion
    """
    success = service.delete_professor(professor_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor with ID {professor_id} not found",
        )
    # For 204 No Content, we should not return any response body
    # FastAPI will handle the 204 status code automatically based on the decorator


@router.get(
    "/{professor_id}/courses",
    response_model=ProfessorCoursesResponse,
    summary="Get professor's courses",
    description="Get courses taught by a specific professor.",
    responses={404: {"description": "Professor not found"}},
)
async def get_professor_courses(
    professor_id: int = Path(..., description="The ID of the professor"),
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Get courses taught by a specific professor.

    - **professor_id**: The unique identifier of the professor
    - Returns a list of courses taught by the professor
    """
    response = service.get_professor_courses(professor_id)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor with ID {professor_id} not found",
        )
    return response


@router.get(
    "/{professor_id}/lectures",
    response_model=ProfessorLecturesResponse,
    summary="Get professor's lectures",
    description="Get lectures by a specific professor.",
    responses={404: {"description": "Professor not found"}},
)
async def get_professor_lectures(
    professor_id: int = Path(..., description="The ID of the professor"),
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Get lectures by a specific professor.

    - **professor_id**: The unique identifier of the professor
    - Returns a list of lectures by the professor across all their courses
    """
    response = service.get_professor_lectures(professor_id)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor with ID {professor_id} not found",
        )
    return response


@router.post(
    "/{professor_id}/generate-image",
    response_model=ProfessorResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate professor image",
    description="Triggers the generation of a profile image for the specified professor.",
    responses={
        404: {"description": "Professor not found"},
        500: {"description": "Image generation failed"},
    },
)
async def generate_professor_image(
    professor_id: int = Path(..., description="The ID of the professor to generate an image for"),
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Generate a profile image for a specific professor.

    - **professor_id**: The unique identifier of the professor
    - Triggers an asynchronous image generation process.
    - Returns the updated professor data with the new image URL if successful.
    """
    updated_professor = await service.generate_professor_image(professor_id)
    if not updated_professor:
        # Distinguish between professor not found and generation failure if possible
        # For now, treating failure generally as internal error
        # Re-fetch professor to check if it exists, if needed for 404 vs 500

        # Check if professor exists first to return 404 (NO await for sync get_professor)
        existing_professor = service.get_professor(professor_id)
        if not existing_professor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Professor with ID {professor_id} not found",
            )
        else:
            # Professor exists, but generation failed
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate image for professor {professor_id}",
            )

    return updated_professor


@router.post(
    "/generate",
    response_model=ProfessorResponse,
    # Use 200 as we're returning the generated data, not creating a resource yet
    status_code=status.HTTP_200_OK,
    summary="Generate professor profile",
    description="Generates a professor profile using AI based on any provided details.",
    responses={
        500: {"description": "Profile generation failed"},
    },
)
async def generate_professor(
    generation_data: ProfessorGenerate,  # Updated model
    service: ProfessorApiService = Depends(get_professor_api_service),
):
    """
    Generate a professor profile using AI.

    Accepts an optional dictionary of partial attributes to guide the generation.
    If no attributes are provided, a completely new profile will be invented.
    If attributes like `department_id` are provided without `department_name`,
    the service will attempt to look up the name.

    Args:
        generation_data: Contains optional `partial_attributes` dictionary.

    Returns:
        The generated professor profile data (not saved to the database).
    """
    # The service method already handles exceptions and converts to HTTPException
    return await service.generate_professor(generation_data)


@router.post(
    "/generate/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue professor generation job",
    description=(
        "Enqueue an async job to generate a professor using AI. Returns a job id to poll via "
        "GET /api/v1/jobs/{id}."
    ),
)
async def enqueue_generate_professor(
    generation_data: ProfessorGenerate,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    payload = {
        "partial_attributes": generation_data.partial_attributes or {},
        "freeform_prompt": generation_data.freeform_prompt,
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    row = repository_factory.job.create(kind="generate_professor", payload=payload)
    return {
        "id": row.id,
        "kind": row.kind,
        "status": row.status,
        "attempts": row.attempts,
        "max_attempts": row.max_attempts,
        "priority": row.priority,
        "run_after": row.run_after,
    }


@router.post(
    "/{professor_id}/generate-image/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue professor image generation job",
    description=(
        "Enqueue an async job to generate a professor image. Returns a job id to poll via "
        "GET /api/v1/jobs/{id}."
    ),
)
async def enqueue_generate_professor_image(
    professor_id: int = Path(..., description="The ID of the professor to generate an image for"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    payload = {"professor_id": professor_id}
    row = repository_factory.job.create(kind="generate_professor_image", payload=payload)
    return {
        "id": row.id,
        "kind": row.kind,
        "status": row.status,
        "attempts": row.attempts,
        "max_attempts": row.max_attempts,
        "priority": row.priority,
        "run_after": row.run_after,
    }
