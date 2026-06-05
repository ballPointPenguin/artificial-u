"""
Quickstart router for the wizard-based course creation flow.

This router provides endpoints for the "easy mode" course creation experience,
guiding users through a simplified flow:
1. Match user's learning goal to existing courses or signal new course creation
2. Review and approve the assigned professor
3. Finalize and kick off content generation
"""

import base64
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from artificial_u.api.dependencies import (
    ensure_student,
    get_content_service,
    get_course_api_service,
    get_course_service,
    get_professor_service,
    get_repository_factory,
    get_voice_service,
)
from artificial_u.api.models.quickstart import (
    CourseBrief,
    IntroAudioRequest,
    IntroAudioResponse,
    ProfessorDetail,
    QuickstartFinalizeRequest,
    QuickstartFinalizeResponse,
    QuickstartMatchRequest,
    QuickstartMatchResponse,
    QuickstartProfessorActionRequest,
    QuickstartProfessorResponse,
    QuickstartRegenerateProfessorRequest,
    QuickstartStartRequest,
    QuickstartStartResponse,
)
from artificial_u.api.security.auth0 import require_coins, require_role
from artificial_u.api.services import CourseApiService
from artificial_u.config.settings import get_settings
from artificial_u.integrations.tts import create_tts_backend
from artificial_u.models.core import Student
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services import (
    ContentService,
    CourseService,
    ProfessorService,
    VoiceService,
)
from artificial_u.services.course_selector_service import CourseSelectorService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/quickstart",
    tags=["quickstart"],
    responses={404: {"description": "Not found"}},
)


def get_course_selector_service(
    content_service: ContentService = Depends(get_content_service),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
) -> CourseSelectorService:
    """Get a course selector service instance."""
    return CourseSelectorService(
        content_service=content_service,
        repository_factory=repository_factory,
        logger=logging.getLogger("artificial_u.services.course_selector_service"),
    )


