"""
Tag generation service for ArtificialU.

Generates subject tags for a course with an LLM and stores them in the
course's content-language universe (English courses get English tags,
French courses get French tags — never translations).
"""

import logging
from typing import List, Optional

from artificial_u.config import get_settings
from artificial_u.models.converters import course_model_to_dict, parse_tags_xml
from artificial_u.models.core import Tag
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.content_service import ContentService
from artificial_u.utils import (
    ContentGenerationError,
    CourseNotFoundError,
    detect_truncation,
    ensure_xml_wrapper,
    extract_xml_between_tags,
)

# Existing vocabulary passed to the prompt, most-used first
VOCABULARY_LIMIT = 100


class TagGeneratorService:
    """Service for AI-powered course tag generation."""

    def __init__(
        self,
        course_service,
        content_service: ContentService,
        repository_factory: RepositoryFactory,
        logger=None,
    ):
        """
        Initialize the tag generator service.

        Args:
            course_service: Core course service for lookups
            content_service: Content generation service
            repository_factory: Repository factory instance
            logger: Optional logger instance
        """
        self.course_service = course_service
        self.content_service = content_service
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)

    async def generate_tags_for_course(self, course_id: int) -> List[Tag]:
        """
        Generate tags for a course using AI and replace its tag set.

        Args:
            course_id: ID of the course to tag

        Returns:
            List[Tag]: The course's new tags

        Raises:
            CourseNotFoundError: If the course does not exist
            ContentGenerationError: If generation or parsing fails
        """
        course_model = self.course_service.get_course(course_id)
        if not course_model:
            raise CourseNotFoundError(f"Course with ID {course_id} not found")

        language = self._resolve_language(course_model.language)
        course_data = course_model_to_dict(course_model)

        department_name = None
        if course_model.department_id:
            department = self.repository_factory.department.get(course_model.department_id)
            if department:
                department_name = department.name

        topic_titles = [
            topic.title
            for topic in sorted(
                self.repository_factory.topic.list_by_course(course_id),
                key=lambda t: (t.week, t.order),
            )
        ]
        existing_tags = self.repository_factory.tag.list_top_names(
            language=language, limit=VOCABULARY_LIMIT
        )

        from artificial_u.prompts import get_prompts_for_language

        prompt_module = get_prompts_for_language(language)
        prompt = prompt_module.get_course_tags_prompt(
            course_data,
            department_name=department_name,
            topic_titles=topic_titles,
            existing_tags=existing_tags,
        )
        system_prompt = prompt_module.get_system_prompt("tags")
        settings = get_settings()

        self.logger.info(
            "Generating tags for course %d (language=%s, vocabulary=%d, topics=%d)",
            course_id,
            language,
            len(existing_tags),
            len(topic_titles),
        )
        raw_response = await self.content_service.generate_text(
            model=settings.TAGS_GENERATION_MODEL,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1024,
        )

        tag_names = self._parse_tag_names(raw_response)
        if department_name:
            # Mechanically include the department as a tag (e.g. "Biology", "French")
            # rather than relying on the LLM, which is instructed to avoid restating it.
            tag_names = [department_name, *tag_names]
        tags = self.repository_factory.tag.get_or_create_by_names(tag_names, language=language)
        if not tags:
            raise ContentGenerationError(
                f"Generated tag names for course {course_id} normalized to nothing: {tag_names}"
            )
        saved = self.repository_factory.tag.set_course_tags(course_id, [t.id for t in tags])

        self.logger.info(
            "Tagged course %d with %d tags: %s",
            course_id,
            len(saved),
            ", ".join(t.name for t in saved),
        )
        return saved

    def _resolve_language(self, language: Optional[str]) -> str:
        """Map a course language to a supported tag/prompt universe."""
        if language and isinstance(language, str):
            prefix = language.lower()[:2]
            if prefix in ("en", "fr"):
                return prefix
        return "en"

    def _parse_tag_names(self, raw_response: str) -> List[str]:
        """Extract the <tags> block from the LLM response and parse names."""
        is_truncated = detect_truncation(raw_response)
        tags_output = extract_xml_between_tags(raw_response, "output")

        if not tags_output:
            inner_content = extract_xml_between_tags(raw_response, "tags")
            if inner_content is not None:
                tags_output = f"<tags>\n{inner_content}\n</tags>"

        if not tags_output:
            error_msg = (
                f"Could not extract <output> or <tags> tag from response"
                f"{' (response was truncated)' if is_truncated else ''}:\n"
                f"{raw_response[:500]}..."
            )
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg)

        try:
            return parse_tags_xml(ensure_xml_wrapper(tags_output, "tags"))
        except ValueError as e:
            self.logger.error("XML parsing error for course tags: %s", e)
            raise ContentGenerationError(f"Error parsing generated tags XML: {e}") from e
