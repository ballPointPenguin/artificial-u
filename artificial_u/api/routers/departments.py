"""
Department router for handling department-related API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from artificial_u.api.dependencies import get_department_api_service, get_repository_factory
from artificial_u.api.models import (
    CoursesListResponse,
    DepartmentCoursesResponse,
    DepartmentCreate,
    DepartmentGenerate,
    DepartmentProfessorsResponse,
    DepartmentResponse,
    DepartmentsListResponse,
    DepartmentUpdate,
    ProfessorsListResponse,
)
from artificial_u.api.security.auth0 import require_coins, require_role
from artificial_u.api.services import DepartmentApiService
from artificial_u.config.settings import get_settings
from artificial_u.models.repositories.factory import RepositoryFactory

# Create the router with dependencies that will be applied to all routes
router = APIRouter(
    prefix="/departments",
    tags=["departments"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_department_api_service)],
)


@router.get(
    "",
    response_model=DepartmentsListResponse,
    summary="List departments",
    description="Get a paginated list of departments with optional filtering.",
)
async def list_departments(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    faculty_id: Optional[int] = Query(None, description="Filter by faculty ID"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    language: str = Query("en", description="Content language sandbox (e.g., 'en', 'fr')"),
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Get a paginated list of departments with filtering options.

    - **page**: Page number (starting from 1)
    - **size**: Number of items per page (1-100)
    - **faculty_id**: Filter by faculty ID
    - **name**: Filter by department name (partial match)
    - **language**: Content language sandbox (default: 'en')
    """
    return department_service.get_departments(
        page=page,
        size=size,
        faculty_id=faculty_id,
        name=name,
        language=language,
    )


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Get department by ID",
    description="Get detailed information about a specific department.",
    responses={404: {"description": "Department not found"}},
)
async def get_department(
    department_id: int = Path(..., description="The ID of the department to retrieve"),
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Get detailed information about a specific department.

    - **department_id**: The unique identifier of the department
    """
    department = department_service.get_department(department_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found",
        )
    return department


@router.post(
    "",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
    description="Create a new department.",
    dependencies=[require_role("creator")],
)
async def create_department(
    department_data: DepartmentCreate,
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Create a new department.

    - Request body contains all required department information
    - Returns the created department with its assigned ID
    """
    return department_service.create_department(department_data)


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Update department",
    description="Update an existing department.",
    responses={404: {"description": "Department not found"}},
    dependencies=[require_role("creator")],
)
async def update_department(
    department_data: DepartmentUpdate,
    department_id: int = Path(..., description="The ID of the department to update"),
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Update an existing department.

    - **department_id**: The unique identifier of the department to update
    - Request body contains the updated department information
    - Returns the updated department
    """
    updated_department = department_service.update_department(department_id, department_data)
    if not updated_department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found",
        )
    return updated_department


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete department",
    description="Delete a department.",
    responses={
        404: {"description": "Department not found"},
    },
    dependencies=[require_role("creator")],
)
async def delete_department(
    department_id: int = Path(..., description="The ID of the department to delete"),
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Delete a department.

    - **department_id**: The unique identifier of the department to delete
    - Returns no content on successful deletion
    - Any associated professors or courses will have their department_id set to null
    """
    success = department_service.delete_department(department_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found",
        )
    # For 204 No Content, we should not return any response body
    # FastAPI will handle the 204 status code automatically based on the decorator


@router.get(
    "/{department_id}/professors",
    response_model=DepartmentProfessorsResponse,
    summary="Get department's professors",
    description="Get professors in a specific department.",
    responses={404: {"description": "Department not found"}},
)
async def get_department_professors(
    department_id: int = Path(..., description="The ID of the department"),
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Get professors in a specific department.

    - **department_id**: The unique identifier of the department
    - Returns a list of professors in the department
    """
    response = department_service.get_department_professors(department_id)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found",
        )
    return response


@router.get(
    "/{department_id}/courses",
    response_model=DepartmentCoursesResponse,
    summary="Get department's courses",
    description="Get courses in a specific department.",
    responses={404: {"description": "Department not found"}},
)
async def get_department_courses(
    department_id: int = Path(..., description="The ID of the department"),
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Get courses in a specific department.

    - **department_id**: The unique identifier of the department
    - Returns a list of courses in the department
    """
    response = department_service.get_department_courses(department_id)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found",
        )
    return response


@router.get("/code/{code}", response_model=DepartmentResponse)
async def get_department_by_code(
    code: str,
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Get department details by code.

    Args:
        code: Department code
        department_service: Department service

    Returns:
        Department details

    Raises:
        HTTPException: If department not found
    """
    department = department_service.get_department_by_code(code)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.get("/{department_id}/professors", response_model=ProfessorsListResponse)
async def list_department_professors(
    department_id: int,
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    List professors for a department.

    Args:
        department_id: Department ID
        department_service: Department service

    Returns:
        List of professors

    Raises:
        HTTPException: If department not found
    """
    professors = department_service.get_department_professors(department_id)
    if not professors:
        raise HTTPException(status_code=404, detail="Department not found")
    return professors


@router.get("/{department_id}/courses", response_model=CoursesListResponse)
async def list_department_courses(
    department_id: int,
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    List courses for a department.

    Args:
        department_id: Department ID
        department_service: Department service

    Returns:
        List of courses

    Raises:
        HTTPException: If department not found
    """
    courses = department_service.get_department_courses(department_id)
    if not courses:
        raise HTTPException(status_code=404, detail="Department not found")
    return courses


@router.post(
    "/generate",
    response_model=DepartmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate department",
    description="Generate a department using AI.",
    responses={
        500: {"description": "Department generation failed"},
    },
    dependencies=[require_coins(cost=get_settings().COIN_COST_DEPARTMENT_GENERATION)],
)
async def generate_department(
    generation_data: DepartmentGenerate,
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Generate department data using AI.

    Accepts optional partial attributes and a freeform prompt to guide generation.

    Args:
        generation_data: Contains optional partial_attributes and freeform_prompt.

    Returns:
        The generated department data (not saved to the database).
    """
    return await department_service.generate_department(generation_data)


@router.post(
    "/generate/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue department generation job",
    description=(
        "Enqueue an async job to generate department data using AI. Returns a job id to poll via "
        "GET /api/v1/jobs/{id}."
    ),
    dependencies=[require_coins(cost=get_settings().COIN_COST_DEPARTMENT_GENERATION)],
)
async def enqueue_generate_department(
    generation_data: DepartmentGenerate,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Enqueue a job with kind 'generate_department'. The payload mirrors DepartmentGenerate.
    """
    payload = {
        "partial_attributes": (generation_data.partial_attributes or {}),
        "freeform_prompt": generation_data.freeform_prompt,
        # departmental context if provided in model
        "department_id": generation_data.department_id,
    }
    # Remove keys with None to keep payload concise
    payload = {k: v for k, v in payload.items() if v is not None}

    row = repository_factory.job.create(
        kind="generate_department",
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
