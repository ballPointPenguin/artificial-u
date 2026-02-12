"""
Lecture router for handling lecture-related API endpoints.
"""

import logging
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from artificial_u.api.dependencies import (
    ensure_student,
    get_lecture_api_service,
    get_repository_factory,
)
from artificial_u.api.models import (
    Lecture,
    LectureCreate,
    LectureGenerate,
    LectureListResponse,
    LectureUpdate,
)
from artificial_u.api.security.auth0 import require_coins, require_role
from artificial_u.api.services import LectureApiService
from artificial_u.audio import ID3Tagger
from artificial_u.config.settings import get_settings
from artificial_u.models.core import Student
from artificial_u.models.database import (
    CourseModel,
    DepartmentModel,
    LectureModel,
    ProfessorModel,
    TopicModel,
)
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.storage_service import StorageService

# -- Response model for recent/enriched lectures --


class RecentLectureResponse(BaseModel):
    """Lecture with nested course, professor, topic, and department data."""

    id: int
    title: str
    summary: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[int] = Field(None, description="Audio duration in seconds")
    course_id: int
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    topic_id: int
    topic_title: Optional[str] = None
    topic_week: Optional[int] = None
    professor_id: Optional[int] = None
    professor_name: Optional[str] = None
    professor_image_url: Optional[str] = None
    professor_accent: Optional[str] = None
    professor_specialization: Optional[str] = None
    department_name: Optional[str] = None
    created_at: Optional[str] = None


# Create the router with dependencies that will be applied to all routes
router = APIRouter(
    prefix="/lectures",
    tags=["lectures"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_lecture_api_service)],
)


