"""
Professor generation service for ArtificialU.

This service handles all AI-powered generation and complex workflows related to professors,
including profile generation, image generation, and job enqueueing. CRUD operations are
handled by the core ProfessorService.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

from artificial_u.config import get_settings
from artificial_u.models.converters import extract_xml_content
from artificial_u.models.core import Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts import (
    get_professor_prompt,
    get_system_prompt,
)
from artificial_u.services.content_service import ContentService
from artificial_u.services.image_service import ImageService
from artificial_u.utils import (
    ContentGenerationError,
    DatabaseError,
    GenerationError,
)


class ProfessorGeneratorService:
    """Service for AI-powered professor generation and complex workflows."""

    def __init__(
        self,
        professor_service,  # Core ProfessorService for CRUD operations
        content_service: ContentService,
        image_service: ImageService,
        repository_factory: RepositoryFactory,
        job_enqueue_service,
        logger=None,
    ):
        """
        Initialize the professor generator service.

        Args:
            professor_service: Core professor service for CRUD operations
            content_service: Content generation service
            image_service: Image generation service
            repository_factory: Repository factory instance
            job_enqueue_service: Job enqueueing service for background tasks
            logger: Optional logger instance
        """
        self.professor_service = professor_service
        self.content_service = content_service
        self.image_service = image_service
        self.repository_factory = repository_factory
        self.job_enqueue_service = job_enqueue_service
        self.logger = logger or logging.getLogger(__name__)

    # --- Generation Methods --- #

    async def generate_professor(
        self,
        partial_attributes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates a professor profile using AI, potentially based on partial attributes.
        Handles fetching department name from ID if necessary.

        Args:
            partial_attributes: Optional dictionary of known attributes to guide generation
                                or fill in the blanks.

        Returns:
            A dictionary containing the complete generated professor attributes.

        Raises:
            GenerationError: If the AI generation or parsing fails.
            DatabaseError: If fetching related data (like department name) fails.
        """
        partial_attributes = partial_attributes or {}
        self.logger.info(
            f"Generating professor profile with partial attributes: "
            f"{list(partial_attributes.keys())}"
        )

        # --- 1. Resolve Department Name --- #
        try:
            resolved_dept_name = self._resolve_department_name(partial_attributes)
        except DatabaseError as e:
            raise e

        # --- 2. Prepare Prompt --- #
        prompt = self._prepare_professor_generation_prompt(
            department_name=resolved_dept_name,
            partial_attributes=partial_attributes,
        )

        # --- 3. Call AI and Parse --- #
        try:
            generated_attrs = await self._call_ai_and_parse(prompt)
        except GenerationError as e:
            # Propagate generation/parsing errors
            raise e

        # --- 4. Combine Attributes --- #
        # Start with generated, overlay with provided, prioritize resolved/input values
        settings = get_settings()
        final_attrs = {
            **generated_attrs,  # Base: Generated values
            **partial_attributes,  # Overlay: User-provided specifics
            # Ensure resolved/input values take final precedence if they exist
            "department_name": (
                resolved_dept_name if resolved_dept_name else generated_attrs.get("department_name")
            ),
            # Add attribution for AI-generated content
            "created_with": settings.PROFESSOR_GENERATION_MODEL,
        }

        self.logger.info(
            f"Successfully generated professor profile data for: {final_attrs.get('name')}"
        )
        return final_attrs

    async def generate_and_set_professor_image(
        self, professor_id: int, aspect_ratio: str = "1:1"
    ) -> Professor:
        """
        Generates an image for the professor and updates their record.

        Args:
            professor_id: The ID of the professor
            aspect_ratio: The desired aspect ratio for the image (e.g., "1:1", "16:9")

        Returns:
            The updated Professor object with the image URL.

        Raises:
            ProfessorNotFoundError: If the professor doesn't exist.
            GenerationError: If image generation fails.
            DatabaseError: If updating the professor record fails.
        """
        self.logger.info(f"Generating image for professor ID: {professor_id}")

        # Get the professor (will raise ProfessorNotFoundError if not found)
        professor = self.professor_service.get_professor(professor_id)

        try:
            # Generate the image using the image service
            result = await self.image_service.generate_professor_image(
                professor=professor, aspect_ratio=aspect_ratio
            )
        except Exception as e:
            self.logger.error(
                f"Image generation step failed for professor {professor_id}: {e}",
                exc_info=True,
            )
            raise GenerationError(f"Failed to generate image for professor {professor_id}") from e

        # Validate result and get image key
        image_key = self._validate_image_generation_result(result, professor_id)
        self.logger.info(f"Image generated for professor {professor_id}: {image_key}")

        # Get the full URL for the image
        image_url = self._get_image_url_from_key(image_key, professor_id)

        # Update the professor record with the new image URL and model used
        try:
            settings = get_settings()
            updated_professor = self.professor_service.update_professor(
                professor_id=professor_id,
                attributes={
                    "image_url": image_url,
                    "image_created_with": settings.IMAGE_GENERATION_MODEL,
                },
            )
            self.logger.info(
                f"Professor {professor_id} updated with new image URL "
                f"(model: {settings.IMAGE_GENERATION_MODEL})."
            )
            return updated_professor
        except Exception as e:
            # Re-raise errors from the update step
            self.logger.error(f"Failed to update professor {professor_id} with image URL: {e}")
            raise

    def enqueue_professor_image_generation(
        self, professor_id: int, aspect_ratio: str = "1:1"
    ) -> None:
        """
        Enqueue a background job to generate an image for the professor.

        Args:
            professor_id: The ID of the professor
            aspect_ratio: The desired aspect ratio for the image

        Raises:
            DatabaseError: If job enqueueing fails
        """
        # Delegate to the centralized job enqueueing service
        self.job_enqueue_service.enqueue_professor_image_generation(professor_id, aspect_ratio)

    # --- Helper Methods --- #

    async def _call_ai_and_parse(self, prompt: str) -> Dict[str, Any]:
        """
        Calls the AI content service with the given prompt and parses the XML response.

        Args:
            prompt: The prompt string for the AI.

        Returns:
            A dictionary of attributes parsed from the AI response.

        Raises:
            GenerationError: If AI call or XML parsing fails.
        """
        settings = get_settings()

        try:
            generated_content = await self.content_service.generate_text(
                prompt=prompt,
                model=settings.PROFESSOR_GENERATION_MODEL,
                system_prompt=get_system_prompt("professor"),
            )
        except Exception as e:
            self.logger.error(f"ContentService generation call failed: {e}", exc_info=True)
            raise GenerationError("AI content generation call failed.") from e

        if not generated_content:
            self.logger.error("AI generation returned empty content.")
            raise GenerationError("AI generation returned empty content.")

        try:
            parsed_attrs = self._parse_generated_professor_profile(generated_content)
            self.logger.debug("Successfully parsed AI response.")
            return parsed_attrs
        except Exception as e:
            # _parse_generated_professor_profile already logs details
            raise GenerationError("Failed to parse AI-generated professor profile.") from e

    def _resolve_department_name(self, partial_attributes: Dict[str, Any]) -> Optional[str]:
        """
        Resolves the department name from ID if name is not provided.

        Args:
            partial_attributes: Dictionary possibly containing department_id or department_name.

        Returns:
            The resolved or provided department name, or None.

        Raises:
            DatabaseError: If database lookup fails.
        """
        department_name = partial_attributes.get("department_name")
        department_id = partial_attributes.get("department_id")

        # If name is already provided, use it directly.
        if department_name:
            return department_name

        # If no ID is provided (and no name was), there's nothing to resolve.
        if department_id is None:
            self.logger.info("No department name or ID provided for resolution.")
            return None

        # ID provided without name, attempt lookup.
        self.logger.debug(f"Attempting to resolve department name for ID: {department_id}")
        try:
            department = self.repository_factory.department.get(department_id)
            if department:
                self.logger.debug(f"Resolved department name: {department.name}")
                return department.name
            else:
                # ID was provided, but not found in DB.
                self.logger.warning(
                    f"Department ID {department_id} not found in database during lookup."
                )
                return None
        except Exception as e:
            self.logger.error(
                f"Database error fetching department {department_id}: {e}",
                exc_info=True,
            )
            # Re-raise as a specific error type for the caller.
            raise DatabaseError(f"Failed to look up department name for ID {department_id}.") from e

    def _prepare_professor_generation_prompt(
        self,
        department_name: Optional[str],
        partial_attributes: dict,
    ) -> str:
        """Prepares the prompt string for professor generation."""
        # Fetch existing professors for context to avoid duplicates
        existing_profs_data = []
        try:
            all_professors = self.repository_factory.professor.list()
            existing_profs_data = [
                {"name": p.name, "specialization": p.specialization} for p in all_professors
            ]
            self.logger.debug(f"Found {len(existing_profs_data)} existing professors for context.")
        except Exception as e:
            self.logger.warning(f"Could not fetch existing professors for context: {e}")

        # Combine department_name and partial_attributes into a single dictionary
        combined_attrs = {**partial_attributes}
        if department_name is not None:
            combined_attrs["department_name"] = department_name

        # Extract freeform prompt if present
        freeform_prompt = combined_attrs.pop("freeform_prompt", None)

        self.logger.debug(f"Combined attributes: {combined_attrs}")
        if freeform_prompt:
            self.logger.debug(f"Freeform prompt: {freeform_prompt}")

        # Pass potentially None values to the prompt function
        return get_professor_prompt(
            existing_professors=existing_profs_data,
            partial_attributes=combined_attrs,
            freeform_prompt=freeform_prompt,
        )

    def _parse_generated_professor_profile(self, generated_content: str) -> Dict[str, Any]:
        """Parses the AI-generated XML content to extract professor attributes."""
        self.logger.debug(f"Attempting to parse generated content:\n{generated_content}")

        # Simplified XML extraction logic
        generated_xml_output = None

        # First try to extract from <output> tags
        generated_xml_output = extract_xml_content(generated_content, "output")
        if generated_xml_output:
            self.logger.info("Successfully extracted content from <output> tags")
        else:
            self.logger.info("<output> tag not found, trying direct <professor> extraction...")

            # Check if the response directly contains <professor>...</professor>
            if generated_content.strip().startswith(
                "<professor>"
            ) and generated_content.strip().endswith("</professor>"):
                # Use the raw response directly
                generated_xml_output = generated_content.strip()
                self.logger.info("Using raw response as it contains valid <professor> structure")
            else:
                # Try to extract inner content and wrap it
                inner_content = extract_xml_content(generated_content, "professor")
                if inner_content:
                    generated_xml_output = f"<professor>\n{inner_content}\n</professor>"
                    self.logger.info("Extracted <professor> inner content and wrapped it")

        if not generated_xml_output:
            error_msg = (
                "Could not extract <output> or <professor> tag from response:\n"
                f"{generated_content}"
            )
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg)

        # Ensure the extracted content has the proper <professor> wrapper
        if not generated_xml_output.strip().startswith("<professor>"):
            self.logger.warning("Wrapping extracted content in <professor> tags")
            generated_xml_output = f"<professor>\n{generated_xml_output}\n</professor>"

        try:
            # Parse the processed text which should now be a valid XML doc with one root
            return self._parse_professor_profile_xml(generated_xml_output)
        except ET.ParseError as e:
            self.logger.error(
                f"XML parsing failed: {e}\nProcessed Text:\n{generated_xml_output[:500]}..."
            )
            raise ValueError("Generated content contains invalid XML.") from e
        except Exception as e:
            self.logger.error(f"Error parsing professor profile XML: {e}")
            raise ValueError("Failed to extract attributes from professor XML.") from e

    def _parse_professor_profile_xml(self, profile_xml: str) -> Dict[str, Any]:
        """Parses the structured XML profile text."""
        root = ET.fromstring(profile_xml.strip())  # Use ET for robust parsing
        profile = {}
        expected_tags = [
            "name",
            "title",
            "specialization",
            "gender",
            "age",
            "accent",
            "description",
            "background",
            "personality",
            "teaching_style",
        ]

        for tag in expected_tags:
            element = root.find(tag)
            if element is not None and element.text:
                profile[tag] = element.text.strip()
            else:
                # Keep field as None if not found or empty in XML
                profile[tag] = None
                self.logger.debug(f"Tag '{tag}' not found or empty in generated XML.")

        # Convert age to integer if present and valid
        if profile.get("age"):
            try:
                profile["age"] = int(profile["age"])
            except (ValueError, TypeError):
                self.logger.warning(
                    f"Could not convert generated age '{profile.get('age')}' to integer. "
                    f"Setting age to None."
                )
                profile["age"] = None  # Set to None if conversion fails

        self.logger.debug(f"Parsed professor attributes from XML: {profile}")
        return profile

    def _validate_image_generation_result(self, result, professor_id: int) -> str:
        """Validate image generation result and return the image key."""
        if not result.success:
            # Provide more specific error information
            error_msg = f"Image generation failed for professor {professor_id}"
            if result.error:
                error_msg += f": {result.error.error_type.value} - {result.error}"
                if result.error.backend:
                    error_msg += f" (backend: {result.error.backend})"

            self.logger.error(error_msg)
            raise GenerationError(error_msg)

        if not result.image_keys:
            self.logger.error(
                f"Image generation succeeded but returned no keys for professor {professor_id}"
            )
            raise GenerationError(
                f"Image generation succeeded but yielded no result for professor {professor_id}"
            )

        return result.image_keys[0]  # Use the first generated image

    def _get_image_url_from_key(self, image_key: str, professor_id: int) -> str:
        """Get the full URL for an image key."""
        try:
            bucket = self.image_service.storage_service.images_bucket
            image_url = self.image_service.storage_service.get_file_url(
                bucket=bucket, object_name=image_key
            )
            self.logger.info(f"Image URL for professor {professor_id}: {image_url}")
            return image_url
        except Exception as e:
            self.logger.error(f"Failed to get image URL for key {image_key}: {e}", exc_info=True)
            raise GenerationError(
                f"Failed to construct image URL for professor {professor_id}"
            ) from e