@router.post(
    "/match-courses",
    response_model=QuickstartMatchResponse,
    summary="Match learning goal to existing courses",
    description=(
        "Uses AI to match the user's learning goal against existing published courses. "
        "Returns matching courses or signals that a new course should be generated."
    ),
    dependencies=[require_role("creator")],
)
async def match_courses(
    request: QuickstartMatchRequest,
    course_selector: CourseSelectorService = Depends(get_course_selector_service),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Match user's learning goal to existing published courses.

    This is the first step in the quickstart wizard. The AI will analyze the
    user's query and either recommend existing courses or signal that a new
    course should be generated.
    """
    try:
        result = await course_selector.match_courses(request.query)

        # Convert courses to brief format
        matched_courses = []
        for course in result.get("courses", []):
            professor_name = None
            professor_image_url = None
            if course.professor_id:
                professor = repository_factory.professor.get(course.professor_id)
                if professor:
                    professor_name = professor.name
                    professor_image_url = professor.image_url

            matched_courses.append(
                CourseBrief(
                    id=course.id,
                    code=course.code,
                    title=course.title,
                    description=course.description or "",
                    professor_name=professor_name,
                    professor_image_url=professor_image_url,
                )
            )

        return QuickstartMatchResponse(
            action=result["action"],
            matched_courses=matched_courses,
            reasoning=result["reasoning"],
        )

    except Exception as e:
        logger.error(f"Error matching courses: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to match courses: {str(e)}",
        )


@router.post(
    "/start",
    response_model=QuickstartStartResponse,
    summary="Start quickstart course creation",
    description=(
        "Creates a new course based on the user's learning goal with smart department "
        "and professor selection. Returns the created course with assigned professor."
    ),
    dependencies=[require_role("creator")],
)
async def start_quickstart(
    request: QuickstartStartRequest,
    course_api_service: CourseApiService = Depends(get_course_api_service),
    course_service: CourseService = Depends(get_course_service),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Start the quickstart course creation flow.

    This creates a new course using AI generation and smart selection for
    department and professor. The course is created with 'hidden' status
    and will be published after the user approves the professor and first lecture.
    """
    from artificial_u.api.models.courses import CourseGenerate

    try:
        # Generate course data using AI via the API service
        generation_request = CourseGenerate(freeform_prompt=request.query)
        generated_data = await course_api_service.generate_course(generation_request)

        # Create course using smart selection (handles department and professor)
        # The create_course method handles smart selection when department_id/professor_id are None
        # Quickstart courses always use 1 lecture per week and 12 weeks for consistency
        created_course, professor = await course_service.create_course(
            title=generated_data.title or "Quickstart Course",
            code=generated_data.code or "QS001",
            level=generated_data.level or "Undergraduate",
            weeks=12,
            lectures_per_week=1,
            department_id=None,  # Smart selection will handle this
            professor_id=None,  # Smart selection will handle this
            description=generated_data.description or request.query,
            created_by=student.id,
            created_with=generated_data.created_with,
            language=request.language,
        )

        # Set course to hidden status (will be published after user approval)
        created_course.status = "hidden"
        repository_factory.course.update(created_course)

        return QuickstartStartResponse(
            course_id=created_course.id,
            professor_id=professor.id,
            department_id=created_course.department_id,
            course_title=created_course.title,
            course_code=created_course.code,
            course_description=created_course.description or "",
        )

    except Exception as e:
        logger.error(f"Error starting quickstart: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start quickstart: {str(e)}",
        )


@router.post(
    "/start/enqueue",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue quickstart course creation job",
    description=(
        "Enqueues an async job to create a course based on the user's learning goal. "
        "Returns a job id to poll via GET /api/v1/jobs/{id}. Use this instead of /start "
        "for production to avoid CloudFront/ALB timeouts on long-running AI operations."
    ),
    dependencies=[require_role("creator")],
)
async def enqueue_start_quickstart(
    request: QuickstartStartRequest,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Enqueue the quickstart course creation as a background job.

    This is the recommended approach for production deployments where CloudFront
    enforces a 30-second timeout. The job will:
    1. Generate course data from the user's query using AI
    2. Create the course with smart department/professor selection
    3. Return course details in the job result

    Poll GET /api/v1/jobs/{id} to check status. When status is 'done', the result
    will contain: course_id, professor_id, department_id, course_title, course_code,
    course_description.
    """
    payload = {
        "query": request.query,
        "created_by": student.id,
        "language": request.language,
    }
    row = repository_factory.job.create(kind="quickstart_start", payload=payload)
    return {
        "id": row.id,
        "kind": row.kind,
        "status": row.status,
        "attempts": row.attempts,
        "max_attempts": row.max_attempts,
        "priority": row.priority,
        "run_after": row.run_after,
    }


@router.get(
    "/professor/{professor_id}",
    response_model=QuickstartProfessorResponse,
    summary="Get professor details for review",
    description="Get detailed professor information for the quickstart review step.",
    dependencies=[require_role("creator")],
)
async def get_professor_for_review(
    professor_id: int,
    course_id: int,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Get professor details for the quickstart review step.

    Returns the professor's information including voice preview URL for
    the user to approve before proceeding with content generation.
    """
    professor = repository_factory.professor.get(professor_id)
    if not professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor with ID {professor_id} not found",
        )

    course = repository_factory.course.get(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found",
        )

    # Get voice preview URL if voice is assigned
    voice_preview_url = None
    if professor.voice_id:
        voice = repository_factory.voice.get(professor.voice_id)
        if voice:
            voice_preview_url = voice.preview_url

    return QuickstartProfessorResponse(
        professor=ProfessorDetail(
            id=professor.id,
            name=professor.name,
            title=professor.title,
            specialization=professor.specialization,
            description=professor.description,
            personality=professor.personality,
            teaching_style=professor.teaching_style,
            background=professor.background,
            gender=professor.gender,
            age=professor.age,
            accent=professor.accent,
            image_url=professor.image_url,
            voice_preview_url=voice_preview_url,
            voice_id=professor.voice_id,
        ),
        course_id=course.id,
        course_title=course.title,
    )


@router.post(
    "/generate-intro-audio",
    response_model=IntroAudioResponse,
    summary="Generate professor intro audio",
    description=(
        "Generates an ephemeral audio clip of the professor introducing themselves. "
        "The audio is returned as a base64 data URI and is not persisted."
    ),
    dependencies=[require_role("creator")],
)
async def generate_intro_audio(
    request: IntroAudioRequest,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Generate an ephemeral intro audio clip for a professor.

    Creates a short audio clip of the professor saying something like:
    "Hello, my name is Dr. Smith and I'll be teaching Introduction to AI."

    The audio is returned as a base64 data URI and is not stored.
    Uses whichever TTS backend is configured for the professor's voice.
    """
    professor = repository_factory.professor.get(request.professor_id)
    if not professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor with ID {request.professor_id} not found",
        )

    if not professor.voice_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Professor does not have an assigned voice",
        )

    voice = repository_factory.voice.get(professor.voice_id)
    if not voice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Professor's voice is not properly configured",
        )

    # Resolve the voice identifier and backend
    voice_identifier = voice.external_id or voice.el_voice_id
    if not voice_identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Professor's voice has no external identifier configured",
        )

    # Professor-level backend override takes priority, then voice's backend
    backend_name = professor.tts_backend or voice.tts_backend or "elevenlabs"

    try:
        backend = create_tts_backend(backend_name=backend_name, logger=logger)
    except (ValueError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"TTS backend '{backend_name}' is not available: {e}",
        )

    # Generate the intro text
    intro_text = f"Hello, my name is {professor.name} and I'll be teaching {request.course_title}."

    try:
        audio_bytes = backend.text_to_speech(
            text=intro_text,
            voice_id=voice_identifier,
        )

        # Convert to base64 data URI
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        audio_data_uri = f"data:audio/mp3;base64,{audio_base64}"

        return IntroAudioResponse(
            audio_data_uri=audio_data_uri,
            text=intro_text,
        )

    except Exception as e:
        logger.error(f"Error generating intro audio: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate intro audio: {str(e)}",
        )


@router.post(
    "/regenerate-professor-image",
    response_model=QuickstartProfessorResponse,
    summary="Regenerate professor image",
    description="Regenerates the professor's image while keeping other attributes.",
    dependencies=[require_coins(cost=get_settings().COIN_COST_PROFESSOR_IMAGE)],
)
async def regenerate_professor_image(
    request: QuickstartProfessorActionRequest,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Regenerate the professor's image.

    Enqueues a job to generate a new image for the professor.
    Returns the professor details (image_url will be updated asynchronously).
    """
    from artificial_u.api.security.auth0 import verify_asset_ownership

    professor = repository_factory.professor.get(request.professor_id)
    if not professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor with ID {request.professor_id} not found",
        )

    # Verify ownership
    verify_asset_ownership(student.id, professor.created_by, student.role, "professor")

    course = repository_factory.course.get(request.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {request.course_id} not found",
        )

    # Enqueue image generation job
    job = repository_factory.job.create(
        kind="generate_professor_image",
        payload={"professor_id": request.professor_id},
    )
    logger.info(f"Enqueued professor image generation job {job.id}")

    # Get voice preview URL
    voice_preview_url = None
    if professor.voice_id:
        voice = repository_factory.voice.get(professor.voice_id)
        if voice:
            voice_preview_url = voice.preview_url

    return QuickstartProfessorResponse(
        professor=ProfessorDetail(
            id=professor.id,
            name=professor.name,
            title=professor.title,
            specialization=professor.specialization,
            description=professor.description,
            personality=professor.personality,
            teaching_style=professor.teaching_style,
            background=professor.background,
            gender=professor.gender,
            age=professor.age,
            accent=professor.accent,
            image_url=professor.image_url,  # Will be updated by job
            voice_preview_url=voice_preview_url,
            voice_id=professor.voice_id,
        ),
        course_id=course.id,
        course_title=course.title,
    )


@router.post(
    "/reassign-professor-voice",
    response_model=QuickstartProfessorResponse,
    summary="Reassign professor voice",
    description="Reassigns a voice to the professor using the voice mapping algorithm.",
    dependencies=[require_role("creator")],
)
async def reassign_professor_voice(
    request: QuickstartProfessorActionRequest,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    voice_service: VoiceService = Depends(get_voice_service),
    student: Student = Depends(ensure_student),
):
    """
    Reassign a voice to the professor.

    Uses the VoiceMapper to select a new appropriate voice based on
    the professor's attributes (gender, accent, age).
    """
    from artificial_u.api.security.auth0 import verify_asset_ownership

    professor = repository_factory.professor.get(request.professor_id)
    if not professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor with ID {request.professor_id} not found",
        )

    # Verify ownership
    verify_asset_ownership(student.id, professor.created_by, student.role, "professor")

    course = repository_factory.course.get(request.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {request.course_id} not found",
        )

    try:
        # Reassign voice using the voice service
        updated_professor = voice_service.assign_voice_to_professor(professor)

        if not updated_professor:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reassign voice",
            )

        # Get voice preview URL
        voice_preview_url = None
        if updated_professor.voice_id:
            voice = repository_factory.voice.get(updated_professor.voice_id)
            if voice:
                voice_preview_url = voice.preview_url

        return QuickstartProfessorResponse(
            professor=ProfessorDetail(
                id=updated_professor.id,
                name=updated_professor.name,
                title=updated_professor.title,
                specialization=updated_professor.specialization,
                description=updated_professor.description,
                personality=updated_professor.personality,
                teaching_style=updated_professor.teaching_style,
                background=updated_professor.background,
                gender=updated_professor.gender,
                age=updated_professor.age,
                accent=updated_professor.accent,
                image_url=updated_professor.image_url,
                voice_preview_url=voice_preview_url,
                voice_id=updated_professor.voice_id,
            ),
            course_id=course.id,
            course_title=course.title,
        )

    except Exception as e:
        logger.error(f"Error reassigning voice: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reassign voice: {str(e)}",
        )


