"""
Department router for handling department-related API endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse

from artificial_u.models.database import Repository
from artificial_u.api.services.department_service import DepartmentService
from artificial_u.api.config import get_settings, Settings
from artificial_u.api.models.departments import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentsListResponse,
    DepartmentProfessorsResponse,
    DepartmentCoursesResponse,
)


router = APIRouter(
    prefix="/departments",
    tags=["departments"],
    responses={404: {"description": "Not found"}},
)


def get_repository(settings: Settings = Depends(get_settings)) -> Repository:
    """Dependency for getting repository instance."""
    return Repository(db_url=settings.DATABASE_URL)


def get_department_service(
    repository: Repository = Depends(get_repository),
) -> DepartmentService:
    """Dependency for getting department service."""
    return DepartmentService(repository)


@router.get(
    "",
    response_model=DepartmentsListResponse,
    summary="List departments",
    description="Get a paginated list of departments with optional filtering.",
)
async def list_departments(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    faculty: Optional[str] = Query(None, description="Filter by faculty"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    service: DepartmentService = Depends(get_department_service),
):
    """
    Get a paginated list of departments with filtering options.

    - **page**: Page number (starting from 1)
    - **size**: Number of items per page (1-100)
    - **faculty**: Filter by faculty name (exact match)
    - **name**: Filter by department name (partial match)
    """
    return service.get_departments(
        page=page,
        size=size,
        faculty=faculty,
        name=name,
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
    service: DepartmentService = Depends(get_department_service),
):
    """
    Get detailed information about a specific department.

    - **department_id**: The unique identifier of the department
    """
    department = service.get_department(department_id)
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
)
async def create_department(
    department_data: DepartmentCreate,
    service: DepartmentService = Depends(get_department_service),
):
    """
    Create a new department.

    - Request body contains all required department information
    - Returns the created department with its assigned ID
    """
    return service.create_department(department_data)


@router.put(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Update department",
    description="Update an existing department.",
    responses={404: {"description": "Department not found"}},
)
async def update_department(
    department_data: DepartmentUpdate,
    department_id: int = Path(..., description="The ID of the department to update"),
    service: DepartmentService = Depends(get_department_service),
):
    """
    Update an existing department.

    - **department_id**: The unique identifier of the department to update
    - Request body contains the updated department information
    - Returns the updated department
    """
    updated_department = service.update_department(department_id, department_data)
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
        409: {
            "description": "Cannot delete department with associated professors or courses"
        },
    },
)
async def delete_department(
    department_id: int = Path(..., description="The ID of the department to delete"),
    service: DepartmentService = Depends(get_department_service),
):
    """
    Delete a department.

    - **department_id**: The unique identifier of the department to delete
    - Returns no content on successful deletion
    - Returns 409 Conflict if department has associated professors or courses
    """
    success = service.delete_department(department_id)
    if not success:
        # First check if department exists
        department = service.get_department(department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with ID {department_id} not found",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot delete department with ID {department_id} because it has associated professors or courses",
            )
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@router.get(
    "/{department_id}/professors",
    response_model=DepartmentProfessorsResponse,
    summary="Get department's professors",
    description="Get professors in a specific department.",
    responses={404: {"description": "Department not found"}},
)
async def get_department_professors(
    department_id: int = Path(..., description="The ID of the department"),
    service: DepartmentService = Depends(get_department_service),
):
    """
    Get professors in a specific department.

    - **department_id**: The unique identifier of the department
    - Returns a list of professors in the department
    """
    response = service.get_department_professors(department_id)
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
    service: DepartmentService = Depends(get_department_service),
):
    """
    Get courses in a specific department.

    - **department_id**: The unique identifier of the department
    - Returns a list of courses in the department
    """
    response = service.get_department_courses(department_id)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found",
        )
    return response
