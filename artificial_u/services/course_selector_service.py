"""
Course selection service for quickstart wizard.

This service handles AI-powered course matching when a user describes what they want
to learn. It can either select existing published courses or signal that a new
course should be generated.
"""

import logging
from typing import Any, Dict, List

from artificial_u.config import get_settings
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts.course_selection import (
    get_course_selection_prompt,
    parse_course_selection_decision,
)
from artificial_u.services.content_service import ContentService
from artificial_u.utils import ContentGenerationError


class CourseSelectorService:
    """Service for matching user learning goals to existing courses or signaling generation."""

    def __init__(
        self,
        content_service: ContentService,
        repository_factory: RepositoryFactory,
        logger=None,
    ):
        """
        Initialize the course selector service.

        Args:
            content_service: Content generation service for AI calls
            repository_factory: Repository factory instance
            logger: Optional logger instance
        """
        self.content_service = content_service
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)

    async def match_courses(self, user_query: str) -> Dict[str, Any]:
        """
        Match user's learning goal against existing published courses.

        Uses an LLM to semantically match the user's query against available courses
        and decide whether to recommend existing courses or generate a new one.

        Args:
            user_query: The user's description of what they want to learn

        Returns:
            Dictionary containing:
            - action: "SELECT" or "GENERATE"
            - courses: List of matched Course objects (if SELECT)
            - course_ids: List of matched course IDs (if SELECT)
            - reasoning: Explanation of the decision

        Raises:
            ContentGenerationError: If AI matching fails
        """
        self.logger.info(f"Matching courses for query: {user_query[:100]}...")

        try:
            # Get all published courses with their details
            published_courses = self._get_published_courses_for_matching()

            if not published_courses:
                self.logger.info("No published courses available, signaling GENERATE")
                return {
                    "action": "GENERATE",
                    "courses": [],
                    "course_ids": [],
                    "reasoning": "No published courses are currently available.",
                }

            # Use AI to decide SELECT or GENERATE
            decision = await self._make_selection_decision(user_query, published_courses)

            if decision["action"] == "SELECT":
                # Fetch the full course objects for selected IDs
                courses = []
                for course_id in decision["course_ids"]:
                    course = self.repository_factory.course.get(course_id)
                    if course:
                        courses.append(course)
                    else:
                        self.logger.warning(f"Course ID {course_id} not found, skipping")

                if not courses:
                    # All selected courses were invalid, fall back to GENERATE
                    self.logger.warning(
                        "All selected course IDs were invalid, falling back to GENERATE"
                    )
                    return {
                        "action": "GENERATE",
                        "courses": [],
                        "course_ids": [],
                        "reasoning": decision["reasoning"]
                        + " (Note: Selected courses were not found)",
                    }

                self.logger.info(
                    f"Selected {len(courses)} existing courses: {[c.id for c in courses]}"
                )
                return {
                    "action": "SELECT",
                    "courses": courses,
                    "course_ids": [c.id for c in courses],
                    "reasoning": decision["reasoning"],
                }

            else:  # GENERATE
                self.logger.info(f"Signaling new course generation: {decision['reasoning']}")
                return {
                    "action": "GENERATE",
                    "courses": [],
                    "course_ids": [],
                    "reasoning": decision["reasoning"],
                }

        except ContentGenerationError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error during course matching: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ContentGenerationError(error_msg) from e

    def _get_published_courses_for_matching(self) -> List[Dict[str, Any]]:
        """
        Get all published courses with details needed for matching.

        Returns:
            List of course dictionaries with id, title, description, and professor_name
        """
        # Get all courses and filter for published status
        all_courses = self.repository_factory.course.list()
        courses = [c for c in all_courses if c.status == "published"]

        course_dicts = []
        for course in courses:
            course_dict = {
                "id": course.id,
                "title": course.title,
                "description": course.description or "",
            }

            # Try to get professor name for context
            if course.professor_id:
                professor = self.repository_factory.professor.get(course.professor_id)
                if professor:
                    course_dict["professor_name"] = professor.name

            course_dicts.append(course_dict)

        self.logger.info(f"Found {len(course_dicts)} published courses for matching")
        return course_dicts

    async def _make_selection_decision(
        self, user_query: str, existing_courses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use AI to decide whether to select existing courses or generate new one.

        Args:
            user_query: User's learning goal
            existing_courses: List of existing published course dictionaries

        Returns:
            Dict containing action, course_ids, and reasoning

        Raises:
            ContentGenerationError: If AI call or parsing fails
        """
        try:
            # Generate selection prompt
            prompt = get_course_selection_prompt(
                user_query=user_query,
                existing_courses=existing_courses,
            )

            settings = get_settings()

            # Call AI for decision (reuse course generation model as discussed)
            self.logger.info("Calling AI for course selection decision...")
            response = await self.content_service.generate_text(
                prompt=prompt,
                model=settings.COURSE_GENERATION_MODEL,
            )
            self.logger.info("Received AI response for course selection")

            if not response:
                raise ContentGenerationError("AI returned empty response for course selection")

            # Parse the decision
            decision = parse_course_selection_decision(response)

            return decision

        except ContentGenerationError:
            raise
        except Exception as e:
            error_msg = f"Failed to get AI selection decision: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ContentGenerationError(error_msg) from e
