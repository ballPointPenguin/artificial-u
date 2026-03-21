"""
Topic generation service for ArtificialU.

This service handles all AI-powered topic generation workflows,
separated from the core CRUD operations in TopicService.
"""

import logging
from typing import Any, Dict, List, Optional

from artificial_u.config import get_settings
from artificial_u.models.converters import course_model_to_dict, parse_topic_xml, topics_to_xml
from artificial_u.models.core import Topic
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts import get_next_topic_prompt, get_system_prompt
from artificial_u.services.content_service import ContentService
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
            topic_slots = self._build_topic_slots(course_data)
            existing_topics = sorted(
                self.topic_service.list_topics_by_course(course_id),
                key=self._topic_sort_key,
            )
            existing_topics_by_slot = {
                (topic.week, topic.order): topic for topic in existing_topics
            }
            prior_topics_context = []
            created_topics = []

            self.logger.info(
                f"Preparing canonical topic generation for {len(topic_slots)} slots "
                f"({len(existing_topics)} already exist)"
            )

            for week, order in topic_slots:
                existing_topic = existing_topics_by_slot.get((week, order))
                if existing_topic:
                    prior_topics_context.append(self._topic_model_to_prompt_dict(existing_topic))
                    continue

                topic_dict = await self._generate_topic_for_slot(
                    course_data=course_data,
                    freeform_prompt=freeform_prompt,
                    prior_topics_context=prior_topics_context,
                    target_week=week,
                    target_order=order,
                )
                created_topic = self._save_topic_dict(topic_dict, course_id, created_by)
                created_topics.append(created_topic)
                prior_topics_context.append(self._topic_model_to_prompt_dict(created_topic))

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

        topic_dict = await self._generate_topic_for_slot(
            course_data=course_data,
            freeform_prompt=freeform_prompt,
            prior_topics_context=prior_topics_context,
            target_week=week,
            target_order=order,
        )

        return Topic(
            title=topic_dict["title"],
            course_id=course_id,
            week=topic_dict["week"],
            order=topic_dict["order"],
            content=topic_dict.get("content"),
            created_by=created_by,
            created_with=get_settings().TOPICS_GENERATION_MODEL,
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

    async def _generate_topic_for_slot(
        self,
        course_data: Dict[str, Any],
        freeform_prompt: Optional[str],
        prior_topics_context: List[Dict[str, Any]],
        target_week: int,
        target_order: int,
    ) -> Dict[str, Any]:
        """Generate a single topic for a specific canonical week/order slot."""
        prior_topics_xml = topics_to_xml(prior_topics_context) if prior_topics_context else None
        topic_prompt = get_next_topic_prompt(
            course_data=course_data,
            target_week=target_week,
            target_order=target_order,
            freeform_prompt=freeform_prompt,
            prior_topics_xml=prior_topics_xml,
        )
        system_prompt = get_system_prompt("topics")
        settings = get_settings()

        self.logger.info(
            f"Generating topic for course ID {course_data.get('id')} "
            f"(week={target_week}, order={target_order})"
        )
        raw_response = await self.content_service.generate_text(
            model=settings.TOPICS_GENERATION_MODEL,
            prompt=topic_prompt,
            system_prompt=system_prompt,
            max_tokens=2048,
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
        self, topic_dict: Dict[str, Any], course_id: int, created_by: Optional[int]
    ) -> Topic:
        title = topic_dict.get("title")
        week = topic_dict.get("week")
        order = topic_dict.get("order")

        if not title or week is None or order is None:
            raise ContentGenerationError(f"Generated topic data is incomplete: {topic_dict}")

        settings = get_settings()
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
            content=topic_dict.get("content"),
            created_by=created_by,
            created_with=settings.TOPICS_GENERATION_MODEL,
        )
        return self.repository_factory.topic.create(new_topic)
