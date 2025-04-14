"""
Professor management service for ArtificialU.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from artificial_u.models.core import Professor
from artificial_u.prompts.base import extract_xml_content
from artificial_u.prompts.professors import get_professor_prompt
from artificial_u.prompts.system import SYSTEM_PROMPTS
from artificial_u.services.content_service import ContentService
from artificial_u.services.image_service import ImageService
from artificial_u.services.voice_service import VoiceService
from artificial_u.utils.exceptions import DatabaseError, ProfessorNotFoundError
from artificial_u.utils.random_generators import RandomGenerators


class ProfessorService:
    """Service for managing professor entities."""

    def __init__(
        self,
        repository,
        content_service: ContentService,
        image_service: ImageService,
        voice_service: Optional[VoiceService] = None,
        logger=None,
    ):
        """
        Initialize the professor service.

        Args:
            repository: Data repository
            content_service: Content generation service
            image_service: Image generation service
            voice_service: Voice service for voice assignment (optional)
            logger: Optional logger instance
        """
        self.repository = repository
        self.content_service = content_service
        self.image_service = image_service
        self.logger = logger or logging.getLogger(__name__)
        self.voice_service = voice_service

    async def create_professor(
        self,
        name: Optional[str] = None,
        title: Optional[str] = None,
        department: Optional[str] = None,
        specialization: Optional[str] = None,
        background: Optional[str] = None,
        teaching_style: Optional[str] = None,
        personality: Optional[str] = None,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        description: Optional[str] = None,
        age: Optional[int] = None,
    ) -> Professor:
        """
        Create a new professor with the given attributes. Async version.

        If parameters are not provided, AI generation or defaults will be used.

        Args:
            name: Professor's name
            title: Academic title
            department: Academic department
            specialization: Research specialization
            background: Professional background
            teaching_style: Teaching methodology
            personality: Personality traits
            gender: Professor's gender (optional)
            accent: Professor's accent (optional)
            description: Physical description of the professor (optional)
            age: Professor's age (optional)

        Returns:
            Professor: The created professor object
        """
        self.logger.info("Creating new professor (async)")

        # First, ensure we have department and specialization
        department = department or RandomGenerators.generate_department()
        specialization = specialization or RandomGenerators.generate_specialization(
            department
        )

        # Consolidate provided attributes
        provided_attrs = {
            k: v
            for k, v in {
                "name": name,
                "title": title,
                "background": background,
                "teaching_style": teaching_style,
                "personality": personality,
                "gender": gender,
                "accent": accent,
                "description": description,
                "age": age,
            }.items()
            if v is not None
        }

        # Try AI generation first
        professor = None
        if self.content_service:
            try:
                professor = await self._create_professor_with_ai(
                    department, specialization, provided_attrs
                )
            except Exception as e:
                self.logger.warning(
                    f"AI generation failed, falling back to random generation: {e}",
                    exc_info=True,
                )

        # If AI generation failed or wasn't attempted, use random generation
        if professor is None:
            professor = self._create_professor_with_random(
                department, specialization, provided_attrs
            )

        # Assign a voice
        self._assign_voice_to_professor(professor)

        # Save professor to repository
        try:
            saved_professor = self.repository.professor.create(professor)
            self.logger.info(f"Professor created with ID: {saved_professor.id}")
            return saved_professor
        except Exception as e:
            error_msg = f"Failed to save professor: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    async def _create_professor_with_ai(
        self,
        department: str,
        specialization: str,
        provided_attrs: dict,
    ) -> Professor:
        """Helper to create professor using AI content generator via ContentService."""
        self.logger.info("Using AI ContentService to generate professor profile")

        # --- 1. Prepare Prompt --- #
        prompt = self._prepare_professor_generation_prompt(
            department, specialization, provided_attrs
        )

        # --- 2. Call Content Service --- #
        try:
            generated_content = await self.content_service.generate_text(
                prompt=prompt,
                model=self._get_model_name(),
                system_prompt=SYSTEM_PROMPTS["professor_profile"],
            )
        except Exception as e:
            self.logger.error(f"ContentService generation failed: {e}", exc_info=True)
            raise  # Re-raise to signal failure to the caller

        if not generated_content:
            self.logger.warning("AI generation returned empty content.")
            raise ValueError("AI generation returned empty content.")

        # --- 3. Parse Response --- #
        generated_attrs = self._parse_generated_professor_profile(generated_content)

        # --- 4. Combine Attributes & Create Professor --- #
        final_attrs = {
            "department": department,
            "specialization": specialization,
            **generated_attrs,  # Use generated attributes first
            **provided_attrs,  # Overwrite with provided attributes
        }

        # Ensure required fields have fallbacks if somehow missed
        final_attrs["name"] = (
            final_attrs.get("name") or RandomGenerators.generate_professor_name()
        )
        final_attrs["title"] = final_attrs.get(
            "title"
        ) or RandomGenerators.generate_professor_title(department)

        # Log final attributes being used
        self.logger.debug(f"Final attributes for professor creation: {final_attrs}")

        # Create professor object
        professor = Professor(**final_attrs)
        self.logger.info(
            f"Successfully generated professor profile using AI: {professor.name}"
        )
        return professor

    def _prepare_professor_generation_prompt(
        self, department: str, specialization: str, provided_attrs: dict
    ) -> str:
        """Prepares the prompt string for professor generation."""
        age_range = None
        if "age" in provided_attrs:
            decade = (provided_attrs["age"] // 10) * 10
            age_range = f"{decade}-{decade+10}"

        return get_professor_prompt(
            department=department,
            specialization=specialization,
            gender=provided_attrs.get("gender"),
            age_range=age_range,
            accent=provided_attrs.get("accent"),
        )

    def _parse_generated_professor_profile(
        self, generated_content: str
    ) -> Dict[str, Any]:
        """Parses the AI-generated content to extract professor attributes."""
        profile_text = extract_xml_content(generated_content, "professor_profile")

        if profile_text:
            return self._parse_professor_profile_xml(profile_text)
        else:
            self.logger.warning(
                "No structured <professor_profile> found. Attempting fallback parsing."
            )
            return self._parse_professor_profile_fallback(generated_content)

    def _parse_professor_profile_xml(self, profile_text: str) -> Dict[str, Any]:
        """Parses the structured XML profile text."""
        profile = {}
        for line in profile_text.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                # Simple normalization of keys
                norm_key = key.strip().lower().replace(" ", "_")
                profile[norm_key] = value.strip()

        # Convert age to integer if present and valid
        generated_age = None
        if "age" in profile:
            try:
                generated_age = int(profile["age"])
            except (ValueError, TypeError):
                self.logger.warning(
                    f"Could not convert generated age '{profile.get('age')}' to integer."
                )

        # Map normalized keys to Professor model fields
        return {
            "name": profile.get("name"),
            "title": profile.get("title"),
            "gender": profile.get("gender"),
            "accent": profile.get("accent"),
            "description": profile.get("description"),
            "background": profile.get("background"),
            "personality": profile.get("personality"),
            "teaching_style": profile.get("teaching_style"),
            "age": generated_age,
        }

    def _parse_professor_profile_fallback(
        self, generated_content: str
    ) -> Dict[str, Any]:
        """Fallback parsing using regex if XML structure is missing."""
        # Basic fallback: try to extract *something* usable
        name_match = re.search(
            r"(?:Name|Professor|Dr\.)[:\s]+([\w\s\.\-]+)",
            generated_content,
            re.IGNORECASE,
        )
        title_match = re.search(
            r"Title[:\s]+([\w\s\(\)\,\-]+)", generated_content, re.IGNORECASE
        )
        # Add more regex fallbacks if needed for other fields

        generated_attrs = {
            "name": name_match.group(1).strip() if name_match else None,
            "title": title_match.group(1).strip() if title_match else None,
            # Add other fallback fields here
        }
        # Clean None values and return
        return {k: v for k, v in generated_attrs.items() if v is not None}

    def _create_professor_with_random(
        self,
        department: str,
        specialization: str,
        provided_attrs: dict,
    ) -> Professor:
        """Helper to create professor using random generation."""
        self.logger.info("Using random generation for professor profile")

        # Generate or use provided attributes
        attrs = {
            "department": department,
            "specialization": specialization,
            "name": (
                provided_attrs.get("name") or RandomGenerators.generate_professor_name()
            ),
            "title": (
                provided_attrs.get("title")
                or RandomGenerators.generate_professor_title(department)
            ),
            "background": (
                provided_attrs.get("background")
                or RandomGenerators.generate_background(specialization)
            ),
            "teaching_style": (
                provided_attrs.get("teaching_style")
                or RandomGenerators.generate_teaching_style()
            ),
            "personality": (
                provided_attrs.get("personality")
                or RandomGenerators.generate_personality()
            ),
            "gender": (
                provided_attrs.get("gender") or RandomGenerators.generate_gender()
            ),
            "accent": (
                provided_attrs.get("accent") or RandomGenerators.generate_accent()
            ),
            "description": (
                provided_attrs.get("description")
                or RandomGenerators.generate_description(provided_attrs.get("gender"))
            ),
            "age": (provided_attrs.get("age") or RandomGenerators.generate_age()),
        }

        # Log generated/used values
        for key, value in attrs.items():
            self.logger.debug(f"Using {key}: {value}")

        # Create professor object
        return Professor(**attrs)

    def _assign_voice_to_professor(self, professor: Professor) -> None:
        """
        Assign a voice to a professor.

        Args:
            professor: Professor object to assign voice to
        """
        try:
            # If we already have a voice_id, don't override it
            if professor.voice_id:
                self.logger.debug(
                    f"Professor {professor.name} already has voice ID {professor.voice_id}"
                )
                return

            # Use the voice service
            if self.voice_service:
                # Select a voice and update professor record
                voice_data = self.voice_service.select_voice_for_professor(professor)

                # Update local professor object
                if "db_voice_id" in voice_data:
                    professor.voice_id = voice_data["db_voice_id"]
                    self.logger.debug(
                        f"Voice ID {voice_data['db_voice_id']} assigned to professor {professor.name}"
                    )
            else:
                self.logger.warning(
                    f"No voice service available to assign voice to professor {professor.name}"
                )

        except Exception as e:
            error_msg = f"Failed to assign voice to professor: {str(e)}"
            self.logger.warning(error_msg)
            # Not raising an exception here as this is not critical

    def get_professor(self, professor_id: str) -> Professor:
        """
        Get a professor by ID.

        Args:
            professor_id: ID of the professor

        Returns:
            Professor: The professor object

        Raises:
            ProfessorNotFoundError: If professor not found
        """
        professor = self.repository.professor.get(professor_id)
        if not professor:
            error_msg = f"Professor with ID {professor_id} not found"
            self.logger.error(error_msg)
            raise ProfessorNotFoundError(error_msg)
        return professor

    def get_or_create_professor(self, professor_id: Optional[str] = None) -> Professor:
        """
        Get an existing professor by ID or create a new one.

        Args:
            professor_id: ID of the professor to retrieve (optional)

        Returns:
            Professor: The retrieved or created professor

        Raises:
            ProfessorNotFoundError: If professor_id is provided but not found
        """
        if professor_id:
            self.logger.debug(f"Retrieving professor with ID: {professor_id}")
            return self.get_professor(professor_id)
        else:
            self.logger.debug("No professor ID provided, creating new professor")
            return self.create_professor()

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
        # Get all professors
        professors = self.repository.professor.list()

        # Apply filters if provided
        if filters:
            if filters.get("department_id") is not None:
                professors = [
                    p for p in professors if p.department_id == filters["department_id"]
                ]
            if filters.get("name"):
                professors = [
                    p for p in professors if filters["name"].lower() in p.name.lower()
                ]
            if filters.get("specialization"):
                professors = [
                    p
                    for p in professors
                    if filters["specialization"].lower() in p.specialization.lower()
                ]

        # Apply pagination if provided
        if page is not None and size is not None:
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            professors = professors[start_idx:end_idx]

        return professors

    def update_professor(
        self, professor_id: str, attributes: Dict[str, Any]
    ) -> Professor:
        """
        Update a professor with specified attributes.

        Args:
            professor_id: ID of the professor to update
            attributes: Dictionary of attributes to update

        Returns:
            Professor: Updated professor

        Raises:
            ProfessorNotFoundError: If professor not found
        """
        # Get existing professor
        professor = self.get_professor(professor_id)

        # Update fields
        for key, value in attributes.items():
            if hasattr(professor, key):
                setattr(professor, key, value)

        # Save changes
        try:
            updated_professor = self.repository.professor.update(professor)
            self.logger.info(f"Professor {professor_id} updated successfully")
            return updated_professor
        except Exception as e:
            error_msg = f"Failed to update professor: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def delete_professor(self, professor_id: str) -> bool:
        """
        Delete a professor.

        Args:
            professor_id: ID of the professor to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            ProfessorNotFoundError: If professor not found
        """
        # Check if professor exists
        professor = self.repository.professor.get(professor_id)
        if not professor:
            error_msg = f"Professor with ID {professor_id} not found"
            self.logger.error(error_msg)
            raise ProfessorNotFoundError(error_msg)

        # Delete the professor
        success = self.repository.professor.delete(professor_id)
        if success:
            self.logger.info(f"Professor {professor_id} deleted successfully")
        else:
            error_msg = f"Failed to delete professor {professor_id}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg)

        return success

    def list_professor_courses(self, professor_id: str) -> List:
        """
        Get courses taught by a professor.

        Args:
            professor_id: ID of the professor

        Returns:
            List: List of courses

        Raises:
            ProfessorNotFoundError: If professor not found
        """
        # Check if professor exists - this will raise an exception if not found
        self.get_professor(professor_id)

        # Get all courses
        all_courses = self.repository.course.list()

        # Filter courses by professor_id
        professor_courses = [c for c in all_courses if c.professor_id == professor_id]

        return professor_courses

    def list_professor_lectures(self, professor_id: str) -> List:
        """
        Get lectures by a professor.

        Args:
            professor_id: ID of the professor

        Returns:
            List: List of lectures

        Raises:
            ProfessorNotFoundError: If professor not found
        """
        # Check if professor exists - this will raise an exception if not found
        self.get_professor(professor_id)

        # Get courses taught by the professor
        professor_courses = self.list_professor_courses(professor_id)

        # Get lectures for all these courses
        all_lectures = []
        for course in professor_courses:
            course_lectures = self.repository.lecture.list_by_course(course.id)
            all_lectures.extend(course_lectures)

        return all_lectures

    async def generate_and_set_professor_image(
        self, professor_id: str, aspect_ratio: str = "1:1"
    ) -> Optional[Professor]:
        """
        Generates an image for the professor and updates their record.

        Args:
            professor_id: The ID of the professor
            aspect_ratio: The desired aspect ratio for the image

        Returns:
            The updated Professor object if successful, None otherwise
        """
        self.logger.info(f"Generating image for professor ID: {professor_id}")

        # Get the professor
        try:
            professor = self.get_professor(professor_id)
        except ProfessorNotFoundError:
            self.logger.error(
                f"Cannot generate image: Professor {professor_id} not found"
            )
            return None

        try:
            # Generate the image using the image service
            image_key = await self.image_service.generate_professor_image(
                professor=professor, aspect_ratio=aspect_ratio
            )

            if not image_key:
                self.logger.error(
                    f"Image generation failed for professor {professor_id}"
                )
                return None

            self.logger.info(
                f"Image generated for professor {professor_id}: {image_key}"
            )

            # Get the full URL for the image using the storage service
            bucket = self.image_service.storage_service.images_bucket
            image_url = self.image_service.storage_service.get_file_url(
                bucket=bucket, object_name=image_key
            )

            self.logger.info(f"Image URL: {image_url}")

            # Update the professor record with the new image URL
            updated_professor = self.update_professor(
                professor_id=professor_id,
                attributes={"image_url": image_url},
            )

            self.logger.info(f"Professor {professor_id} updated with new image URL")
            return updated_professor

        except Exception as e:
            self.logger.error(
                f"Error during image generation or update for professor {professor_id}: {e}",
                exc_info=True,
            )
            return None

    def _get_model_name(self) -> str:
        """Get the appropriate model name from configuration."""
        try:
            from artificial_u.config import get_settings

            settings = get_settings()
            # Use a direct setting or fallback to default
            return getattr(settings, "CLAUDE_MODEL", "claude-3-5-sonnet-20240620")
        except Exception:
            # Fallback model name if settings unavailable
            return "claude-3-5-sonnet-20240620"
