"""
Professor management service for ArtificialU.
"""

import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from artificial_u.config import get_settings
from artificial_u.models.core import Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.prompts.base import extract_xml_content
from artificial_u.prompts.professors import get_professor_prompt
from artificial_u.prompts.system import SYSTEM_PROMPTS
from artificial_u.services.content_service import ContentService
from artificial_u.services.image_service import ImageService
from artificial_u.services.voice_service import VoiceService
from artificial_u.utils.exceptions import DatabaseError, GenerationError, ProfessorNotFoundError


class ProfessorService:
    """Service for managing professor entities."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        content_service: ContentService,
        image_service: ImageService,
        voice_service: VoiceService,
        logger=None,
    ):
        """
        Initialize the professor service.

        Args:
            repository_factory: Repository factory instance
            content_service: Content generation service
            image_service: Image generation service
            voice_service: Voice service
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.content_service = content_service
        self.image_service = image_service
        self.logger = logger or logging.getLogger(__name__)
        self.voice_service = voice_service

    # --- Generation Method --- #

    async def generate_professor_profile(
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
        final_attrs = {
            **generated_attrs,  # Base: Generated values
            **partial_attributes,  # Overlay: User-provided specifics
            # Ensure resolved/input values take final precedence if they exist
            "department_name": (
                resolved_dept_name if resolved_dept_name else generated_attrs.get("department_name")
            ),
        }

        self.logger.info(
            f"Successfully generated professor profile data for: {final_attrs.get('name')}"
        )
        return final_attrs

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
        model = settings.PROFESSOR_GENERATION_MODEL
        self.logger.debug(f"Calling AI model {model} for professor generation.")

        try:
            generated_content = await self.content_service.generate_text(
                prompt=prompt,
                model=model,
                system_prompt=SYSTEM_PROMPTS["professor"],
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

        self.logger.debug(f"Combined attributes: {combined_attrs}")

        # Pass potentially None values to the prompt function
        return get_professor_prompt(
            existing_professors=existing_profs_data,
            partial_attributes=combined_attrs,
        )

    def _parse_generated_professor_profile(self, generated_content: str) -> Dict[str, Any]:
        """Parses the AI-generated XML content to extract professor attributes."""
        self.logger.debug(f"Attempting to parse generated content:\n{generated_content}")

        # Attempt to extract content within <professor> tags first
        profile_text = extract_xml_content(generated_content, "professor")

        if not profile_text:
            # If extraction helper fails, log and raise.
            # We rely on the LLM adhering to the <professor> tag structure.
            self.logger.error(
                f"Could not extract content within <professor> tags. Raw content starts with: "
                f"{generated_content[:200]}..."
            )
            raise ValueError(
                "Could not find expected <professor> XML tag in the generated content."
            )

        self.logger.debug(f"Extracted content block:\n{profile_text}")

        # Ensure the extracted text is wrapped in <professor> tags for the parser
        # It's possible extract_xml_content returns only the inner content.
        processed_text = profile_text.strip()
        if not processed_text.startswith("<professor>"):
            self.logger.warning("Extracted text missing root <professor> tag, attempting to wrap.")
            # Basic check: if it looks like the inner elements, wrap it.
            # More robust checks might be needed depending on extract_xml_content behavior.
            if processed_text.startswith("<"):
                processed_text = f"<professor>\n{processed_text}\n</professor>"
            else:
                # If it doesn't even start with a tag, wrapping is unlikely to help.
                self.logger.error(
                    f"Extracted text doesn't appear to be valid inner XML: "
                    f"{processed_text[:100]}..."
                )
                raise ValueError("Extracted content block is not valid XML.")

        try:
            # Parse the processed text which should now be a valid XML doc with one root
            return self._parse_professor_profile_xml(processed_text)
        except ET.ParseError as e:
            self.logger.error(
                f"XML parsing failed: {e}\nProcessed Text:\n{processed_text[:500]}..."
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

    # --- CRUD Methods --- #

    def create_professor(self, professor: Professor) -> Professor:
        """
        Saves a new professor object to the database after assigning a voice.

        Args:
            professor: A complete Professor object to be saved.

        Returns:
            The saved Professor object with its assigned ID.

        Raises:
            DatabaseError: If saving to the database fails.
        """
        self.logger.info(f"Attempting to save professor: {professor.name}")

        # Assign a voice before saving
        self._assign_voice_to_professor(professor)

        # Save professor to repository
        try:
            saved_professor = self.repository_factory.professor.create(professor)
            self.logger.info(f"Professor created successfully with ID: {saved_professor.id}")
            return saved_professor
        except Exception as e:
            error_msg = f"Failed to save professor '{professor.name}': {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def _assign_voice_to_professor(self, professor: Professor) -> None:
        """
        Assign a voice to a professor using the VoiceService.
        Updates the professor object in place with a voice_id if possible.
        """
        # If we already have a voice_id, don't override it
        if professor.voice_id:
            self.logger.debug(
                f"Professor {professor.name} already has voice ID {professor.voice_id}. "
                f"Skipping assignment."
            )
            return

        try:
            # Select a voice using VoiceService
            selected_voice = self.voice_service.select_voice_for_professor(professor)

            if not selected_voice:
                self.logger.warning(
                    f"Voice selection did not return a valid voice for {professor.name}"
                )

        except Exception as e:
            # Log warning but don't block professor creation
            self.logger.warning(f"Failed to assign voice to professor {professor.name}: {str(e)}")

    def get_professor(self, professor_id: int) -> Professor:  # Assuming ID is int based on repo
        """
        Get a professor by ID.

        Args:
            professor_id: ID of the professor

        Returns:
            Professor: The professor object

        Raises:
            ProfessorNotFoundError: If professor not found
        """
        professor = self.repository_factory.professor.get(professor_id)
        if not professor:
            error_msg = f"Professor with ID {professor_id} not found"
            self.logger.warning(error_msg)  # Log as warning, raise specific error
            raise ProfessorNotFoundError(error_msg)
        return professor

    def list_professors(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
    ) -> List[Professor]:
        """
        List professors with optional filtering and pagination.

        Args:
            filters: Dictionary of filter criteria (department_id, name, specialization)
            page: Page number (starting from 1)
            size: Number of items per page

        Returns:
            List[Professor]: List of professor objects
        """
        # Get all professors from repository
        try:
            professors = self.repository_factory.professor.list()
        except Exception as e:
            self.logger.error(f"Failed to list professors from repository: {e}", exc_info=True)
            raise DatabaseError("Failed to retrieve professors.") from e

        # Apply filters if provided
        if filters:
            # Assuming filters keys match Professor attribute names
            # Example: filtering by department_id
            dept_id = filters.get("department_id")
            if dept_id is not None:
                professors = [p for p in professors if p.department_id == dept_id]

            name_filter = filters.get("name")
            if name_filter:
                professors = [p for p in professors if name_filter.lower() in p.name.lower()]

            spec_filter = filters.get("specialization")
            if spec_filter:
                professors = [
                    p for p in professors if spec_filter.lower() in p.specialization.lower()
                ]
            # Add more filters as needed

        # Apply pagination if provided
        if page is not None and size is not None and page > 0 and size > 0:
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            total_items = len(professors)
            professors = professors[start_idx:end_idx]
            self.logger.debug(
                f"Pagination applied: page {page}, size {size}. "
                f"Returning {len(professors)} of {total_items} items."
            )
        elif (page is not None and page <= 0) or (size is not None and size <= 0):
            self.logger.warning(
                f"Invalid pagination parameters: page={page}, size={size}. Ignoring pagination."
            )

        return professors

    def update_professor(self, professor_id: int, attributes: Dict[str, Any]) -> Professor:
        """
        Update specific attributes of an existing professor.

        Args:
            professor_id: ID of the professor to update.
            attributes: Dictionary of attributes to update.

        Returns:
            The updated Professor object.

        Raises:
            ProfessorNotFoundError: If the professor is not found.
            DatabaseError: If the update fails.
        """
        self.logger.info(
            f"Updating professor {professor_id} with attributes: {list(attributes.keys())}"
        )
        # Use the repository's update_field method directly for efficiency
        try:
            updated_professor = self.repository_factory.professor.update_field(
                professor_id=professor_id, **attributes
            )
            if updated_professor is None:
                raise ProfessorNotFoundError(
                    f"Professor with ID {professor_id} not found for update."
                )

            self.logger.info(f"Professor {professor_id} updated successfully.")
            return updated_professor
        except ProfessorNotFoundError:  # Re-raise specific error
            self.logger.warning(f"Update failed: Professor {professor_id} not found.")
            raise
        except Exception as e:
            error_msg = f"Failed to update professor {professor_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

    def delete_professor(self, professor_id: int) -> bool:
        """
        Delete a professor by ID.

        Args:
            professor_id: ID of the professor to delete.

        Returns:
            True if deletion was successful.

        Raises:
            ProfessorNotFoundError: If the professor doesn't exist.
            DatabaseError: If deletion fails in the database.
            # Consider adding DependencyError check here if needed
        """
        self.logger.info(f"Attempting to delete professor {professor_id}")
        # Existence check happens within repository.delete in this refactor
        try:
            success = self.repository_factory.professor.delete(professor_id)
            if success:
                self.logger.info(f"Professor {professor_id} deleted successfully")
                return True
            else:
                # This case implies the professor wasn't found by the repo method
                raise ProfessorNotFoundError(f"Delete failed: Professor {professor_id} not found.")
        except ProfessorNotFoundError:  # Re-raise specific error
            self.logger.warning(f"Delete failed: Professor {professor_id} not found.")
            raise
        except Exception as e:
            # Catch potential DB-level errors during delete
            error_msg = f"Database error during deletion of professor {professor_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

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
        professor = self.get_professor(professor_id)

        try:
            # Generate the image using the image service
            image_key = await self.image_service.generate_professor_image(
                professor=professor, aspect_ratio=aspect_ratio
            )
        except Exception as e:
            self.logger.error(
                f"Image generation step failed for professor {professor_id}: {e}",
                exc_info=True,
            )
            raise GenerationError(f"Failed to generate image for professor {professor_id}") from e

        if not image_key:
            self.logger.error(f"Image generation returned no key for professor {professor_id}")
            raise GenerationError(
                f"Image generation yielded no result for professor {professor_id}"
            )

        self.logger.info(f"Image generated for professor {professor_id}: {image_key}")

        # Get the full URL for the image
        try:
            bucket = self.image_service.storage_service.images_bucket
            image_url = self.image_service.storage_service.get_file_url(
                bucket=bucket, object_name=image_key
            )
            self.logger.info(f"Image URL for professor {professor_id}: {image_url}")
        except Exception as e:
            self.logger.error(f"Failed to get image URL for key {image_key}: {e}", exc_info=True)
            raise GenerationError(
                f"Failed to construct image URL for professor {professor_id}"
            ) from e

        # Update the professor record with the new image URL
        try:
            updated_professor = self.update_professor(
                professor_id=professor_id,
                attributes={"image_url": image_url},
            )
            self.logger.info(f"Professor {professor_id} updated with new image URL.")
            return updated_professor
        except (ProfessorNotFoundError, DatabaseError) as e:
            # Re-raise errors from the update step
            self.logger.error(f"Failed to update professor {professor_id} with image URL: {e}")
            raise
