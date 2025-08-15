import logging
from typing import Any, Dict, Optional

from artificial_u.models.repositories.factory import RepositoryFactory


class JobService:
    """
    Central job dispatcher and utility helpers for backoff scheduling.

    Provides a single entrypoint `dispatch(kind, payload)` that routes to
    domain services. Also exposes `compute_backoff_seconds` for retry logic.
    """

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        logger: Optional[logging.Logger] = None,
    ):
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)

        # Lazily initialized service instances
        self._content_service = None
        self._storage_service = None
        self._image_service = None
        self._voice_service = None
        self._job_enqueue_service = None
        self._professor_service = None
        self._professor_generator_service = None
        self._course_service = None
        self._course_generator_service = None
        self._department_service = None
        self._department_generator_service = None
        self._topic_service = None
        self._topic_generator_service = None
        self._lecture_service = None
        self._lecture_generator_service = None

    # ---- Public API ----

    async def dispatch(self, kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a job by kind to the appropriate handler. Returns a JSON-serializable result.
        """
        self.logger.info(
            f"Dispatching job of kind '{kind}' with payload keys: {list(payload.keys())}"
        )
        handler = self._get_handler(kind)
        if not handler:
            error_msg = f"No handler for kind={kind}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.debug(f"Found handler for kind '{kind}', executing...")
        try:
            result = await handler(payload)
            self.logger.info(f"Job kind '{kind}' completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Job kind '{kind}' failed: {e}", exc_info=True)
            raise

    @staticmethod
    def compute_backoff_seconds(attempts: int) -> float:
        import random

        base = min(2**attempts, 60)
        jitter = random.uniform(0, 0.25 * base)
        return base + jitter

    # ---- Handlers ----

    def _get_handler(self, kind: str):
        return {
            # Generation tasks (lightweight return values; some persist internally)
            "generate_course": self._handle_generate_course,
            "create_course": self._handle_create_course,
            "generate_department": self._handle_generate_department,
            "generate_professor": self._handle_generate_professor,
            "generate_topics_for_course": self._handle_generate_topics_for_course,
            "generate_lecture": self._handle_generate_lecture,
            "generate_lecture_summary": self._handle_generate_lecture_summary,
            "generate_lecture_audio": self._handle_generate_lecture_audio,
            "generate_professor_image": self._handle_generate_professor_image,
        }.get(kind)

    async def _handle_generate_course(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        service = self._course_generator_service_instance()
        partial = payload.get("partial_attributes") or {}
        result = await service.generate_course(partial)
        return {"generated_course": result}

    async def _handle_create_course(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a course using smart department/professor selection/generation.

        Expects payload with fields matching CourseService.create_course signature.
        Accepts either 'weeks' or 'total_weeks' for compatibility with API schema.
        """
        service = self._course_service_instance()

        # Payload normalization
        title = payload.get("title")
        code = payload.get("code")
        level = payload.get("level")
        credits = payload.get("credits", 3)
        weeks = payload.get("weeks", payload.get("total_weeks", 12))
        lectures_per_week = payload.get("lectures_per_week", 1)
        department_id = payload.get("department_id")
        professor_id = payload.get("professor_id")
        description = payload.get("description")

        if not title or not code or not level:
            raise ValueError("title, code, and level are required to create a course")

        course, professor = await service.create_course(
            title=title,
            code=code,
            level=level,
            credits=credits,
            weeks=weeks,
            lectures_per_week=lectures_per_week,
            department_id=department_id,
            professor_id=professor_id,
            description=description,
        )

        return {
            "course_id": course.id,
            "department_id": course.department_id,
            "professor_id": professor.id,
        }

    async def _handle_generate_department(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        service = self._department_generator_service_instance()
        partial = payload.get("partial_attributes") or {}
        result = await service.generate_department(partial)
        return {"generated_department": result}

    async def _handle_generate_professor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        service = self._professor_generator_service_instance()
        partial = payload.get("partial_attributes") or {}
        result = await service.generate_professor(partial)
        return {"generated_professor": result}

    async def _handle_generate_topics_for_course(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        service = self._topic_generator_service_instance()
        course_id = payload.get("course_id")
        freeform = payload.get("freeform_prompt")
        if course_id is None:
            raise ValueError("course_id is required")
        topics = await service.generate_topics_for_course(course_id, freeform)
        # Convert Topic models to minimal dicts
        return {
            "created_topics": [
                {
                    "id": t.id,
                    "title": t.title,
                    "course_id": t.course_id,
                    "week": t.week,
                    "order": t.order,
                }
                for t in topics
            ]
        }

    async def _handle_generate_lecture(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        service = self._lecture_generator_service_instance()
        partial = payload.get("partial_attributes") or {}
        self.logger.info(f"Generating and saving lecture with partial attributes: {partial}")

        # Use the new generate_and_save_lecture method for complete processing
        saved_lecture = await service.generate_and_save_lecture(partial)

        self.logger.info(f"Generate and save lecture completed: {saved_lecture.id}")
        return {
            "lecture_id": saved_lecture.id,
            "course_id": saved_lecture.course_id,
            "topic_id": saved_lecture.topic_id,
            "title": saved_lecture.title,
            "transcript_url": saved_lecture.transcript_url,
        }

    async def _handle_generate_lecture_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        service = self._lecture_generator_service_instance()
        lecture_id = payload.get("lecture_id")
        if lecture_id is None:
            raise ValueError("lecture_id is required")
        result = await service.generate_lecture_summary(lecture_id)
        return result

    async def _handle_generate_lecture_audio(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        service = self._lecture_generator_service_instance()
        lecture_id = payload.get("lecture_id")
        if lecture_id is None:
            raise ValueError("lecture_id is required")
        result = await service.generate_lecture_audio(lecture_id)
        return result

    async def _handle_generate_professor_image(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        service = self._professor_generator_service_instance()
        professor_id = payload.get("professor_id")
        aspect_ratio = payload.get("aspect_ratio", "1:1")
        if professor_id is None:
            raise ValueError("professor_id is required")
        updated = await service.generate_and_set_professor_image(
            professor_id=professor_id, aspect_ratio=aspect_ratio
        )
        return {"professor_id": updated.id, "image_url": getattr(updated, "image_url", None)}

    # ---- Service builders (lazy) ----

    def _content_service_instance(self):
        if self._content_service is None:
            from artificial_u.services.content_service import ContentService

            self._content_service = ContentService(
                logger=self.logger,
            )
        return self._content_service

    def _storage_service_instance(self):
        if self._storage_service is None:
            from artificial_u.services.storage_service import StorageService

            self._storage_service = StorageService(logger=self.logger)
        return self._storage_service

    def _image_service_instance(self):
        if self._image_service is None:
            from artificial_u.services.image_service import ImageService

            self._image_service = ImageService(
                storage_service=self._storage_service_instance(),
            )
        return self._image_service

    def _voice_service_instance(self):
        if self._voice_service is None:
            from artificial_u.services.voice_service import VoiceService

            # Create ElevenLabs client with API key if available
            elevenlabs_client = self._get_elevenlabs_client()

            self._voice_service = VoiceService(
                repository_factory=self.repository_factory,
                client=elevenlabs_client,
                logger=self.logger,
            )
        return self._voice_service

    def _job_enqueue_service_instance(self):
        if self._job_enqueue_service is None:
            from artificial_u.services.job_enqueue_service import JobEnqueueService

            self._job_enqueue_service = JobEnqueueService(
                repository_factory=self.repository_factory,
                logger=self.logger,
            )
        return self._job_enqueue_service

    def _professor_service_instance(self):
        if self._professor_service is None:
            from artificial_u.services.professor_service import ProfessorService

            self._professor_service = ProfessorService(
                repository_factory=self.repository_factory,
                voice_service=self._voice_service_instance(),
                job_enqueue_service=self._job_enqueue_service_instance(),
                logger=self.logger,
            )
        return self._professor_service

    def _professor_generator_service_instance(self):
        if self._professor_generator_service is None:
            from artificial_u.services.professor_generator_service import ProfessorGeneratorService

            self._professor_generator_service = ProfessorGeneratorService(
                professor_service=self._professor_service_instance(),
                content_service=self._content_service_instance(),
                image_service=self._image_service_instance(),
                repository_factory=self.repository_factory,
                job_enqueue_service=self._job_enqueue_service_instance(),
                logger=self.logger,
            )
        return self._professor_generator_service

    def _course_service_instance(self):
        if self._course_service is None:
            from artificial_u.services.course_service import CourseService

            self._course_service = CourseService(
                repository_factory=self.repository_factory,
                professor_service=self._professor_service_instance(),
                department_selector_service=self._department_selector_service_instance(),
                professor_selector_service=self._professor_selector_service_instance(),
                logger=self.logger,
            )
        return self._course_service

    def _topic_service_instance(self):
        if self._topic_service is None:
            from artificial_u.services.topic_service import TopicService

            self._topic_service = TopicService(
                repository_factory=self.repository_factory,
                logger=self.logger,
            )
        return self._topic_service

    def _lecture_service_instance(self):
        if self._lecture_service is None:
            from artificial_u.services.lecture_service import LectureService

            self._lecture_service = LectureService(
                repository_factory=self.repository_factory,
                logger=self.logger,
            )
        return self._lecture_service

    def _lecture_generator_service_instance(self):
        if self._lecture_generator_service is None:
            from artificial_u.services.lecture_generator_service import LectureGeneratorService

            self._lecture_generator_service = LectureGeneratorService(
                lecture_service=self._lecture_service_instance(),
                content_service=self._content_service_instance(),
                course_service=self._course_service_instance(),
                professor_service=self._professor_service_instance(),
                repository_factory=self.repository_factory,
                topic_service=self._topic_service_instance(),
                job_enqueue_service=self._job_enqueue_service_instance(),
                storage_service=self._storage_service_instance(),
                logger=self.logger,
            )
        return self._lecture_generator_service

    def _department_service_instance(self):
        if self._department_service is None:
            from artificial_u.services.department_service import DepartmentService

            self._department_service = DepartmentService(
                repository_factory=self.repository_factory,
                professor_service=self._professor_service_instance(),
                course_service=self._course_service_instance(),
                logger=self.logger,
            )
        return self._department_service

    def _course_generator_service_instance(self):
        if self._course_generator_service is None:
            from artificial_u.services.course_generator_service import CourseGeneratorService

            self._course_generator_service = CourseGeneratorService(
                course_service=self._course_service_instance(),
                professor_service=self._professor_service_instance(),
                content_service=self._content_service_instance(),
                repository_factory=self.repository_factory,
                job_enqueue_service=self._job_enqueue_service_instance(),
                logger=self.logger,
            )
        return self._course_generator_service

    def _department_generator_service_instance(self):
        if self._department_generator_service is None:
            from artificial_u.services.department_generator_service import (
                DepartmentGeneratorService,
            )

            # Note: Avoid injecting DepartmentService here to prevent a dependency cycle:
            # CourseService -> DepartmentSelectorService -> DepartmentGeneratorService
            # -> DepartmentService -> CourseService. DepartmentGeneratorService does not
            # currently use department_service, so pass None.
            self._department_generator_service = DepartmentGeneratorService(
                department_service=None,  # break circular dependency
                content_service=self._content_service_instance(),
                repository_factory=self.repository_factory,
                job_enqueue_service=self._job_enqueue_service_instance(),
                logger=self.logger,
            )
        return self._department_generator_service

    def _department_selector_service_instance(self):
        if (
            not hasattr(self, "_department_selector_service")
            or self._department_selector_service is None
        ):
            from artificial_u.services.department_selector_service import DepartmentSelectorService

            self._department_selector_service = DepartmentSelectorService(
                content_service=self._content_service_instance(),
                repository_factory=self.repository_factory,
                department_generator_service=self._department_generator_service_instance(),
                logger=self.logger,
            )
        return self._department_selector_service

    def _professor_selector_service_instance(self):
        if (
            not hasattr(self, "_professor_selector_service")
            or self._professor_selector_service is None
        ):
            from artificial_u.services.professor_selector_service import ProfessorSelectorService

            self._professor_selector_service = ProfessorSelectorService(
                content_service=self._content_service_instance(),
                repository_factory=self.repository_factory,
                professor_generator_service=self._professor_generator_service_instance(),
                professor_service=self._professor_service_instance(),
                logger=self.logger,
            )
        return self._professor_selector_service

    def _topic_generator_service_instance(self):
        if self._topic_generator_service is None:
            from artificial_u.services.topic_generator_service import TopicGeneratorService

            self._topic_generator_service = TopicGeneratorService(
                topic_service=self._topic_service_instance(),
                course_service=self._course_service_instance(),
                content_service=self._content_service_instance(),
                repository_factory=self.repository_factory,
                job_enqueue_service=self._job_enqueue_service_instance(),
                logger=self.logger,
            )
        return self._topic_generator_service

    def _get_elevenlabs_client(self):
        """Get ElevenLabs client with API key if available."""
        from artificial_u.config import get_settings
        from artificial_u.integrations import elevenlabs

        settings = get_settings()
        if not settings.ELEVENLABS_API_KEY:
            self.logger.warning("ElevenLabs API key not found - voice services may be limited")
            return None

        try:
            return elevenlabs.ElevenLabsClient(api_key=settings.ELEVENLABS_API_KEY)
        except Exception as e:
            self.logger.error(f"Failed to create ElevenLabs client: {e}")
            return None
