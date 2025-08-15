"""
Department selection service for smart course creation.

This service handles AI-powered department selection when creating courses without
a specified department_id. It can either select an existing department or
delegate to DepartmentGeneratorService to create a new one.
"""

import logging
from typing import Any, Dict

from artificial_u.config import get_settings
from artificial_u.models.converters import department_model_to_dict
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts.selection import get_department_selection_prompt, parse_selection_decision
from artificial_u.services.content_service import ContentService
from artificial_u.utils import (
    ContentGenerationError,
    DatabaseError,
)


class DepartmentSelectorService:
    """Service for selecting or generating departments based on course context."""

    def __init__(
        self,
        content_service: ContentService,
        repository_factory: RepositoryFactory,
        department_generator_service,
        logger=None,
    ):
        """
        Initialize the department selector service.

        Args:
            content_service: Content generation service for AI calls
            repository_factory: Repository factory instance
            department_generator_service: Service to generate new departments
            logger: Optional logger instance
        """
        self.content_service = content_service
        self.repository_factory = repository_factory
        self.department_generator_service = department_generator_service
        self.logger = logger or logging.getLogger(__name__)

    async def resolve_department(self, course_attributes: Dict[str, Any]) -> int:
        """
        Resolve department for a course by selecting existing or generating new.

        Args:
            course_attributes: Dictionary containing course details

        Returns:
            int: Department ID (either selected from existing or newly generated)

        Raises:
            DatabaseError: If there's an error accessing the database
            ContentGenerationError: If AI selection or generation fails
        """
        self.logger.info(
            f"Resolving department for course: {course_attributes.get('title', 'Unknown')}"
        )

        try:
            # Get all existing departments
            existing_departments = self.repository_factory.department.list()
            existing_departments_dicts = [department_model_to_dict(d) for d in existing_departments]

            # Use AI to decide SELECT or GENERATE
            decision = await self._make_selection_decision(
                course_attributes, existing_departments_dicts
            )

            if decision["action"] == "SELECT":
                if decision["entity_id"] is None:
                    raise ContentGenerationError("SELECT decision returned null entity_id")

                self.logger.info(
                    f"Selected existing department {decision['entity_id']}: {decision['reasoning']}"
                )
                return decision["entity_id"]

            elif decision["action"] == "GENERATE":
                self.logger.info(f"Generating new department: {decision['reasoning']}")

                # Delegate to existing generator service
                department_attrs = await self.department_generator_service.generate_department(
                    partial_attributes=course_attributes
                )

                # Create the department using the core service
                from artificial_u.models.core import Department

                department = Department(
                    name=department_attrs["name"],
                    code=department_attrs["code"],
                    faculty=department_attrs["faculty"],
                    description=department_attrs["description"],
                )

                created_department = self.repository_factory.department.create(department)
                self.logger.info(f"Generated new department with ID: {created_department.id}")
                return created_department.id

            else:
                raise ContentGenerationError(f"Unknown action in AI decision: {decision['action']}")

        except (DatabaseError, ContentGenerationError):
            # Re-raise specific errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error during department resolution: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    async def _make_selection_decision(
        self, course_attributes: Dict[str, Any], existing_departments: list
    ) -> Dict[str, Any]:
        """
        Use AI to decide whether to select existing department or generate new one.

        Args:
            course_attributes: Course details for context
            existing_departments: List of existing department dictionaries

        Returns:
            Dict containing action, entity_id, and reasoning

        Raises:
            ContentGenerationError: If AI call or parsing fails
        """
        try:
            # Generate selection prompt
            prompt = get_department_selection_prompt(
                course_attributes=course_attributes,
                existing_departments=existing_departments,
            )

            settings = get_settings()

            # Call AI for decision
            self.logger.info("Calling AI for department selection decision...")
            response = await self.content_service.generate_text(
                prompt=prompt,
                model=settings.DEPARTMENT_GENERATION_MODEL,
                # Removing system_prompt as it may add extra text that interferes with parsing
            )
            self.logger.info("Received AI response for department selection")

            if not response:
                raise ContentGenerationError("AI returned empty response for department selection")

            # Parse the decision
            decision = parse_selection_decision(response)

            # Validate decision
            if decision["action"] not in ["SELECT", "GENERATE"]:
                raise ContentGenerationError(f"Invalid action in decision: {decision['action']}")

            if decision["action"] == "SELECT" and decision["entity_id"] is None:
                raise ContentGenerationError("SELECT action must include valid entity_id")

            return decision

        except ContentGenerationError:
            raise
        except Exception as e:
            error_msg = f"Failed to get AI selection decision: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ContentGenerationError(error_msg) from e
