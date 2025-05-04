"""
Department router for handling department-related API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from artificial_u.api.dependencies import get_department_api_service
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
from artificial_u.api.services import DepartmentApiService

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
    faculty: Optional[str] = Query(None, description="Filter by faculty"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Get a paginated list of departments with filtering options.

    - **page**: Page number (starting from 1)
    - **size**: Number of items per page (1-100)
    - **faculty**: Filter by faculty name (exact match)
    - **name**: Filter by department name (partial match)
    """
    return await department_service.get_departments(
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
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Get detailed information about a specific department.

    - **department_id**: The unique identifier of the department
    """
    department = await department_service.get_department(department_id)
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
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Create a new department.

    - Request body contains all required department information
    - Returns the created department with its assigned ID
    """
    return await department_service.create_department(department_data)


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
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Update an existing department.

    - **department_id**: The unique identifier of the department to update
    - Request body contains the updated department information
    - Returns the updated department
    """
    updated_department = await department_service.update_department(department_id, department_data)
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
    success = await department_service.delete_department(department_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found",
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
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Get professors in a specific department.

    - **department_id**: The unique identifier of the department
    - Returns a list of professors in the department
    """
    response = await department_service.get_department_professors(department_id)
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
    response = await department_service.get_department_courses(department_id)
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
    department = await department_service.get_department_by_code(code)
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
    professors = await department_service.get_department_professors(department_id)
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
    courses = await department_service.get_department_courses(department_id)
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
)
async def generate_department(
    department_data: DepartmentGenerate,
    department_service: DepartmentApiService = Depends(get_department_api_service),
):
    """
    Generate a department using AI.

    - If name is provided, it is used.
    - If only course_name is provided, it is used to invent a department.
    - If neither is provided, the model invents a department.

    Args:
        name: Optional name of the department to generate
        course_name: Optional name of the course to generate a department for
    Returns:
        The generated department XML as a string
    """
    return await department_service.generate_department(department_data)
