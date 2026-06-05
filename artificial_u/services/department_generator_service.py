"""
Department generation service for ArtificialU.

This service handles all AI-powered department generation workflows,
separated from the core CRUD operations in DepartmentService.
"""

import logging
from typing import Dict, List, Optional

from artificial_u.config import get_settings
from artificial_u.models.converters import (
    department_model_to_dict,
    enrich_department_dict_with_faculty,
    extract_xml_content,
    parse_department_xml,
)
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts import (
    get_prompts_for_language,
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
        language: Optional[str] = None,
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
        language = language or "en"
        self.logger.info(
            f"Generating department with partial attributes: {list(partial_attributes.keys())}, "
            f"language: {language}"
        )

        try:
            # Prepare existing data for context (filtered by language)
            existing_departments_dicts = self._prepare_existing_departments_data(
                partial_attributes, language
            )
            existing_faculties_dicts = self._prepare_existing_faculties_data(language)

            # Normalize freeform prompt and enrich partial attributes
            freeform_prompt = self._normalize_freeform_prompt(partial_attributes, freeform_prompt)
            self._enrich_partial_attributes_with_faculty_name(partial_attributes)

            # Generate and parse content
            department_attrs = await self._generate_and_parse_content(
                existing_departments_dicts,
                existing_faculties_dicts,
                partial_attributes,
                freeform_prompt,
                language,
            )

            # Convert faculty name to faculty_id
            self._convert_faculty_name_to_id(
                department_attrs, existing_faculties_dicts, partial_attributes
            )

            self.logger.info(f"Successfully generated department: {department_attrs.get('name')}")
            return department_attrs

        except ContentGenerationError:
            # Re-raise content generation errors
            raise
        except Exception as e:
            error_msg = f"Unexpected error during department generation: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise ContentGenerationError(error_msg) from e

    # --- Helper Methods for Generation --- #

    def _prepare_existing_departments_data(
        self, partial_attributes: Dict, language: str = "en"
    ) -> List[Dict]:
        """Prepare existing departments data for prompt context.

        Fetches departments filtered by language, filters out the current one if editing,
        and enriches them with faculty information.

        Args:
            partial_attributes: Dictionary that may contain department_id
            language: Language code to filter context data

        Returns:
            List of enriched department dictionaries
        """
        existing_departments_models = self.repository_factory.department.list(language=language)

        # Filter out the current department being edited from existing departments
        department_id = partial_attributes.get("department_id")
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

        return existing_departments_dicts

    def _prepare_existing_faculties_data(self, language: str = "en") -> List[Dict]:
        """Prepare existing faculties data for prompt context.

        Args:
            language: Language code to filter context data

        Returns:
            List of faculty dictionaries with id, name, and description
        """
        existing_faculties_models = self.repository_factory.faculty.list(language=language)
        existing_faculties_dicts = [
            {"id": f.id, "name": f.name, "description": f.description}
            for f in existing_faculties_models
        ]
        self.logger.info(f"Fetched {len(existing_faculties_dicts)} existing faculties")
        return existing_faculties_dicts

    def _normalize_freeform_prompt(
        self, partial_attributes: Dict, freeform_prompt: Optional[str]
    ) -> Optional[str]:
        """Extract and normalize freeform prompt from arguments or partial attributes.

        Args:
            partial_attributes: Dictionary that may contain 'freeform_prompt'
            freeform_prompt: Optional explicit freeform prompt argument

        Returns:
            The normalized freeform prompt, or None
        """
        if freeform_prompt is None:
            freeform_prompt = partial_attributes.pop("freeform_prompt", None)
        else:
            # Ensure we don't pass it along inside partials if it was also present there
            partial_attributes.pop("freeform_prompt", None)
        return freeform_prompt

    def _enrich_partial_attributes_with_faculty_name(self, partial_attributes: Dict) -> None:
        """Enrich partial_attributes with faculty_name if faculty_id is present.

        This helps the prompt generation by providing the faculty name
        when only the ID is known.

        Args:
            partial_attributes: Dictionary to enrich (modified in place)
        """
        if "faculty_id" in partial_attributes and partial_attributes["faculty_id"]:
            faculty = self.repository_factory.faculty.get(partial_attributes["faculty_id"])
            if faculty:
                partial_attributes["faculty_name"] = faculty.name
                self.logger.info(
                    f"Enriched partial_attributes with faculty_name '{faculty.name}' "
                    f"from faculty_id {partial_attributes['faculty_id']}"
                )

    async def _generate_and_parse_content(
        self,
        existing_departments_dicts: List[Dict],
        existing_faculties_dicts: List[Dict],
        partial_attributes: Dict,
        freeform_prompt: Optional[str],
        language: str = "en",
    ) -> Dict:
        """Generate department content and parse the XML response.

        Args:
            existing_departments_dicts: List of existing department dictionaries
            existing_faculties_dicts: List of existing faculty dictionaries
            partial_attributes: Dictionary of partial attributes for generation
            freeform_prompt: Optional freeform guidance text
            language: Language code for prompt selection

        Returns:
            Dictionary of parsed department attributes

        Raises:
            ContentGenerationError: If generation or parsing fails
        """
        # Get the prompt using the language-appropriate module
        prompts_module = get_prompts_for_language(language)
        prompt = prompts_module.get_department_prompt(
            existing_departments=existing_departments_dicts,
            existing_faculties=existing_faculties_dicts,
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
        return department_attrs

    def _convert_faculty_name_to_id(
        self,
        department_attrs: Dict,
        existing_faculties_dicts: List[Dict],
        partial_attributes: Dict,
    ) -> None:
        """Convert faculty name to faculty_id in department attributes.

        The LLM returns a faculty name string, we need to convert it to faculty_id.
        Modifies department_attrs in place.

        Args:
            department_attrs: Dictionary of department attributes (modified in place)
            existing_faculties_dicts: List of existing faculty dictionaries for error messages
            partial_attributes: Original partial attributes for fallback checking

        Raises:
            ContentGenerationError: If faculty name is provided but not found
        """
        faculty_name = department_attrs.get("faculty")
        if faculty_name:
            # Look up the faculty by name
            faculty = self.repository_factory.faculty.get_by_name(faculty_name)
            if faculty:
                # Replace faculty name with faculty_id
                department_attrs["faculty_id"] = faculty.id
                self.logger.info(f"Converted faculty '{faculty_name}' to faculty_id {faculty.id}")
            else:
                # Faculty not found - this should not happen if LLM followed instructions
                error_msg = (
                    f"Faculty '{faculty_name}' not found in existing faculties. "
                    f"Available faculties: {[f['name'] for f in existing_faculties_dicts]}"
                )
                self.logger.error(error_msg)
                raise ContentGenerationError(error_msg)
        else:
            # No faculty provided - check if faculty_id was in partial_attributes
            if "faculty_id" not in partial_attributes:
                self.logger.warning("No faculty specified in generation, faculty_id will be None")