@router.post(
    "/regenerate-professor",
    response_model=QuickstartProfessorResponse,
    summary="Regenerate professor",
    description="Generates a new professor for the course with optional freeform guidance.",
    dependencies=[require_coins(cost=get_settings().COIN_COST_PROFESSOR_GENERATION)],
)
async def regenerate_professor(
    request: QuickstartRegenerateProfessorRequest,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    professor_service: ProfessorService = Depends(get_professor_service),
    content_service: ContentService = Depends(get_content_service),
    student: Student = Depends(ensure_student),
):
    """
    Regenerate the professor for a course.

    Creates a new professor (with voice and image) and assigns them to the course.
    The old professor is not deleted (they may be used by other courses).
    """
    from artificial_u.api.security.auth0 import verify_asset_ownership
    from artificial_u.models.core import Professor
    from artificial_u.services.professor_generator_service import (
        ProfessorGeneratorService,
    )

    course = repository_factory.course.get(request.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {request.course_id} not found",
        )

    # Verify ownership
    verify_asset_ownership(student.id, course.created_by, student.role, "course")

    try:
        # Generate new professor
        from artificial_u.api.dependencies import (
            get_http_client,
            get_image_service,
            get_job_enqueue_service,
            get_storage_service,
        )

        image_service = get_image_service(get_storage_service(), get_http_client())
        job_enqueue_service = get_job_enqueue_service(repository_factory)

        professor_generator = ProfessorGeneratorService(
            professor_service=professor_service,
            content_service=content_service,
            image_service=image_service,
            repository_factory=repository_factory,
            job_enqueue_service=job_enqueue_service,
            logger=logging.getLogger("artificial_u.services.professor_generator_service"),
        )

        # Generate professor attributes
        generated_attrs = await professor_generator.generate_professor(
            partial_attributes={
                "department_id": request.department_id,
            },
            freeform_prompt=request.freeform_prompt,
        )

        # Create professor
        new_professor = Professor(
            name=generated_attrs["name"],
            title=generated_attrs["title"],
            department_id=request.department_id,
            specialization=generated_attrs["specialization"],
            gender=generated_attrs.get("gender"),
            age=generated_attrs.get("age"),
            accent=generated_attrs.get("accent"),
            description=generated_attrs.get("description"),
            background=generated_attrs.get("background"),
            personality=generated_attrs.get("personality"),
            teaching_style=generated_attrs.get("teaching_style"),
            created_by=student.id,
            created_with=generated_attrs.get("created_with"),
        )

        created_professor = professor_service.create_professor(new_professor)

        # Update course to use new professor
        course.professor_id = created_professor.id
        repository_factory.course.update(course)

        # Get voice preview URL
        voice_preview_url = None
        if created_professor.voice_id:
            voice = repository_factory.voice.get(created_professor.voice_id)
            if voice:
                voice_preview_url = voice.preview_url

        return QuickstartProfessorResponse(
            professor=ProfessorDetail(
                id=created_professor.id,
                name=created_professor.name,
                title=created_professor.title,
                specialization=created_professor.specialization,
                description=created_professor.description,
                personality=created_professor.personality,
                teaching_style=created_professor.teaching_style,
                background=created_professor.background,
                gender=created_professor.gender,
                age=created_professor.age,
                accent=created_professor.accent,
                image_url=created_professor.image_url,
                voice_preview_url=voice_preview_url,
                voice_id=created_professor.voice_id,
            ),
            course_id=course.id,
            course_title=course.title,
        )

    except Exception as e:
        logger.error(f"Error regenerating professor: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate professor: {str(e)}",
        )


