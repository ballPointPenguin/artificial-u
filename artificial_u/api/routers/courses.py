"""
Course router for handling course-related API endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from artificial_u.api.dependencies import (
    ensure_student,
    get_course_api_service,
    get_repository_factory,
    optional_student,
)
from artificial_u.api.models import (
    CourseCreate,
    CourseDepartmentBrief,
    CourseGenerate,
    CourseLecturesResponse,
    CourseProfessorBrief,
    CourseResponse,
    CoursesListResponse,
    CourseUpdate,
    GeneratedCourseData,
)
from artificial_u.api.security.auth0 import require_coins, require_role
from artificial_u.api.services import CourseApiService
from artificial_u.config.settings import get_settings
from artificial_u.models.core import Student
from artificial_u.models.repositories.factory import RepositoryFactory

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
    description="Get a paginated list of courses with optional filtering and sorting. "
    "Hidden courses are only visible to authenticated users.",
)
async def list_courses(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    professor_id: Optional[int] = Query(None, description="Filter by professor ID"),
    level: Optional[str] = Query(None, description="Filter by course level"),
    title: Optional[str] = Query(None, description="Filter by title (partial match)"),
    created_by: Optional[int] = Query(None, description="Filter by creator student ID"),
    sort_by: Optional[str] = Query(
        "updated_at",
        description=(
            "Field to sort by (code, title, level, status, updated_at, created_at, "
            "professor, department, creator, audio_count, topics_count)"
        ),
    ),
    order: Optional[str] = Query(
        "desc", description="Sort order (asc or desc)", pattern="^(asc|desc)$"
    ),
    include_hidden: bool = Query(
        False,
        description=(
            "When true, authenticated users see hidden courses they are allowed "
            "to see (admins: all hidden; non-admins: their own hidden). "
            "Ignored for unauthenticated requests, which always see only "
            "published courses."
        ),
    ),
    language: str = Query("en", description="Content language sandbox (e.g., 'en', 'fr')"),
    course_service: CourseApiService = Depends(get_course_api_service),
    student: Optional[Student] = Depends(optional_student),
):
    """
    Get a paginated list of courses with filtering and sorting options.

    Visibility rules for hidden courses:
    - Unauthenticated users: only see published courses
    - Authenticated non-admin users: see published courses + hidden courses they created
    - Admin users: see all courses
    """
    student_id = student.id if student else None
    student_role = student.role if student else None
    return course_service.get_courses(
        page=page,
        size=size,
        department_id=department_id,
        professor_id=professor_id,
        level=level,
        title=title,
        created_by=created_by,
        sort_by=sort_by,
        order=order,
        student_id=student_id,
        student_role=student_role,
        include_hidden=include_hidden,
        language=language,
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
    response_data = course_service.get_course(course_id)
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
    response_data = course_service.get_course_by_code(code)
    if response_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with code {code} not found.",
        )
    return response_data


@router.post(
    "/{course_id}/generate-image",
    response_model=CourseResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate course album art",
    description=(
        "Generates or regenerates AI album-art imagery for a course. "
        "Only the creator or an admin can modify a course."
    ),
    responses={
        404: {"description": "Course not found"},
        403: {"description": "Forbidden - user doesn't own this course"},
        500: {"description": "Image generation failed"},
    },
    dependencies=[require_coins(cost=get_settings().COIN_COST_COURSE_IMAGE)],
)
async def generate_course_image(
    course_id: int = Path(..., description="The ID of the course to generate art for"),
    course_service: CourseApiService = Depends(get_course_api_service),
    student: Student = Depends(ensure_student),
):
    """
    Generate album art for a course (sync; may take several minutes).
    """
    updated = await course_service.generate_course_image(course_id, student.id, student.role)
    if updated:
        return updated

    try:
        existing = course_service.get_course(course_id)
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise
        raise
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to generate image for course {course_id}",
    )


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create course",
    description="Create a new course with optional smart selection for department/professor.",
    responses={  # Add specific error responses
        404: {"description": "Professor or Department not found"},
        500: {"description": "Internal server error during creation"},
    },
    dependencies=[require_role("creator")],
)
async def create_course(
    course_data: CourseCreate,
    course_service: CourseApiService = Depends(get_course_api_service),
    student=Depends(ensure_student),
):
    """
    Create a new course with optional smart selection.
    If department_id or professor_id are not provided, the system will
    intelligently select existing ones or generate new ones using AI.
    """
    return await course_service.create_course(course_data, created_by=student.id)


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Update course",
    description="Update an existing course. Only the creator or an admin can modify a course.",
    responses={
        404: {"description": "Course or referenced Professor not found"},
        403: {"description": "Forbidden - user doesn't own this course"},
        400: {"description": "Invalid update data (e.g., bad foreign key)"},
        500: {"description": "Internal server error during update"},
    },
    dependencies=[require_role("creator")],
)
async def update_course(
    course_data: CourseUpdate,
    course_id: int = Path(..., description="The ID of the course to update"),
    course_service: CourseApiService = Depends(get_course_api_service),
    student: Student = Depends(ensure_student),
):
    """
    Update an existing course.
    The service handles the update logic and potential errors.
    Requires ownership verification - only the course creator or admin can update.
    """
    # Service handles update logic with ownership check
    updated_course_data = course_service.update_course(
        course_id, course_data, student.id, student.role
    )
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
    description="Delete a course. Only the creator or an admin can delete a course.",
    responses={
        404: {"description": "Course not found"},
        403: {"description": "Forbidden - user doesn't own this course"},
        409: {"description": "Cannot delete course with associated resources (e.g., lectures)"},
        500: {"description": "Internal server error during deletion"},
    },
    dependencies=[require_role("creator")],
)
async def delete_course(
    course_id: int = Path(..., description="The ID of the course to delete"),
    course_service: CourseApiService = Depends(get_course_api_service),
    student: Student = Depends(ensure_student),
):
    """
    Delete a course.
    The service handles deletion and raises specific exceptions for 404/409/500.
    Requires ownership verification - only the course creator or admin can delete.
    """
    success = course_service.delete_course(course_id, student.id, student.role)
    # The service now returns False only if not found (after attempting delete)
    # It raises HTTPException for 409 or 500 errors.
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found for deletion.",
        )
    # For 204 No Content, we should not return any response body
    # FastAPI will handle the 204 status code automatically based on the decorator


@router.post(
    "/{course_id}/publish",
    response_model=CourseResponse,
    summary="Publish course",
    description="Publish a course, making it visible to the public. This is a one-way action.",
    responses={
        404: {"description": "Course not found"},
        403: {"description": "Forbidden - user doesn't own this course"},
        400: {"description": "Course is already published"},
        500: {"description": "Internal server error during publishing"},
    },
    dependencies=[require_role("creator")],
)
async def publish_course(
    course_id: int = Path(..., description="The ID of the course to publish"),
    course_service: CourseApiService = Depends(get_course_api_service),
    student: Student = Depends(ensure_student),
):
    """
    Publish a course by changing its status from 'hidden' to 'published'.
    This is a one-way action - courses cannot be unpublished.
    Only the course creator or an admin can publish a course.
    """
    return course_service.publish_course(course_id, student.id, student.role)


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
    response_data = course_service.get_course_professor(course_id)
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
    response_data = course_service.get_course_department(course_id)
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
    description="Get lecture briefs for a specific course (excluding content field for performance).",
    responses={
        404: {"description": "Course not found"},
        500: {"description": "Internal server error"},
    },
)
async def get_course_lectures(
    course_id: int = Path(..., description="The ID of the course"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of lectures to return"),
    course_service: CourseApiService = Depends(get_course_api_service),
):
    """
    Get lecture briefs for a specific course.
    Returns only id, course_id, topic_id, title, and summary fields,
    excluding the large 'content' field for better performance.
    """
    # Service handles lookup and raises HTTPException on errors (if implemented)
    # We also need to handle the case where the service might just return None
    response_data = course_service.get_course_lectures(course_id, limit=limit)
    if response_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found or has no lectures.",
        )
    return response_data


@router.post(
    "/generate",
    response_model=GeneratedCourseData,
    status_code=status.HTTP_200_OK,
    summary="Generate course data",
    description="Generates AI course data. Response may be partial.",
    responses={
        500: {"description": "Course generation failed"},
    },
    dependencies=[require_coins(cost=get_settings().COIN_COST_COURSE_GENERATION)],
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
        The generated course data (not saved to the database), potentially partial.
    """
    return await course_service.generate_course(generation_data)


