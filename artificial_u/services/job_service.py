import logging
from typing import Any, Dict, Optional

from artificial_u.config import get_settings
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.lecture_images_generator_service import (
    DEFAULT_LECTURE_IMAGE_ASPECT_RATIO,
)


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
        self.settings = get_settings()
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
        self._course_export_service = None
        self._department_service = None
        self._department_generator_service = None
        self._topic_service = None
        self._topic_generator_service = None
        self._lecture_service = None
        self._lecture_generator_service = None
        self._lecture_images_generator_service = None

    # ---- Public API ----

    async def dispatch(
        self,
        kind: str,
        payload: Dict[str, Any],
        parent_job_id: Optional[int] = None,
    ) -> Dict[str, Any]:
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
            result = await handler(payload, parent_job_id=parent_job_id)
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

    def _build_lecture_slide_chain(
        self,
        slide_payloads: list[Dict[str, Any]],
        *,
        chain_parent_job_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Build a linked list of slide payloads so each slide can enqueue its successor
        only after its image URL has been written to the shared timeline.
        """
        next_payload: Optional[Dict[str, Any]] = None
        for slide_payload in reversed(slide_payloads):
            current = dict(slide_payload)
            if chain_parent_job_id is not None:
                current["chain_parent_job_id"] = chain_parent_job_id
            if next_payload is not None:
                current["next_slide_payload"] = next_payload
            next_payload = current

        return next_payload

    def _lecture_image_interval_sec_from_payload(self, payload: Dict[str, Any]) -> int:
        interval_sec = payload.get("interval_sec")
        if interval_sec is not None:
            return int(interval_sec)
        return self.settings.LECTURE_IMAGE_INTERVAL_SEC

    def _enqueue_next_lecture_slide(
        self, payload: Dict[str, Any], result: Dict[str, Any]
    ) -> Optional[int]:
        next_slide_payload = payload.get("next_slide_payload")
        if not next_slide_payload:
            return None
        if result.get("reason") == "stale_batch":
            return None
        if result.get("status") not in {"done", "failed", "skipped"}:
            return None

        chain_parent_job_id = payload.get("chain_parent_job_id")
        row = self.repository_factory.job.create(
            kind="generate_lecture_slide",
            payload=next_slide_payload,
            parent_job_id=chain_parent_job_id,
        )
        return row.id

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
            "generate_lecture_text_only": self._handle_generate_lecture_text_only,
            "generate_lecture_summary": self._handle_generate_lecture_summary,
            "generate_lecture_audio": self._handle_generate_lecture_audio,
            "generate_lecture_timeline": self._handle_generate_lecture_timeline,
            "remap_lecture_images_timeline": self._handle_remap_lecture_images_timeline,
            "generate_lecture_images": self._handle_generate_lecture_images,
            "resume_lecture_images": self._handle_resume_lecture_images,
            "generate_lecture_slide": self._handle_generate_lecture_slide,
            "generate_professor_image": self._handle_generate_professor_image,
            "generate_course_image": self._handle_generate_course_image,
            # Export tasks
            "export_course": self._handle_export_course,
            # Quickstart tasks
            "quickstart_start": self._handle_quickstart_start,
        }.get(kind)

    async def _handle_generate_course(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._course_generator_service_instance()
        partial = dict(payload.get("partial_attributes") or {})
        connected_course_ids = payload.get("connected_course_ids")
        if connected_course_ids is not None:
            partial["connected_course_ids"] = connected_course_ids
        result = await service.generate_course(partial)
        return {"generated_course": result}

    async def _handle_create_course(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a course using smart department/professor selection/generation.

        Expects payload with fields matching CourseService.create_course signature.
        Accepts either 'weeks' or 'total_weeks' for compatibility with API schema.
        """
        service = self._course_service_instance()

        # Payload normalization
        title = payload.get("title")
        code = payload.get("code")
        level = payload.get("level")
        weeks = payload.get("weeks", payload.get("total_weeks", 12))
        lectures_per_week = payload.get("lectures_per_week", 1)
        department_id = payload.get("department_id")
        professor_id = payload.get("professor_id")
        description = payload.get("description")
        created_by = payload.get("created_by")
        created_with = payload.get("created_with")
        connected_course_ids = payload.get("connected_course_ids")
        language = payload.get("language")

        if not title or not code or not level:
            raise ValueError("title, code, and level are required to create a course")

        course, professor = await service.create_course(
            title=title,
            code=code,
            level=level,
            weeks=weeks,
            lectures_per_week=lectures_per_week,
            department_id=department_id,
            professor_id=professor_id,
            description=description,
            created_by=created_by,
            created_with=created_with,
            connected_course_ids=connected_course_ids,
            parent_job_id=parent_job_id,
            language=language,
        )

        # After successful course creation, enqueue topic generation
        topics_job_id = None
        try:
            job_enqueue_service = self._job_enqueue_service_instance()
            topics_job_id = job_enqueue_service.enqueue_topics_generation(
                course.id, created_by=created_by, parent_job_id=parent_job_id
            )
            self.logger.info(f"Enqueued topic generation for course {course.id}")
        except Exception as e:
            self.logger.warning(f"Failed to enqueue topic generation for course {course.id}: {e}")

        result: Dict[str, Any] = {
            "course_id": course.id,
            "department_id": course.department_id,
            "professor_id": professor.id,
        }
        if topics_job_id is not None:
            result["topics_job_id"] = topics_job_id
        return result

    async def _handle_generate_department(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._department_generator_service_instance()
        partial = payload.get("partial_attributes") or {}
        freeform = payload.get("freeform_prompt")
        result = await service.generate_department(
            partial_attributes=partial,
            freeform_prompt=freeform,
        )
        return {"generated_department": result}

    async def _handle_generate_professor(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._professor_generator_service_instance()
        partial = dict(payload.get("partial_attributes") or {})
        freeform_prompt = payload.get("freeform_prompt")
        if freeform_prompt:
            partial["freeform_prompt"] = freeform_prompt

        result = await service.generate_professor(partial)
        return {"generated_professor": result}

    async def _handle_generate_topics_for_course(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._topic_generator_service_instance()
        course_id = payload.get("course_id")
        freeform = payload.get("freeform_prompt")
        created_by = payload.get("created_by")
        if course_id is None:
            raise ValueError("course_id is required")
        topics = await service.generate_topics_for_course(course_id, freeform, created_by)
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

    async def _handle_generate_lecture(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._lecture_generator_service_instance()
        partial = payload.get("partial_attributes") or {}
        self.logger.info(f"Generating and saving lecture with partial attributes: {partial}")

        # Batch mode: when the job payload includes a follow-up chain (created by the Topics
        # admin batch operations), we must ensure the lecture summary is fully generated before
        # enqueuing the next lecture in the chain. We achieve this by:
        # - generating/saving the lecture text only (no auto-enqueued summary/audio),
        # - enqueueing a `generate_lecture_summary` job that carries the follow_up chain,
        # - enqueueing audio in parallel (optional; doesn't affect narrative continuity).
        follow_up = payload.get("follow_up")
        if follow_up:
            saved_lecture = await service.generate_and_save_lecture_text_only(partial)

            # Enqueue summary job with follow-up chain so the worker advances only after summary.
            try:
                summary_payload: Dict[str, Any] = {
                    "lecture_id": saved_lecture.id,
                    "topic_id": saved_lecture.topic_id,
                    "follow_up": follow_up,
                }
                self.repository_factory.job.create(
                    kind="generate_lecture_summary",
                    payload=summary_payload,
                    parent_job_id=parent_job_id,
                )
            except Exception as e:  # noqa: BLE001
                self.logger.error(
                    "Failed to enqueue chained summary generation for lecture %s: %s",
                    saved_lecture.id,
                    e,
                    exc_info=True,
                )
                raise

            # Enqueue audio (does not participate in chaining).
            try:
                self.repository_factory.job.create(
                    kind="generate_lecture_audio",
                    payload={"lecture_id": saved_lecture.id, "topic_id": saved_lecture.topic_id},
                    parent_job_id=parent_job_id,
                )
            except Exception as e:  # noqa: BLE001
                self.logger.warning(
                    "Failed to enqueue audio generation for lecture %s: %s",
                    saved_lecture.id,
                    e,
                    exc_info=True,
                )
        else:
            # Use the complete workflow for non-batch jobs.
            saved_lecture = await service.generate_and_save_lecture(
                partial, parent_job_id=parent_job_id
            )

        self.logger.info(f"Generate and save lecture completed: {saved_lecture.id}")
        return {
            "lecture_id": saved_lecture.id,
            "course_id": saved_lecture.course_id,
            "topic_id": saved_lecture.topic_id,
            "title": saved_lecture.title,
            "transcript_url": saved_lecture.transcript_url,
        }

    async def _handle_generate_lecture_text_only(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._lecture_generator_service_instance()
        partial = payload.get("partial_attributes") or {}
        self.logger.info(
            f"Generating and saving lecture text only with partial attributes: {partial}"
        )

        # Use the method that generates and saves without enqueueing background jobs
        saved_lecture = await service.generate_and_save_lecture_text_only(partial)

        self.logger.info(f"Generate and save lecture text only completed: {saved_lecture.id}")
        return {
            "lecture_id": saved_lecture.id,
            "course_id": saved_lecture.course_id,
            "topic_id": saved_lecture.topic_id,
            "title": saved_lecture.title,
            "transcript_url": saved_lecture.transcript_url,
        }

    async def _handle_generate_lecture_summary(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._lecture_generator_service_instance()
        lecture_id = payload.get("lecture_id")
        if lecture_id is None:
            raise ValueError("lecture_id is required")
        result = await service.generate_lecture_summary(lecture_id)
        return result

    async def _handle_generate_lecture_audio(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._lecture_generator_service_instance()
        lecture_id = payload.get("lecture_id")
        if lecture_id is None:
            raise ValueError("lecture_id is required")
        result = await service.generate_lecture_audio(lecture_id, parent_job_id=parent_job_id)
        return result

    async def _handle_generate_lecture_timeline(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._lecture_generator_service_instance()
        lecture_id = payload.get("lecture_id")
        if lecture_id is None:
            raise ValueError("lecture_id is required")
        result = await service.generate_lecture_timeline(lecture_id)
        lecture = self.repository_factory.lecture.get(lecture_id)
        if payload.get("remap_images_timeline", True) and getattr(
            lecture, "images_timeline_url", None
        ):
            row = self.repository_factory.job.create(
                kind="remap_lecture_images_timeline",
                payload={
                    "lecture_id": lecture_id,
                    "topic_id": payload.get("topic_id") or getattr(lecture, "topic_id", None),
                },
                parent_job_id=parent_job_id,
            )
            result["remap_images_timeline_job_id"] = row.id
        return result

    async def _handle_remap_lecture_images_timeline(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._lecture_images_generator_service_instance()
        lecture_id = payload.get("lecture_id")
        if lecture_id is None:
            raise ValueError("lecture_id is required")
        result = await service.remap_lecture_images_timeline(
            lecture_id,
            interval_sec=self._lecture_image_interval_sec_from_payload(payload),
            aspect_ratio=payload.get("aspect_ratio", DEFAULT_LECTURE_IMAGE_ASPECT_RATIO),
            model_name_override=payload.get("model_name_override"),
        )
        return result

    async def _handle_generate_lecture_images(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._lecture_images_generator_service_instance()
        lecture_id = payload.get("lecture_id")
        if lecture_id is None:
            raise ValueError("lecture_id is required")
        interval_sec = self._lecture_image_interval_sec_from_payload(payload)
        aspect_ratio = payload.get("aspect_ratio", DEFAULT_LECTURE_IMAGE_ASPECT_RATIO)
        model_name_override = payload.get("model_name_override")
        cleanup_result = None
        if payload.get("delete_existing_images"):
            cleanup_result = await service.delete_existing_lecture_images(lecture_id)
        result = await service.plan_lecture_images(
            lecture_id,
            interval_sec=interval_sec,
            aspect_ratio=aspect_ratio,
            model_name_override=model_name_override,
        )
        if cleanup_result is not None:
            result["deleted_existing_images"] = cleanup_result.get("deleted", 0)
        slide_payloads = result.pop("slide_payloads", [])
        first_slide_payload = self._build_lecture_slide_chain(
            slide_payloads,
            chain_parent_job_id=parent_job_id,
        )
        job_ids = []
        if first_slide_payload:
            row = self.repository_factory.job.create(
                kind="generate_lecture_slide",
                payload=first_slide_payload,
                parent_job_id=parent_job_id,
            )
            job_ids.append(row.id)

        result["enqueued"] = len(job_ids)
        result["chain_remaining"] = max(0, len(slide_payloads) - len(job_ids))
        result["slide_job_ids"] = job_ids
        return result

    async def _handle_resume_lecture_images(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._lecture_images_generator_service_instance()
        lecture_id = payload.get("lecture_id")
        if lecture_id is None:
            raise ValueError("lecture_id is required")

        result = await service.resume_lecture_images(
            lecture_id,
            aspect_ratio=payload.get("aspect_ratio", DEFAULT_LECTURE_IMAGE_ASPECT_RATIO),
            model_name_override=payload.get("model_name_override"),
        )
        slide_payloads = result.pop("slide_payloads", [])
        first_slide_payload = self._build_lecture_slide_chain(
            slide_payloads,
            chain_parent_job_id=parent_job_id,
        )
        job_ids = []
        if first_slide_payload:
            row = self.repository_factory.job.create(
                kind="generate_lecture_slide",
                payload=first_slide_payload,
                parent_job_id=parent_job_id,
            )
            job_ids.append(row.id)

        result["enqueued"] = len(job_ids)
        result["chain_remaining"] = max(0, len(slide_payloads) - len(job_ids))
        result["slide_job_ids"] = job_ids
        return result

    async def _handle_generate_lecture_slide(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._lecture_images_generator_service_instance()
        lecture_id = payload.get("lecture_id")
        slot_idx = payload.get("slot_idx")
        object_key = payload.get("object_key")
        if lecture_id is None:
            raise ValueError("lecture_id is required")
        if slot_idx is None:
            raise ValueError("slot_idx is required")
        if not object_key:
            raise ValueError("object_key is required")

        result = await service.generate_lecture_slide(
            lecture_id,
            slot_idx=int(slot_idx),
            object_key=object_key,
            batch_id=payload.get("batch_id"),
            chunk_text=payload.get("chunk_text", ""),
            previous_chunk_text=payload.get("previous_chunk_text"),
            aspect_ratio=payload.get("aspect_ratio", DEFAULT_LECTURE_IMAGE_ASPECT_RATIO),
            model_name_override=payload.get("model_name_override"),
        )
        next_job_id = self._enqueue_next_lecture_slide(payload, result)
        if next_job_id is not None:
            result["next_slide_job_id"] = next_job_id
        return result

    async def _handle_generate_professor_image(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._professor_generator_service_instance()
        professor_id = payload.get("professor_id")
        aspect_ratio = payload.get("aspect_ratio", "1:1")
        if professor_id is None:
            raise ValueError("professor_id is required")
        updated = await service.generate_and_set_professor_image(
            professor_id=professor_id, aspect_ratio=aspect_ratio
        )
        return {"professor_id": updated.id, "image_url": getattr(updated, "image_url", None)}

    async def _handle_generate_course_image(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        service = self._course_generator_service_instance()
        course_id = payload.get("course_id")
        aspect_ratio = payload.get("aspect_ratio", "1:1")
        if course_id is None:
            raise ValueError("course_id is required")
        updated = await service.generate_and_set_course_image(
            course_id=course_id, aspect_ratio=aspect_ratio
        )
        return {"course_id": updated.id, "image_url": getattr(updated, "image_url", None)}

    async def _handle_export_course(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Export a course with all related data and assets."""
        service = self._course_export_service_instance()
        course_id = payload.get("course_id")
        if course_id is None:
            raise ValueError("course_id is required")
        result = await service.export_course(course_id)
        return result

    async def _handle_quickstart_start(
        self, payload: Dict[str, Any], parent_job_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Start the quickstart course creation flow.

        Generates course data from user query and creates the course with smart
        department/professor selection. This combines the AI generation step and
        course creation into a single job to avoid multiple long-running operations.

        Expects payload:
            query: str - The user's learning goal/description
            created_by: int - Student ID who initiated the request

        Returns dict with:
            course_id, professor_id, department_id, course_title, course_code, course_description
        """
        query = payload.get("query")
        created_by = payload.get("created_by")
        language = payload.get("language")

        if not query:
            raise ValueError("query is required for quickstart_start")

        self.logger.info(f"Starting quickstart course creation for query: {query[:100]}...")

        # Step 1: Generate course data from the user's query
        generator_service = self._course_generator_service_instance()
        generated_data = await generator_service.generate_course(
            partial_attributes={"freeform_prompt": query}
        )

        self.logger.info(f"Generated course data: {generated_data.get('title')}")

        # Step 2: Create the course with smart department/professor selection
        course_service = self._course_service_instance()
        course, professor = await course_service.create_course(
            title=generated_data.get("title") or "Quickstart Course",
            code=generated_data.get("code") or "QS001",
            level=generated_data.get("level") or "Undergraduate",
            weeks=12,
            lectures_per_week=1,
            department_id=None,
            professor_id=None,
            description=generated_data.get("description") or query,
            created_by=created_by,
            created_with=generated_data.get("created_with"),
            parent_job_id=parent_job_id,
            language=language,
        )

        # Step 3: Set course to hidden status (will be published after user approval)
        course.status = "hidden"
        self.repository_factory.course.update(course)

        self.logger.info(f"Created quickstart course {course.id} with professor {professor.id}")

        return {
            "course_id": course.id,
            "professor_id": professor.id,
            "department_id": course.department_id,
            "course_title": course.title,
            "course_code": course.code,
            "course_description": course.description or "",
        }

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
            from artificial_u.services.professor_generator_service import (
                ProfessorGeneratorService,
            )

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
                job_enqueue_service=self._job_enqueue_service_instance(),
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
            from artificial_u.services.lecture_generator_service import (
                LectureGeneratorService,
            )

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

    def _lecture_images_generator_service_instance(self):
        if self._lecture_images_generator_service is None:
            from artificial_u.services.lecture_images_generator_service import (
                LectureImagesGeneratorService,
            )

            self._lecture_images_generator_service = LectureImagesGeneratorService(
                lecture_service=self._lecture_service_instance(),
                course_service=self._course_service_instance(),
                topic_service=self._topic_service_instance(),
                professor_service=self._professor_service_instance(),
                storage_service=self._storage_service_instance(),
                image_service=self._image_service_instance(),
                logger=self.logger,
            )
        return self._lecture_images_generator_service

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
            from artificial_u.services.course_generator_service import (
                CourseGeneratorService,
            )

            self._course_generator_service = CourseGeneratorService(
                course_service=self._course_service_instance(),
                professor_service=self._professor_service_instance(),
                content_service=self._content_service_instance(),
                image_service=self._image_service_instance(),
                repository_factory=self.repository_factory,
                job_enqueue_service=self._job_enqueue_service_instance(),
                logger=self.logger,
            )
        return self._course_generator_service

    def _course_export_service_instance(self):
        if self._course_export_service is None:
            from artificial_u.services.course_export_service import (
                CourseExportService,
            )

            self._course_export_service = CourseExportService(
                repository_factory=self.repository_factory,
                storage_service=self._storage_service_instance(),
                logger=self.logger,
            )
        return self._course_export_service

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
            from artificial_u.services.department_selector_service import (
                DepartmentSelectorService,
            )

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
            from artificial_u.services.professor_selector_service import (
                ProfessorSelectorService,
            )

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
            from artificial_u.services.topic_generator_service import (
                TopicGeneratorService,
            )

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
