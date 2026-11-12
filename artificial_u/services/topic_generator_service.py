"""
Topic generation service for ArtificialU.

This service handles all AI-powered topic generation workflows,
separated from the core CRUD operations in TopicService.
"""

import logging
from typing import Any, Dict, List, Optional

from artificial_u.models.converters import (
    course_model_to_dict,
    parse_topic_xml,
    parse_topics_xml,
    topics_to_xml,
)
from artificial_u.models.core import Topic
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.content_service import ContentService
from artificial_u.services.preference_service import PreferenceService
from artificial_u.utils import (
    ContentGenerationError,
    CourseNotFoundError,
    DatabaseError,
    detect_truncation,
    ensure_xml_wrapper,
    extract_xml_between_tags,
)


class TopicGeneratorService:
    """Service for AI-powered topic generation and related processing."""

    def __init__(
        self,
        topic_service,
        course_service,
        content_service: ContentService,
        repository_factory: RepositoryFactory,
        job_enqueue_service,
        logger=None,
    ):
        """
        Initialize the topic generator service.

        Args:
            topic_service: Core topic service for CRUD operations
            course_service: Course management service
            content_service: Content generation service
            repository_factory: Repository factory instance
            job_enqueue_service: Job enqueueing service for background tasks
            logger: Optional logger instance
        """
        self.topic_service = topic_service
        self.course_service = course_service
        self.content_service = content_service
        self.repository_factory = repository_factory
        self.job_enqueue_service = job_enqueue_service
        self.logger = logger or logging.getLogger(__name__)
        self.preference_service = PreferenceService(repository_factory, logger=self.logger)

    async def generate_topics_for_course(
        self,
        course_id: int,
        freeform_prompt: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> List[Topic]:
        """
        Generate a list of topics for a course using AI.

        Args:
            course_id: ID of the course for which to generate topics.
            freeform_prompt: Optional freeform text to guide topic generation.
            created_by: Optional student ID who triggered the generation.

        Returns:
            List[Topic]: A list of created Topic objects.

        Raises:
            CourseNotFoundError: If the course with the given ID is not found.
            ContentGenerationError: If content generation or parsing fails.
            DatabaseError: If there's an error saving topics to the database.
        """
        self.logger.info(
            f"Generating topics for course ID: {course_id}, freeform: {bool(freeform_prompt)}, "
            f"created_by: {created_by}"
        )

        try:
            course_model = self.course_service.get_course(course_id)
            course_data = course_model_to_dict(course_model)
            related_courses_topics_context = self._build_related_courses_topics_context(course_data)
            topic_slots = self._build_topic_slots(course_data)
            existing_topics = sorted(
                self.topic_service.list_topics_by_course(course_id),
                key=self._topic_sort_key,
            )
            existing_topics_by_slot = {
                (topic.week, topic.order): topic for topic in existing_topics
            }
            missing_slots = [slot for slot in topic_slots if slot not in existing_topics_by_slot]
            model = self.preference_service.get_topics_generation_model()

            self.logger.info(
                f"Preparing canonical topic generation for {len(topic_slots)} slots "
                f"({len(existing_topics)} already exist, {len(missing_slots)} missing)"
            )

            if not missing_slots:
                return []

            existing_topics_context = [
                self._topic_model_to_prompt_dict(topic) for topic in existing_topics
            ]
            generated_topics = await self._generate_topics_batch(
                course_data=course_data,
                freeform_prompt=freeform_prompt,
                existing_topics_context=existing_topics_context,
                related_courses_topics_context=related_courses_topics_context,
                missing_slots=missing_slots,
                existing_topics_by_slot=existing_topics_by_slot,
                model=model,
            )

            created_topics = []
            for topic_dict in generated_topics:
                created_topic = self._save_topic_dict(
                    topic_dict,
                    course_id,
                    created_by,
                    model=model,
                    language=course_model.language,
                )
                created_topics.append(created_topic)

            self.logger.info(
                f"Overall success: generated and saved {len(created_topics)} topics for course "
                f"{course_id}"
            )
            return created_topics

        except CourseNotFoundError as e:
            self.logger.error(f"Error generating topics - course not found: {e}")
            raise
        except ContentGenerationError as e:
            self.logger.error(f"Content generation or parsing error for topics: {e}")
            raise
        # ValueError from parsing is now handled inside _parse_convert_and_save_topics
        # and raised as ContentGenerationError, so it's caught by the above.
        except DatabaseError as e:
            self.logger.error(f"Database error during topic generation: {e}")
            raise
        except Exception as e:
            log_message = f"Unexpected error during topic generation for course {course_id}: {e}"
            self.logger.error(log_message, exc_info=True)
            raise ContentGenerationError(
                f"An unexpected error occurred during topic generation: {e}"
            ) from e

    async def generate_topic_for_course_slot(
        self,
        course_id: int,
        week: int,
        order: int,
        freeform_prompt: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> Topic:
        """Generate a single unsaved topic draft for a canonical course slot."""
        course_model = self.course_service.get_course(course_id)
        course_data = course_model_to_dict(course_model)
        related_courses_topics_context = self._build_related_courses_topics_context(course_data)
        self._validate_topic_slot(course_data, week, order)

        existing_topics = sorted(
            self.topic_service.list_topics_by_course(course_id),
            key=self._topic_sort_key,
        )
        prior_topics_context = [
            self._topic_model_to_prompt_dict(topic)
            for topic in existing_topics
            if self._topic_sort_key(topic) < (week, order, 0)
        ]

        model = self.preference_service.get_topics_generation_model()
        topic_dict = await self._generate_topic_for_slot(
            course_data=course_data,
            freeform_prompt=freeform_prompt,
            prior_topics_context=prior_topics_context,
            related_courses_topics_context=related_courses_topics_context,
            target_week=week,
            target_order=order,
            model=model,
        )

        return Topic(
            title=topic_dict["title"],
            course_id=course_id,
            week=topic_dict["week"],
            order=topic_dict["order"],
            language=course_model.language,
            content=topic_dict.get("content"),
            created_by=created_by,
            created_with=model,
        )

    def _build_topic_slots(self, course_data: Dict[str, Any]) -> List[tuple[int, int]]:
        lectures_per_week = max(1, int(course_data.get("lectures_per_week") or 1))
        total_weeks = max(1, int(course_data.get("total_weeks") or 1))
        return [
            (week, order)
            for week in range(1, total_weeks + 1)
            for order in range(1, lectures_per_week + 1)
        ]

    def _validate_topic_slot(self, course_data: Dict[str, Any], week: int, order: int) -> None:
        lectures_per_week = max(1, int(course_data.get("lectures_per_week") or 1))
        total_weeks = max(1, int(course_data.get("total_weeks") or 1))

        if week < 1 or week > total_weeks:
            raise ValueError(f"week must be between 1 and {total_weeks}")
        if order < 1 or order > lectures_per_week:
            raise ValueError(f"order must be between 1 and {lectures_per_week}")

    def _topic_sort_key(self, topic: Topic) -> tuple[int, int, int]:
        return (topic.week, topic.order, topic.id or 0)

    def _topic_model_to_prompt_dict(self, topic: Topic) -> Dict[str, Any]:
        return {
            "title": topic.title,
            "week": topic.week,
            "order": topic.order,
            "content": topic.content,
        }

    def _build_related_courses_topics_context(self, course_data: Dict[str, Any]) -> str:
        connected_course_ids = course_data.get("connected_course_ids") or []
        if not connected_course_ids:
            return ""

        related_sections: List[str] = []
        for connected_course_id in connected_course_ids:
            try:
                connected_course = self.course_service.get_course(connected_course_id)
            except Exception as e:
                self.logger.warning(
                    "Skipping related course %s for topic prompt context: %s",
                    connected_course_id,
                    e,
                )
                continue

            connected_topics = sorted(
                self.topic_service.list_topics_by_course(connected_course_id),
                key=self._topic_sort_key,
            )
            if not connected_topics:
                continue

            connected_topics_xml = topics_to_xml(
                [self._topic_model_to_prompt_dict(topic) for topic in connected_topics]
            )
            related_sections.append(
                "Related course topics (for continuity and to avoid repetition):\n"
                f"Related course: {connected_course.title}\n"
                f"{connected_topics_xml}"
            )

        if not related_sections:
            return ""

        return "\n\n".join(related_sections) + "\n"

    def save_topics_for_course(
        self,
        course_id: int,
        topics_data: List[Dict[str, Any]],
        created_by: Optional[int] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[Topic]:
        """Persist a list of pre-generated topic dicts (e.g. from an approved course draft)."""
        resolved_model = model or self.preference_service.get_course_generation_model()
        saved_topics: List[Topic] = []
        for idx, raw_topic in enumerate(topics_data):
            if not isinstance(raw_topic, dict) or not raw_topic.get("title"):
                continue
            topic_dict = {
                "title": str(raw_topic["title"]).strip(),
                "week": int(raw_topic.get("week") or (idx + 1)),
                "order": int(raw_topic.get("order") or 1),
                "content": raw_topic.get("content"),
            }
            saved_topics.append(
                self._save_topic_dict(
                    topic_dict=topic_dict,
                    course_id=course_id,
                    created_by=created_by,
                    model=resolved_model,
                    language=language,
                )
            )
        return saved_topics

    async def _generate_topics_batch(
        self,
        course_data: Dict[str, Any],
        freeform_prompt: Optional[str],
        existing_topics_context: List[Dict[str, Any]],
        related_courses_topics_context: str,
        missing_slots: List[tuple[int, int]],
        existing_topics_by_slot: Dict[tuple[int, int], Topic],
        model: str,
    ) -> List[Dict[str, Any]]:
        """Generate all missing topics for a course in a single LLM call."""
        existing_topics_xml = (
            topics_to_xml(existing_topics_context) if existing_topics_context else None
        )

        language = course_data.get("language") or "en"
        lang = "en"
        if language and isinstance(language, str):
            lang_prefix = language.lower()[:2]
            if lang_prefix in ("en", "fr"):
                lang = lang_prefix

        from artificial_u.prompts import get_prompts_for_language

        prompt_module = get_prompts_for_language(lang)
        topics_prompt = prompt_module.get_topics_prompt(
            course_data=course_data,
            freeform_prompt=freeform_prompt,
            existing_topics_xml=existing_topics_xml,
            related_courses_topics_context=related_courses_topics_context,
        )
        system_prompt = prompt_module.get_system_prompt("topics")
        self.logger.info(
            f"Generating {len(missing_slots)} topics in a single batch for course ID "
            f"{course_data.get('id')}"
        )
        raw_response = await self.content_service.generate_text(
            model=model,
            prompt=topics_prompt,
            system_prompt=system_prompt,
            max_tokens=16384,
            thinking_level="low",
        )
        generated_topics_xml = self._extract_generated_topics_xml(raw_response)

        try:
            parsed_topics = parse_topics_xml(generated_topics_xml)
        except ValueError as e:
            self.logger.error(f"XML parsing error for batch topics: {e}")
            raise ContentGenerationError(f"Error parsing generated topics XML: {e}") from e

        valid_topics = [t for t in parsed_topics if isinstance(t, dict) and t.get("title")]
        if not valid_topics:
            raise ContentGenerationError("Generated topics XML did not include any valid topics")

        return self._match_topics_to_missing_slots(
            valid_topics=valid_topics,
            missing_slots=missing_slots,
            existing_topics_by_slot=existing_topics_by_slot,
        )

    def _match_topics_to_missing_slots(
        self,
        valid_topics: List[Dict[str, Any]],
        missing_slots: List[tuple[int, int]],
        existing_topics_by_slot: Dict[tuple[int, int], Topic],
    ) -> List[Dict[str, Any]]:
        missing_slot_set = set(missing_slots)
        assigned_by_slot: Dict[tuple[int, int], Dict[str, Any]] = {}
        unassigned_topics: List[Dict[str, Any]] = []
        existing_titles = {
            t.title.strip().lower() for t in existing_topics_by_slot.values() if t.title
        }

        for topic in valid_topics:
            slot = (topic.get("week"), topic.get("order"))
            if slot in missing_slot_set and slot not in assigned_by_slot:
                topic["week"], topic["order"] = slot
                assigned_by_slot[slot] = topic
            elif slot in existing_topics_by_slot and (
                topic.get("title", "").strip().lower() in existing_titles
            ):
                # Model echoed back an existing topic unchanged; skip it
                continue
            else:
                unassigned_topics.append(topic)

        unassigned_iter = iter(unassigned_topics)
        final_topics: List[Dict[str, Any]] = []
        for week, order in missing_slots:
            if (week, order) in assigned_by_slot:
                final_topics.append(assigned_by_slot[(week, order)])
                continue
            fallback = next(unassigned_iter, None)
            if fallback is None:
                break
            if fallback.get("week") != week or fallback.get("order") != order:
                self.logger.warning(
                    "Generated topic returned mismatched positioning; normalizing to "
                    f"requested slot (expected week={week}, order={order}, "
                    f"received week={fallback.get('week')}, order={fallback.get('order')})"
                )
            fallback["week"] = week
            fallback["order"] = order
            final_topics.append(fallback)

        return final_topics

    def _extract_generated_topics_xml(self, raw_response: str) -> str:
        is_truncated = detect_truncation(raw_response)
        generated_output = extract_xml_between_tags(raw_response, "output")

        if generated_output:
            stripped_output = generated_output.strip()
            if stripped_output.startswith("<topics>") and stripped_output.endswith("</topics>"):
                return stripped_output
            inner_topics = extract_xml_between_tags(stripped_output, "topics")
            if inner_topics:
                return ensure_xml_wrapper(inner_topics, "topics")
            if "<topic>" in stripped_output:
                return ensure_xml_wrapper(stripped_output, "topics")

        stripped_response = raw_response.strip()
        if stripped_response.startswith("<topics>") and stripped_response.endswith("</topics>"):
            return stripped_response

        inner_topics = extract_xml_between_tags(raw_response, "topics")
        if inner_topics:
            return f"<topics>\n{inner_topics}\n</topics>"

        inner_topic = extract_xml_between_tags(raw_response, "topic")
        if inner_topic:
            return f"<topics>\n<topic>\n{inner_topic}\n</topic>\n</topics>"

        error_msg = (
            f"Could not extract <output> or <topics> tag from response"
            f"{' (response was truncated)' if is_truncated else ''}:\n"
            f"{raw_response[:500]}..."
        )
        self.logger.error(error_msg)
        raise ContentGenerationError(error_msg)

    async def _generate_topic_for_slot(
        self,
        course_data: Dict[str, Any],
        freeform_prompt: Optional[str],
        prior_topics_context: List[Dict[str, Any]],
        related_courses_topics_context: str,
        target_week: int,
        target_order: int,
        model: str,
    ) -> Dict[str, Any]:
        """Generate a single topic for a specific canonical week/order slot."""
        prior_topics_xml = topics_to_xml(prior_topics_context) if prior_topics_context else None

        # Determine language for prompts
        language = course_data.get("language") or "en"
        lang = "en"
        if language and isinstance(language, str):
            lang_prefix = language.lower()[:2]
            if lang_prefix in ("en", "fr"):
                lang = lang_prefix

        from artificial_u.prompts import get_prompts_for_language

        prompt_module = get_prompts_for_language(lang)
        topic_prompt = prompt_module.get_next_topic_prompt(
            course_data=course_data,
            target_week=target_week,
            target_order=target_order,
            freeform_prompt=freeform_prompt,
            prior_topics_xml=prior_topics_xml,
            related_courses_topics_context=related_courses_topics_context,
        )
        system_prompt = prompt_module.get_system_prompt("topics")
        self.logger.info(
            f"Generating topic for course ID {course_data.get('id')} "
            f"(week={target_week}, order={target_order})"
        )
        raw_response = await self.content_service.generate_text(
            model=model,
            prompt=topic_prompt,
            system_prompt=system_prompt,
            # Gemini 3.x reasoning models spend "thinking" tokens out of this same
            # budget, so a tight cap (e.g. 2048) gets exhausted before the XML
            # finishes, truncating the response. Give generous headroom and keep
            # the reasoning effort modest for this structured-output task.
            max_tokens=8192,
            thinking_level="low",
        )
        generated_topic_xml = self._extract_generated_topic_xml(raw_response)

        try:
            topic_dict = parse_topic_xml(generated_topic_xml)
        except ValueError as e:
            self.logger.error(f"XML parsing error for topic slot {target_week}/{target_order}: {e}")
            raise ContentGenerationError(f"Error parsing generated topic XML: {e}") from e

        if not topic_dict.get("title"):
            raise ContentGenerationError("Generated topic XML did not include a title")

        if topic_dict.get("week") != target_week or topic_dict.get("order") != target_order:
            self.logger.warning(
                "Generated topic returned mismatched positioning; normalizing to requested slot "
                f"(expected week={target_week}, order={target_order}, "
                f"received week={topic_dict.get('week')}, order={topic_dict.get('order')})"
            )

        topic_dict["week"] = target_week
        topic_dict["order"] = target_order
        return topic_dict

    def _extract_generated_topic_xml(self, raw_response: str) -> str:
        is_truncated = detect_truncation(raw_response)
        generated_topic_output = extract_xml_between_tags(raw_response, "output")

        if not generated_topic_output:
            stripped_response = raw_response.strip()
            if stripped_response.startswith("<topic>") and stripped_response.endswith("</topic>"):
                generated_topic_output = stripped_response
            else:
                inner_content = extract_xml_between_tags(raw_response, "topic")
                if inner_content:
                    generated_topic_output = f"<topic>\n{inner_content}\n</topic>"

        if not generated_topic_output:
            error_msg = (
                f"Could not extract <output> or <topic> tag from response"
                f"{' (response was truncated)' if is_truncated else ''}:\n"
                f"{raw_response[:500]}..."
            )
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg)

        return ensure_xml_wrapper(generated_topic_output, "topic")

    def _save_topic_dict(
        self,
        topic_dict: Dict[str, Any],
        course_id: int,
        created_by: Optional[int],
        model: str,
        language: Optional[str] = None,
    ) -> Topic:
        title = topic_dict.get("title")
        week = topic_dict.get("week")
        order = topic_dict.get("order")

        if not title or week is None or order is None:
            raise ContentGenerationError(f"Generated topic data is incomplete: {topic_dict}")

        existing_topic = self.repository_factory.topic.get_by_course_week_order(
            course_id=course_id,
            week=week,
            order=order,
        )
        if existing_topic:
            self.logger.info(
                f"Replacing existing topic '{existing_topic.title}' "
                f"(course={course_id}, week={week}, order={order}) with '{title}'"
            )
            self.repository_factory.topic.delete(existing_topic.id)

        new_topic = Topic(
            title=title,
            course_id=course_id,
            week=week,
            order=order,
            language=language,
            content=topic_dict.get("content"),
            created_by=created_by,
            created_with=model,
        )
        return self.repository_factory.topic.create(new_topic)
