"""
Course router for handling course-related API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import JSONResponse

from artificial_u.api.config import Settings, get_settings
from artificial_u.api.models.courses import (
    CourseCreate,
    CourseLecturesResponse,
    CourseResponse,
    CoursesListResponse,
    CourseUpdate,
    DepartmentBrief,
    ProfessorBrief,
)
from artificial_u.api.services.course_service import CourseService
from artificial_u.models.repositories import RepositoryFactory

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
    responses={404: {"description": "Not found"}},
)


def get_repository(settings: Settings = Depends(get_settings)) -> RepositoryFactory:
    """Dependency for getting repository instance."""
    return RepositoryFactory(db_url=settings.DATABASE_URL)


def get_course_service(
    repository: RepositoryFactory = Depends(get_repository),
) -> CourseService:
    """Dependency for getting course service."""
    return CourseService(repository)


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
    service: CourseService = Depends(get_course_service),
):
    """
    Get a paginated list of courses with filtering options.

    - **page**: Page number (starting from 1)
    - **size**: Number of items per page (1-100)
    - **department_id**: Filter by department ID
    - **professor_id**: Filter by professor ID
    - **level**: Filter by course level (e.g., 'Undergraduate', 'Graduate')
    - **title**: Filter by course title (partial match)
    """
    return service.get_courses(
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
    service: CourseService = Depends(get_course_service),
):
    """
    Get detailed information about a specific course.

    - **course_id**: The unique identifier of the course
    """
    course = service.get_course(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )
    return course


@router.get(
    "/code/{code}",
    response_model=CourseResponse,
    summary="Get course by code",
    description="Get detailed information about a specific course by its code.",
    responses={404: {"description": "Course not found"}},
)
async def get_course_by_code(
    code: str = Path(..., description="The code of the course to retrieve"),
    service: CourseService = Depends(get_course_service),
):
    """
    Get detailed information about a specific course by its code.

    - **code**: The unique code of the course
    """
    course = service.get_course_by_code(code)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with code {code} not found",
        )
    return course


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create course",
    description="Create a new course.",
)
async def create_course(
    course_data: CourseCreate,
    service: CourseService = Depends(get_course_service),
):
    """
    Create a new course.

    - Request body contains all required course information
    - Returns the created course with its assigned ID
    """
    return service.create_course(course_data)


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Update course",
    description="Update an existing course.",
    responses={404: {"description": "Course not found"}},
)
async def update_course(
    course_data: CourseUpdate,
    course_id: int = Path(..., description="The ID of the course to update"),
    service: CourseService = Depends(get_course_service),
):
    """
    Update an existing course.

    - **course_id**: The unique identifier of the course to update
    - Request body contains the updated course information
    - Returns the updated course
    """
    updated_course = service.update_course(course_id, course_data)
    if not updated_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )
    return updated_course


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete course",
    description="Delete a course.",
    responses={
        404: {"description": "Course not found"},
        409: {"description": "Cannot delete course with associated lectures"},
    },
)
async def delete_course(
    course_id: int = Path(..., description="The ID of the course to delete"),
    service: CourseService = Depends(get_course_service),
):
    """
    Delete a course.

    - **course_id**: The unique identifier of the course to delete
    - Returns no content on successful deletion
    """
    success = service.delete_course(course_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )
    return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)


@router.get(
    "/{course_id}/professor",
    response_model=ProfessorBrief,
    summary="Get course professor",
    description="Get information about the professor teaching a specific course.",
    responses={404: {"description": "Course or professor not found"}},
)
async def get_course_professor(
    course_id: int = Path(..., description="The ID of the course"),
    service: CourseService = Depends(get_course_service),
):
    """
    Get information about the professor teaching a specific course.

    - **course_id**: The unique identifier of the course
    - Returns brief information about the professor
    """
    professor = service.get_course_professor(course_id)
    if not professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} or its professor not found",
        )
    return professor


@router.get(
    "/{course_id}/department",
    response_model=DepartmentBrief,
    summary="Get course department",
    description="Get information about the department offering a specific course.",
    responses={404: {"description": "Course or department not found"}},
)
async def get_course_department(
    course_id: int = Path(..., description="The ID of the course"),
    service: CourseService = Depends(get_course_service),
):
    """
    Get information about the department offering a specific course.

    - **course_id**: The unique identifier of the course
    - Returns brief information about the department
    """
    department = service.get_course_department(course_id)
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} or its department not found",
        )
    return department


@router.get(
    "/{course_id}/lectures",
    response_model=CourseLecturesResponse,
    summary="Get course lectures",
    description="Get lectures for a specific course.",
    responses={404: {"description": "Course not found"}},
)
async def get_course_lectures(
    course_id: int = Path(..., description="The ID of the course"),
    service: CourseService = Depends(get_course_service),
):
    """
    Get lectures for a specific course.

    - **course_id**: The unique identifier of the course
    - Returns a list of lectures for the course
    """
    response = service.get_course_lectures(course_id)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )
    return response