@router.get(
    "",
    response_model=LectureListResponse,
    summary="List lectures",
    description="Get a paginated list of lectures with optional filtering.",
)
async def list_lectures(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    course_id: Optional[int] = Query(None, description="Filter by course ID"),
    professor_id: Optional[int] = Query(None, description="Filter by professor ID"),
    topic_id: Optional[int] = Query(None, description="Filter by topic ID"),
    search: Optional[str] = Query(None, description="Search in content and summary"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Get a paginated list of lectures with filtering options.

    - **page**: Page number (starting from 1)
    - **size**: Number of items per page (1-100)
    - **course_id**: Filter by course ID
    - **professor_id**: Filter by professor ID
    - **topic_id**: Filter by topic ID
    - **search**: Search in title and description
    """
    return lecture_service.list_lectures(
        page=page,
        size=size,
        course_id=course_id,
        professor_id=professor_id,
        topic_id=topic_id,
        search=search,
    )


@router.get(
    "/recent",
    response_model=List[RecentLectureResponse],
    summary="Get recent lectures with audio",
    description=(
        "Returns the most recently created lectures that have audio, "
        "enriched with course, professor, topic, and department info."
    ),
)
async def get_recent_lectures(
    limit: int = Query(4, ge=1, le=12, description="Number of lectures to return"),
    ids: Optional[str] = Query(
        None,
        description="Comma-separated lecture IDs to fetch (overrides limit/recency ordering)",
    ),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Get enriched lectures with nested course/professor/topic/department data.

    Two modes:
    - **Default**: returns the N most recently created lectures with audio.
    - **ids=1,2,3**: returns specific lectures by ID (for featured items).
    """
    with repository_factory.lecture.get_session() as session:
        query = (
            session.query(LectureModel)
            .outerjoin(CourseModel, LectureModel.course_id == CourseModel.id)
            .outerjoin(TopicModel, LectureModel.topic_id == TopicModel.id)
            .outerjoin(ProfessorModel, CourseModel.professor_id == ProfessorModel.id)
            .outerjoin(DepartmentModel, CourseModel.department_id == DepartmentModel.id)
        )

        if ids:
            # Fetch specific lectures by ID
            id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
            if not id_list:
                return []
            query = query.filter(LectureModel.id.in_(id_list))
        else:
            # Default: most recent with audio
            query = query.filter(LectureModel.audio_url.isnot(None))
            query = query.order_by(LectureModel.created_at.desc()).limit(limit)

        rows = query.all()

        results = []
        for lec in rows:
            course = lec.course
            topic = lec.topic
            professor = course.professor if course else None
            department = course.department if course else None

            results.append(
                RecentLectureResponse(
                    id=lec.id,
                    title=lec.title,
                    summary=lec.summary,
                    audio_url=lec.audio_url,
                    duration=lec.duration,
                    course_id=lec.course_id,
                    course_code=course.code if course else None,
                    course_title=course.title if course else None,
                    topic_id=lec.topic_id,
                    topic_title=topic.title if topic else None,
                    topic_week=topic.week if topic else None,
                    professor_id=professor.id if professor else None,
                    professor_name=professor.name if professor else None,
                    professor_image_url=professor.image_url if professor else None,
                    professor_accent=professor.accent if professor else None,
                    professor_specialization=professor.specialization if professor else None,
                    department_name=department.name if department else None,
                    created_at=str(lec.created_at) if lec.created_at else None,
                )
            )

    return results


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
    dependencies=[require_role("creator")],
)
async def create_lecture(
    lecture_data: LectureCreate,
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
    student=Depends(ensure_student),
):
    """
    Create a new lecture.

    - Request body contains all required lecture information
    - Returns the created lecture with its assigned ID
    """
    lecture = lecture_service.create_lecture(lecture_data, created_by=student.id)
    return lecture


@router.patch(
    "/{lecture_id}",
    response_model=Lecture,
    summary="Update lecture",
    description="Update an existing lecture. Only the creator or an admin can modify a lecture.",
    responses={
        404: {"description": "Lecture not found"},
        403: {"description": "Forbidden - user doesn't own this lecture"},
    },
    dependencies=[require_role("creator")],
)
async def update_lecture(
    lecture_data: LectureUpdate,
    lecture_id: int = Path(..., description="The ID of the lecture to update"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
    student: Student = Depends(ensure_student),
):
    """
    Update an existing lecture.

    - **lecture_id**: The unique identifier of the lecture to update
    - Request body contains the updated lecture information (all fields optional)
    - Returns the updated lecture
    - Requires ownership verification - only the lecture creator or admin can update
    """
    updated_lecture = lecture_service.update_lecture(
        lecture_id, lecture_data, student.id, student.role
    )
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
    description="Delete a lecture. Only the creator or an admin can delete a lecture.",
    responses={
        404: {"description": "Lecture not found"},
        403: {"description": "Forbidden - user doesn't own this lecture"},
        400: {"description": "Failed due to database issue (e.g., constraints)"},
    },
    dependencies=[require_role("creator")],
)
async def delete_lecture(
    lecture_id: int = Path(..., description="The ID of the lecture to delete"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
    student: Student = Depends(ensure_student),
):
    """
    Delete a lecture.

    - **lecture_id**: The unique identifier of the lecture to delete
    - Returns no content on successful deletion
    - Requires ownership verification - only the lecture creator or admin can delete
    """
    success = lecture_service.delete_lecture(lecture_id, student.id, student.role)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lecture with ID {lecture_id} not found (delete operation failed).",
        )
    # For 204 No Content, we should not return any response body
    # FastAPI will handle the 204 status code automatically based on the decorator


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
    "/{lecture_id}/generate-audio",
    response_model=Lecture,
    status_code=status.HTTP_200_OK,
    summary="Generate lecture audio",
    description=(
        "Triggers generation of audio for the specified lecture and returns the updated lecture. "
        "Only the creator or an admin can modify a lecture."
    ),
    responses={
        404: {"description": "Lecture not found"},
        403: {"description": "Forbidden - user doesn't own this lecture"},
        500: {"description": "Audio generation failed"},
    },
    dependencies=[require_coins(cost=get_settings().COIN_COST_LECTURE_AUDIO)],
)
async def generate_lecture_audio(
    lecture_id: int = Path(..., description="The ID of the lecture to generate audio for"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
    student: Student = Depends(ensure_student),
):
    """
    Generate audio for a specific lecture.

    - **lecture_id**: The unique identifier of the lecture
    - Triggers an audio generation process and returns the updated lecture
    - Requires ownership verification - only the lecture creator or admin can generate audio
    """
    return await lecture_service.generate_lecture_audio(lecture_id, student.id, student.role)


@router.post(
    "/{lecture_id}/generate-audio/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue lecture audio generation job",
    description=(
        "Enqueue an async job to generate audio for a lecture. Returns a job id to poll via "
        "GET /api/v1/jobs/{id}. Only the creator or an admin can modify a lecture."
    ),
    responses={
        404: {"description": "Lecture not found"},
        403: {"description": "Forbidden - user doesn't own this lecture"},
    },
    dependencies=[require_coins(cost=get_settings().COIN_COST_LECTURE_AUDIO)],
)
async def enqueue_generate_lecture_audio(
    lecture_id: int = Path(..., description="The ID of the lecture to generate audio for"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    # Look up the lecture and verify ownership
    lecture = repository_factory.lecture.get(lecture_id)
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Lecture {lecture_id} not found"
        )

    # Verify ownership
    from artificial_u.api.security.auth0 import verify_asset_ownership

    verify_asset_ownership(student.id, lecture.created_by, student.role, "lecture")

    payload = {"lecture_id": lecture_id}
    if lecture.topic_id:
        payload["topic_id"] = lecture.topic_id

    row = repository_factory.job.create(
        kind="generate_lecture_audio",
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
    "/{lecture_id}/upload-audio",
    response_model=Lecture,
    status_code=status.HTTP_200_OK,
    summary="Upload audio file for lecture",
    description=(
        "Upload an MP3 audio file for the specified lecture. The audio will be processed "
        "with ID3 metadata tags and saved to storage. Admin only."
    ),
    responses={
        404: {"description": "Lecture not found"},
        400: {"description": "Invalid file or upload failed"},
        403: {"description": "Admin access required"},
    },
    dependencies=[require_role("admin")],
)
async def upload_lecture_audio(
    lecture_id: int = Path(..., description="The ID of the lecture to upload audio for"),
    file: UploadFile = File(..., description="MP3 audio file to upload"),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Upload an MP3 audio file for a specific lecture (admin only).

    - **lecture_id**: The unique identifier of the lecture
    - **file**: MP3 audio file to upload
    - Processes the audio with ID3 metadata tags
    - Uploads to S3 storage with proper naming
    - Returns the updated lecture with audio_url
    """
    logger = logging.getLogger(__name__)

    # 1. Verify lecture exists and get related entities
    lecture = repository_factory.lecture.get(lecture_id)
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Lecture {lecture_id} not found"
        )

    # Validate file type
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio file (MP3 recommended)",
        )

    try:
        # 2. Read the uploaded file
        audio_bytes = await file.read()
        logger.info(f"Received audio upload: {len(audio_bytes)} bytes for lecture {lecture_id}")

        # 3. Get course and topic for metadata and naming
        course = repository_factory.course.get(lecture.course_id)
        topic = repository_factory.topic.get(lecture.topic_id) if lecture.topic_id else None

        if not course:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lecture must be associated with a valid course",
            )

        if not topic:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lecture must be associated with a valid topic",
            )

        # 4. Add ID3 tags
        tagger = ID3Tagger(logger=logger)

        # Calculate track number based on topic position
        track_number = tagger.calculate_track_number(
            topic_week=topic.week,
            topic_order=topic.order,
            course_id=course.id,
            repository_factory=repository_factory,
        )

        # Generate comment indicating uploaded file
        model_name = getattr(lecture, "created_with", None)
        comment = tagger.generate_comment(
            model_name=model_name,
            include_elevenlabs=True,
        )

        # Add tags to audio
        tagged_audio = tagger.add_tags_to_audio(
            audio_bytes=audio_bytes,
            title=lecture.title or f"Lecture {topic.week}.{topic.order}",
            album=course.title,
            track_number=track_number,
            year=lecture.created_at.year if hasattr(lecture, "created_at") else None,
            comment=comment if comment else None,
        )

        logger.info(f"Added ID3 tags to uploaded audio: {len(tagged_audio)} bytes")

        # 5. Upload to S3 with proper naming
        storage_service = StorageService(logger=logger)
        course_code = getattr(course, "code", str(course.id))
        object_key = storage_service.generate_audio_key(
            course_code=str(course_code),
            week_number=int(topic.week),
            lecture_order=int(topic.order),
        )

        success, audio_url = await storage_service.upload_audio_file(
            file_data=tagged_audio,
            object_name=object_key,
            content_type="audio/mpeg",
        )

        if not success or not audio_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload audio to storage",
            )

        logger.info(f"Uploaded audio to {audio_url}")

        # 5b. Extract audio duration
        duration_seconds = tagger.get_duration_seconds(tagged_audio)

        # 6. Update lecture with audio_url and duration
        lecture.audio_url = audio_url
        lecture.duration = duration_seconds
        updated_lecture = repository_factory.lecture.update(lecture)

        if not updated_lecture:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update lecture with audio URL",
            )

        logger.info(f"Updated lecture {lecture_id} with audio URL")

        return updated_lecture

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading audio for lecture {lecture_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process audio upload: {str(e)}",
        )


@router.post(
    "/{lecture_id}/generate-summary",
    response_model=Lecture,
    status_code=status.HTTP_200_OK,
    summary="Generate lecture summary",
    description=(
        "Triggers generation of a concise summary for the specified lecture and returns "
        "the updated lecture."
    ),
    responses={
        404: {"description": "Lecture not found"},
        500: {"description": "Summary generation failed"},
    },
    dependencies=[require_coins(cost=get_settings().COIN_COST_LECTURE_SUMMARY)],
)
async def generate_lecture_summary(
    lecture_id: int = Path(..., description="The ID of the lecture to generate a summary for"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Generate a summary for a specific lecture.

    - **lecture_id**: The unique identifier of the lecture
    - Triggers the summary generation process and returns the updated lecture
    """
    return await lecture_service.generate_lecture_summary(lecture_id)


@router.delete(
    "/{lecture_id}/summary",
    response_model=Lecture,
    status_code=status.HTTP_200_OK,
    summary="Clear lecture summary",
    description="Clears the summary for a lecture. Admin only.",
    responses={
        404: {"description": "Lecture not found"},
        403: {"description": "Forbidden - admin access required"},
    },
    dependencies=[require_role("admin")],
)
async def clear_lecture_summary(
    lecture_id: int = Path(..., description="The ID of the lecture to clear the summary for"),
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Clear the summary for a specific lecture.

    - **lecture_id**: The unique identifier of the lecture
    - Returns the updated lecture with summary cleared
    - Admin only
    """
    return await lecture_service.clear_lecture_summary(lecture_id)


@router.post(
    "/generate",
    response_model=Lecture,
    status_code=status.HTTP_200_OK,
    summary="Generate lecture data",
    description="Generates lecture data using AI based on partial attributes.",
    responses={
        500: {"description": "Lecture generation failed"},
    },
    dependencies=[require_coins(cost=get_settings().COIN_COST_LECTURE_GENERATION)],
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


@router.post(
    "/generate/text-only",
    response_model=Lecture,
    status_code=status.HTTP_200_OK,
    summary="Generate lecture text only",
    description=(
        "Generates lecture text content using AI based on partial attributes, "
        "without automatically enqueueing audio or summary generation jobs."
    ),
    responses={
        500: {"description": "Lecture text generation failed"},
    },
    dependencies=[require_coins(cost=get_settings().COIN_COST_LECTURE_GENERATION)],
)
async def generate_lecture_text_only(
    generation_data: LectureGenerate,
    lecture_service: LectureApiService = Depends(get_lecture_api_service),
):
    """
    Generate lecture text content using AI.

    This endpoint generates only the lecture text content and saves it to the database,
    without automatically triggering audio or summary generation jobs.

    Args:
        generation_data: Contains optional partial_attributes and freeform_prompt.

    Returns:
        The generated and saved lecture data.
    """
    return await lecture_service.generate_lecture_text_only(generation_data)


@router.post(
    "/generate/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue lecture generation job",
    description=(
        "Enqueue an async job to generate lecture data using AI. Returns a job id to poll via "
        "GET /api/v1/jobs/{id}."
    ),
    dependencies=[require_coins(cost=get_settings().COIN_COST_LECTURE_GENERATION)],
)
async def enqueue_generate_lecture(
    generation_data: LectureGenerate,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student=Depends(ensure_student),
):
    """
    Enqueue a job with kind 'generate_lecture'. Payload mirrors LectureGenerate.
    """
    # Create a new dict to avoid modifying the input
    partial_attrs = dict(generation_data.partial_attributes or {})
    # Add created_by to partial attributes
    partial_attrs["created_by"] = student.id

    payload = {
        "partial_attributes": partial_attrs,
        "freeform_prompt": generation_data.freeform_prompt,
    }
    # Don't filter out partial_attributes even if it's just {"created_by": ...}
    if payload.get("freeform_prompt") is None:
        payload.pop("freeform_prompt", None)

    row = repository_factory.job.create(
        kind="generate_lecture",
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
    "/generate/text-only/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue lecture text generation job",
    description=(
        "Enqueue an async job to generate lecture text content using AI, "
        "without automatically enqueueing audio or summary generation. "
        "Returns a job id to poll via GET /api/v1/jobs/{id}."
    ),
    dependencies=[require_coins(cost=get_settings().COIN_COST_LECTURE_GENERATION)],
)
async def enqueue_generate_lecture_text_only(
    generation_data: LectureGenerate,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student=Depends(ensure_student),
):
    """
    Enqueue a job with kind 'generate_lecture_text_only'. Payload mirrors LectureGenerate.
    This job will generate only the lecture text without triggering audio/summary jobs.
    """
    # Create a new dict to avoid modifying the input
    partial_attrs = dict(generation_data.partial_attributes or {})
    # Add created_by to partial attributes
    partial_attrs["created_by"] = student.id

    payload = {
        "partial_attributes": partial_attrs,
        "freeform_prompt": generation_data.freeform_prompt,
    }
    # Don't filter out partial_attributes even if it's just {"created_by": ...}
    if payload.get("freeform_prompt") is None:
        payload.pop("freeform_prompt", None)

    row = repository_factory.job.create(
        kind="generate_lecture_text_only",
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