@router.post(
    "/finalize",
    response_model=QuickstartFinalizeResponse,
    summary="Finalize quickstart and generate content",
    description=(
        "Finalizes the quickstart flow by kicking off topic and lecture generation. "
        "The first lecture will be automatically generated after topics are ready."
    ),
    dependencies=[require_role("creator")],
)
async def finalize_quickstart(
    request: QuickstartFinalizeRequest,
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
    student: Student = Depends(ensure_student),
):
    """
    Finalize the quickstart flow and start content generation.

    This kicks off:
    1. Topic generation for the course
    2. First lecture generation (will be chained after topics complete)

    The course remains hidden until explicitly published.
    """
    from artificial_u.api.security.auth0 import verify_asset_ownership

    course = repository_factory.course.get(request.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {request.course_id} not found",
        )

    # Verify ownership
    verify_asset_ownership(student.id, course.created_by, student.role, "course")

    # Enqueue topic generation job with follow-up to generate first lecture
    job = repository_factory.job.create(
        kind="generate_topics_for_course",
        payload={
            "course_id": request.course_id,
            "generate_first_lecture": True,  # Signal to generate first lecture after topics
        },
    )
    logger.info(f"Enqueued topic generation job {job.id} for course {request.course_id}")

    return QuickstartFinalizeResponse(
        course_id=course.id,
        topics_job_id=job.id,
        message=(
            f"Content generation started! Topics and the first lecture will be generated "
            f"for '{course.title}'. You can track progress on the course page."
        ),
    )