@router.post(
    "/generate/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue course generation job",
    description=(
        "Enqueue an async job to generate course data using AI. Returns a job id to poll via "
        "GET /api/v1/jobs/{id}."
    ),
    dependencies=[require_coins(cost=get_settings().COIN_COST_COURSE_GENERATION)],
)
async def enqueue_generate_course(
    generation_data: CourseGenerate,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Enqueue a job with kind 'generate_course'. The payload mirrors CourseGenerate.
    """
    payload = {
        "partial_attributes": generation_data.partial_attributes or {},
        "freeform_prompt": generation_data.freeform_prompt,
        "connected_course_ids": generation_data.connected_course_ids,
    }
    row = repository_factory.job.create(
        kind="generate_course",
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


@router.post(
    "/create/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue smart course creation job",
    description=(
        "Enqueue an async job that performs smart department/professor selection/generation "
        "and creates the course. Returns a job id to poll via GET /api/v1/jobs/{id}."
    ),
    dependencies=[require_role("creator")],
)
async def enqueue_create_course(
    course_data: CourseCreate,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student=Depends(ensure_student),
):
    """
    Enqueue a job with kind 'create_course'. The payload mirrors CourseCreate fields.
    """
    payload = {
        "code": course_data.code,
        "title": course_data.title,
        "department_id": course_data.department_id,
        "level": course_data.level,
        "professor_id": course_data.professor_id,
        "description": course_data.description,
        "lectures_per_week": course_data.lectures_per_week,
        "total_weeks": course_data.total_weeks,
        "connected_course_ids": course_data.connected_course_ids,
        "created_by": student.id,
        "created_with": course_data.created_with,
    }
    row = repository_factory.job.create(
        kind="create_course",
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


@router.post(
    "/{course_id}/export",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Export course with all related data and assets",
    description=(
        "Admin-only endpoint to export a complete course bundle including all related data "
        "(professor, department, topics, lectures) and assets (audio, transcripts, images). "
        "Returns a job id to poll via GET /api/v1/jobs/{id}. The job result will contain "
        "a download URL for the exported zip file."
    ),
    dependencies=[require_role("admin")],
    responses={
        202: {"description": "Export job enqueued successfully"},
        403: {"description": "Insufficient permissions (requires admin role)"},
        404: {"description": "Course not found"},
    },
)
async def export_course(
    course_id: int = Path(..., description="The ID of the course to export"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Enqueue a job to export a course with all related data and assets.

    This endpoint is restricted to admin users only. The export will include:
    - Course data
    - Professor data (including voice metadata)
    - Department data
    - All topics
    - All lectures
    - Professor image (if available)
    - Lecture audio files (if available)
    - Lecture transcripts (if available)

    The result will be a compressed zip archive stored in the exports bucket.
    """
    # Verify course exists
    course = repository_factory.course.get(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found.",
        )

    # Enqueue export job
    row = repository_factory.job.create(
        kind="export_course",
        payload={"course_id": course_id},
    )

    return {
        "id": row.id,
        "kind": row.kind,
        "status": row.status,
        "attempts": row.attempts,
        "max_attempts": row.max_attempts,
        "priority": row.priority,
        "run_after": row.run_after,
        "message": f"Course export job enqueued. Poll GET /api/v1/jobs/{row.id} for status and download URL.",
    }
