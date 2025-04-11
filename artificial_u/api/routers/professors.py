"""
Professor router for handling professor-related API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from artificial_u.models.database import Repository
from artificial_u.api.services.professor_service import ProfessorService
from artificial_u.api.config import get_settings, Settings
from artificial_u.api.models.professors import (
    ProfessorCreate,
    ProfessorUpdate,
    ProfessorResponse,
    ProfessorsListResponse,
    ProfessorCoursesResponse,
    ProfessorLecturesResponse,
)


router = APIRouter(
    prefix="/professors",
    tags=["professors"],
    responses={404: {"description": "Not found"}},
)


def get_repository(settings: Settings = Depends(get_settings)) -> Repository:
    """Dependency for getting repository instance."""
    return Repository(db_url=settings.DATABASE_URL)


def get_professor_service(
    repository: Repository = Depends(get_repository),
) -> ProfessorService:
    """Dependency for getting professor service."""
    return ProfessorService(repository)


@router.get(
    "",
    response_model=ProfessorsListResponse,
    summary="List professors",
    description="Get a paginated list of professors with optional filtering.",
)
async def list_professors(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    department: Optional[str] = Query(None, description="Filter by department"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    specialization: Optional[str] = Query(
        None, description="Filter by specialization (partial match)"
    ),
    service: ProfessorService = Depends(get_professor_service),
):
    """
    Get a paginated list of professors with filtering options.

    - **page**: Page number (starting from 1)
    - **size**: Number of items per page (1-100)
    - **department**: Filter by department name (exact match)
    - **name**: Filter by professor name (partial match)
    - **specialization**: Filter by specialization (partial match)
    """
    return service.get_professors(
        page=page,
        size=size,
        department=department,
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
    service: ProfessorService = Depends(get_professor_service),
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
    service: ProfessorService = Depends(get_professor_service),
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
    service: ProfessorService = Depends(get_professor_service),
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
    service: ProfessorService = Depends(get_professor_service),
):
    """
    Delete a professor.

    - **professor_id**: The unique identifier of the professor to delete
    - Returns no content on successful deletion
    """
    # In a real implementation, we would check for associated resources and possibly
    # implement soft delete if references exist
    success = service.delete_professor(professor_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor with ID {professor_id} not found",
        )
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@router.get(
    "/{professor_id}/courses",
    response_model=ProfessorCoursesResponse,
    summary="Get professor's courses",
    description="Get courses taught by a specific professor.",
    responses={404: {"description": "Professor not found"}},
)
async def get_professor_courses(
    professor_id: int = Path(..., description="The ID of the professor"),
    service: ProfessorService = Depends(get_professor_service),
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
    service: ProfessorService = Depends(get_professor_service),
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
