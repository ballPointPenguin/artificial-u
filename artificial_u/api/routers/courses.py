"""
Course router for handling course-related API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from artificial_u.api.dependencies import get_course_api_service
from artificial_u.api.models import (
    CourseCreate,
    CourseDepartmentBrief,
    CourseGenerate,
    CourseLecturesResponse,
    CourseProfessorBrief,
    CourseResponse,
    CoursesListResponse,
    CourseUpdate,
)
from artificial_u.api.services import CourseApiService

# Create the router
router = APIRouter(
    prefix="/courses",
    tags=["courses"],
    responses={404: {"description": "Not found"}},
    # Dependency injection handled per route for clarity now
)


@router.get(
    "",
    response_model=CoursesListResponse,
    summary="List courses",
    description="Get a paginated list of courses with optional filtering.",
)
async def list_courses(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    professor_id: Optional[int] = Query(None, description="Filter by professor ID"),
    level: Optional[str] = Query(None, description="Filter by course level"),
    title: Optional[str] = Query(None, description="Filter by title (partial match)"),
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Get a paginated list of courses with filtering options.
    """
    return await course_service.get_courses(
        page=page,
        size=size,
        department_id=department_id,
        professor_id=professor_id,
        level=level,
        title=title,
    )


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Get course by ID",
    description="Get detailed information about a specific course.",
    responses={404: {"description": "Course not found"}},
)
async def get_course(
    course_id: int = Path(..., description="The ID of the course to retrieve"),
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Get detailed information about a specific course.
    """
    # Service raises HTTPException on not found or errors (if implemented)
    # Add check for None response
    response_data = await course_service.get_course(course_id)
    if response_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )
    return response_data


@router.get(
    "/code/{code}",
    response_model=CourseResponse,
    summary="Get course by code",
    description="Get detailed information about a specific course by its code.",
    responses={404: {"description": "Course not found"}},
)
async def get_course_by_code(
    code: str = Path(..., description="The code of the course to retrieve"),
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Get detailed information about a specific course by its code.
    """
    # Service raises HTTPException on not found or errors (if implemented)
    # Add check for None response
    response_data = await course_service.get_course_by_code(code)
    if response_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with code {code} not found.",
        )
    return response_data


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create course",
    description="Create a new course.",
    responses={  # Add specific error responses
        404: {"description": "Professor or Department not found"},
        500: {"description": "Internal server error during creation"},
    },
)
async def create_course(
    course_data: CourseCreate,
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Create a new course.
    The service handles looking up dependencies and potential errors.
    """
    return await course_service.create_course(course_data)


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Update course",
    description="Update an existing course.",
    responses={
        404: {"description": "Course or referenced Professor not found"},
        400: {"description": "Invalid update data (e.g., bad foreign key)"},
        500: {"description": "Internal server error during update"},
    },
)
async def update_course(
    course_data: CourseUpdate,
    course_id: int = Path(..., description="The ID of the course to update"),
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Update an existing course.
    The service handles the update logic and potential errors.
    """
    # Service handles update logic and raises HTTPException on errors
    updated_course_data = await course_service.update_course(course_id, course_data)
    # Add check for None response (course not found)
    if updated_course_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found for update.",
        )
    return updated_course_data


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete course",
    description="Delete a course.",
    responses={
        404: {"description": "Course not found"},
        409: {"description": "Cannot delete course with associated resources (e.g., lectures)"},
        500: {"description": "Internal server error during deletion"},
    },
)
async def delete_course(
    course_id: int = Path(..., description="The ID of the course to delete"),
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Delete a course.
    The service handles deletion and raises specific exceptions for 404/409/500.
    """
    success = await course_service.delete_course(course_id)
    # The service now returns False only if not found (after attempting delete)
    # It raises HTTPException for 409 or 500 errors.
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found for deletion.",
        )
    # If service returns True, return 204
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@router.get(
    "/{course_id}/professor",
    response_model=CourseProfessorBrief,
    summary="Get course professor",
    description="Get information about the professor teaching a specific course.",
    responses={
        404: {"description": "Course or its associated Professor not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_course_professor(
    course_id: int = Path(..., description="The ID of the course"),
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Get information about the professor teaching a specific course.
    """
    # Service handles lookup and raises HTTPException on errors (if implemented)
    # Add check for None response
    response_data = await course_service.get_course_professor(course_id)
    if response_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} or its professor not found.",
        )
    return response_data


@router.get(
    "/{course_id}/department",
    response_model=CourseDepartmentBrief,
    summary="Get course department",
    description="Get information about the department offering a specific course.",
    responses={
        404: {"description": "Course or its associated Department not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_course_department(
    course_id: int = Path(..., description="The ID of the course"),
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Get information about the department offering a specific course.
    """
    # Service handles lookup and raises HTTPException on errors (if implemented)
    # Add check for None response
    response_data = await course_service.get_course_department(course_id)
    if response_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} or its department not found.",
        )
    return response_data


@router.get(
    "/{course_id}/lectures",
    response_model=CourseLecturesResponse,
    summary="Get course lectures",
    description="Get lectures for a specific course.",
    responses={
        404: {"description": "Course not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_course_lectures(
    course_id: int = Path(..., description="The ID of the course"),
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Get lectures for a specific course.
    """
    # Service handles lookup and raises HTTPException on errors (if implemented)
    # We also need to handle the case where the service might just return None
    response_data = await course_service.get_course_lectures(course_id)
    if response_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found or has no lectures.",
        )
    return response_data


@router.post(
    "/generate",
    response_model=CourseResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate course data",
    description="Generates course data using AI based on partial attributes.",
    responses={
        500: {"description": "Course generation failed"},
    },
)
async def generate_course(
    generation_data: CourseGenerate,
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Generate course data using AI.

    Accepts optional partial attributes and a freeform prompt to guide generation.

    Args:
        generation_data: Contains optional partial_attributes and freeform_prompt.

    Returns:
        The generated course data (not saved to the database).
    """
    # The service method handles exceptions and converts to HTTPException
    return await course_service.generate_course(generation_data)
