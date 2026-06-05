"""
Professor selection service for smart course creation.

This service handles AI-powered professor selection when creating courses without
a specified professor_id. It can either select an existing professor or
delegate to ProfessorGeneratorService to create a new one.
"""

import logging
from typing import Any, Dict, Optional

from artificial_u.config import get_settings
from artificial_u.models.converters import (
    department_model_to_dict,
    professor_model_to_dict,
)
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts.selection import get_professor_selection_prompt, parse_selection_decision
from artificial_u.services.content_service import ContentService
from artificial_u.utils import (
    ContentGenerationError,
    DatabaseError,
)


class ProfessorSelectorService:
    """Service for selecting or generating professors based on course and department context."""

    def __init__(
        self,
        content_service: ContentService,
        repository_factory: RepositoryFactory,
        professor_generator_service,
        professor_service,  # For creating generated professors
        logger=None,
    ):
        """
        Initialize the professor selector service.

        Args:
            content_service: Content generation service for AI calls
            repository_factory: Repository factory instance
            professor_generator_service: Service to generate new professors
            professor_service: Core service for creating professors
            logger: Optional logger instance
        """
        self.content_service = content_service
        self.repository_factory = repository_factory
        self.professor_generator_service = professor_generator_service
        self.professor_service = professor_service
        self.logger = logger or logging.getLogger(__name__)

    async def resolve_professor(
        self,
        course_attributes: Dict[str, Any],
        department_id: int,
        created_by: Optional[int] = None,
        language: Optional[str] = None,
    ) -> int:
        """
        Resolve professor for a course by selecting existing or generating new.

        Args:
            course_attributes: Dictionary containing course details
            department_id: ID of the department for this course
            created_by: ID of student creator
            language: Optional language/locale of the professor

        Returns:
            int: Professor ID (either selected from existing or newly generated)

        Raises:
            DatabaseError: If there's an error accessing the database
            ContentGenerationError: If AI selection or generation fails
        """
        self.logger.info(
            f"Resolving professor for course: {course_attributes.get('title', 'Unknown')} "
            f"in department {department_id}"
        )

        try:
            # Get department info for context
            department = self.repository_factory.department.get(department_id)
            if not department:
                raise DatabaseError(f"Department {department_id} not found")

            # Get professors in this department
            department_professors = self.repository_factory.professor.list_by_department(
                department_id=department_id
            )
            department_professors_dicts = [
                professor_model_to_dict(p) for p in department_professors
            ]

            # Use AI to decide SELECT or GENERATE
            decision = await self._make_selection_decision(
                course_attributes, department, department_professors_dicts
            )

            if decision["action"] == "SELECT":
                if decision["entity_id"] is None:
                    raise ContentGenerationError("SELECT decision returned null entity_id")

                self.logger.info(
                    f"Selected existing professor {decision['entity_id']}: {decision['reasoning']}"
                )
                return decision["entity_id"]

            elif decision["action"] == "GENERATE":
                self.logger.info(f"Generating new professor: {decision['reasoning']}")

                freeform_prompt = decision["reasoning"] or course_attributes["description"]

                # Delegate to existing generator service
                professor_attrs = await self.professor_generator_service.generate_professor(
                    partial_attributes={
                        "freeform_prompt": freeform_prompt,
                        "department_id": department_id,
                    }
                )

                # Create the professor using the core service
                from artificial_u.models.core import Professor

                professor = Professor(
                    name=professor_attrs["name"],
                    title=professor_attrs["title"],
                    department_id=department_id,
                    specialization=professor_attrs["specialization"],
                    gender=professor_attrs["gender"],
                    age=professor_attrs["age"],
                    accent=professor_attrs["accent"],
                    description=professor_attrs["description"],
                    background=professor_attrs["background"],
                    personality=professor_attrs["personality"],
                    teaching_style=professor_attrs["teaching_style"],
                    created_by=created_by,
                    created_with=professor_attrs.get("created_with"),
                    language=language,
                )

                created_professor = self.professor_service.create_professor(professor)
                self.logger.info(f"Generated new professor with ID: {created_professor.id}")
                return created_professor.id

            else:
                raise ContentGenerationError(f"Unknown action in AI decision: {decision['action']}")

        except DatabaseError, ContentGenerationError:
            # Re-raise specific errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error during professor resolution: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    async def _make_selection_decision(
        self, course_attributes: Dict[str, Any], department, existing_professors: list
    ) -> Dict[str, Any]:
        """
        Use AI to decide whether to select existing professor or generate new one.

        Args:
            course_attributes: Course details for context
            department: Department model for context
            existing_professors: List of existing professor dictionaries in the department

        Returns:
            Dict containing action, entity_id, and reasoning

        Raises:
            ContentGenerationError: If AI call or parsing fails
        """
        try:
            # Generate selection prompt
            from artificial_u.models.converters import enrich_department_dict_with_faculty

            prompt = get_professor_selection_prompt(
                course_attributes=course_attributes,
                department_data=enrich_department_dict_with_faculty(
                    department_model_to_dict(department), self.repository_factory
                ),
                existing_professors=existing_professors,
            )

            settings = get_settings()

            # Call AI for decision
            self.logger.info("Calling AI for professor selection decision...")
            response = await self.content_service.generate_text(
                prompt=prompt,
                model=settings.PROFESSOR_GENERATION_MODEL,
                # Removing system_prompt as it may add extra text that interferes with parsing
            )
            self.logger.info("Received AI response for professor selection")

            if not response:
                raise ContentGenerationError("AI returned empty response for professor selection")

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
