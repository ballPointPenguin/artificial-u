"""
Department generation service for ArtificialU.

This service handles all AI-powered department generation workflows,
separated from the core CRUD operations in DepartmentService.
"""

import logging
from typing import Dict, Optional

from artificial_u.config import get_settings
from artificial_u.models.converters import (
    department_model_to_dict,
    enrich_department_dict_with_faculty,
    extract_xml_content,
    parse_department_xml,
)
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts import (
    get_department_prompt,
    get_system_prompt,
)
from artificial_u.services.content_service import ContentService
from artificial_u.utils import (
    ContentGenerationError,
)


class DepartmentGeneratorService:
    """Service for AI-powered department generation and related processing."""

    def __init__(
        self,
        department_service,
        content_service: ContentService,
        repository_factory: RepositoryFactory,
        job_enqueue_service,
        logger=None,
    ):
        """
        Initialize the department generator service.

        Args:
            department_service: Core department service for CRUD operations
            content_service: Content generation service
            repository_factory: Repository factory instance
            job_enqueue_service: Job enqueueing service for background tasks
            logger: Optional logger instance
        """
        self.department_service = department_service
        self.content_service = content_service
        self.repository_factory = repository_factory
        self.job_enqueue_service = job_enqueue_service
        self.logger = logger or logging.getLogger(__name__)

    async def generate_department(
        self,
        partial_attributes: Optional[Dict] = None,
        freeform_prompt: Optional[str] = None,
    ) -> dict:
        """
        Generate a department using AI based on provided partial attributes.

        Args:
            partial_attributes: Optional dictionary containing attributes to guide generation
            freeform_prompt: Optional freeform guidance text (can also be provided inside
                partial_attributes as key 'freeform_prompt')

        Returns:
            dict: The generated department attributes

        Raises:
            ContentGenerationError: If generation or parsing fails
            DatabaseError: If there's an error accessing the database
        """
        partial_attributes = partial_attributes or {}
        self.logger.info(
            f"Generating department with partial attributes: {list(partial_attributes.keys())}"
        )

        try:
            # Get existing departments for context
            # existing_courses_models = await self._get_existing_courses(department_model)
            # existing_courses_dicts = [course_model_to_dict(c) for c in existing_courses_models]
            existing_departments_models = self.repository_factory.department.list()

            # Extract department_id if present (for editing existing department)
            department_id = partial_attributes.get("department_id")

            # Filter out the current department being edited from existing departments
            if department_id:
                existing_departments_models = [
                    d for d in existing_departments_models if d.id != department_id
                ]
                self.logger.info(
                    f"Excluded department ID {department_id} from existing departments list"
                )

            existing_departments_dicts = [
                enrich_department_dict_with_faculty(
                    department_model_to_dict(d), self.repository_factory
                )
                for d in existing_departments_models
            ]

            # Extract freeform prompt if present either as explicit arg or within partials
            if freeform_prompt is None:
                freeform_prompt = partial_attributes.pop("freeform_prompt", None)
            else:
                # Ensure we don't pass it along inside partials if it was also present there
                partial_attributes.pop("freeform_prompt", None)

            # Get the prompt using the helper function
            prompt = get_department_prompt(
                existing_departments=existing_departments_dicts,
                partial_attributes=partial_attributes,
                freeform_prompt=freeform_prompt,
            )

            settings = get_settings()

            # Generate the department using content service
            self.logger.info("Calling content service to generate department...")
            response = await self.content_service.generate_text(
                prompt=prompt,
                model=settings.DEPARTMENT_GENERATION_MODEL,
                system_prompt=get_system_prompt("department"),
            )
            self.logger.info("Received response from content service.")

            if not response:
                raise ContentGenerationError("Content service returned empty response")

            # Extract XML content if wrapped in output tags
            xml_content = extract_xml_content(response, "output")
            if not xml_content:
                xml_content = response  # Use full response if no output tags

            # Parse the response using the converter function
            department_attrs = parse_department_xml(xml_content)
            self.logger.info(f"Successfully generated department: {department_attrs.get('name')}")
            return department_attrs

        except ContentGenerationError:
            # Re-raise content generation errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error during department generation: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ContentGenerationError(error_msg) from e
