"""
Professor management service for ArtificialU.

This service handles CRUD operations for professors. AI generation and complex workflows
are handled by the ProfessorGeneratorService.
"""

import logging
from typing import Any, Dict, List, Optional

from artificial_u.config import get_settings
from artificial_u.models.core import Course, Professor
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.services.voice_service import VoiceService
from artificial_u.utils import (
    DatabaseError,
    ProfessorNotFoundError,
)


class ProfessorService:
    """Service for managing professor entities."""

    def __init__(
        self,
        repository_factory: RepositoryFactory,
        voice_service: VoiceService,
        job_enqueue_service,
        logger=None,
    ):
        """
        Initialize the professor service.

        Args:
            repository_factory: Repository factory instance
            voice_service: Voice selection service
            job_enqueue_service: Job enqueueing service for background tasks
            logger: Optional logger instance
        """
        self.repository_factory = repository_factory
        self.voice_service = voice_service
        self.job_enqueue_service = job_enqueue_service
        self.logger = logger or logging.getLogger(__name__)

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
            # Enqueue background image generation if no image yet (skip during tests)
            if not get_settings().testing:
                try:
                    if not getattr(saved_professor, "image_url", None):
                        self.job_enqueue_service.enqueue_professor_image_generation(
                            saved_professor.id
                        )
                    else:
                        self.logger.debug(
                            "Skipping image generation on create: professor %s already has image",
                            saved_professor.id,
                        )
                except Exception as bg_e:
                    self.logger.error(
                        "Failed to enqueue image generation for professor %s: %s",
                        saved_professor.id,
                        bg_e,
                    )
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
            # Select a voice using VoiceService (this now updates professor.voice_id automatically)
            selected_voice = self.voice_service.select_voice_for_professor(professor)

            if selected_voice:
                voice_name = selected_voice.get("name", "Unknown")
                voice_id = selected_voice.get("db_voice_id", "Unknown")
                self.logger.info(
                    f"Successfully assigned voice '{voice_name}' (ID: {voice_id}) "
                    f"to professor {professor.name}"
                )
            else:
                self.logger.warning(
                    f"Voice selection did not return a valid voice for {professor.name}"
                )

        except Exception as e:
            # Log warning but don't block professor creation
            self.logger.warning(f"Failed to assign voice to professor {professor.name}: {str(e)}")

    def assign_voice_to_professor(self, professor_id: int) -> Professor:
        """
        Assign a voice to an existing professor.

        Args:
            professor_id: ID of the professor to assign voice to

        Returns:
            The updated Professor object with assigned voice

        Raises:
            ProfessorNotFoundError: If professor not found
            DatabaseError: If voice assignment or update fails
        """
        self.logger.info(f"Assigning voice to existing professor {professor_id}")

        # Get the existing professor
        professor = self.get_professor(professor_id)

        # If professor already has a voice, log and continue to reassign
        if professor.voice_id:
            self.logger.info(
                f"Professor {professor.name} currently has voice ID {professor.voice_id}. "
                f"Reassigning voice as requested."
            )

        try:
            # Use the voice assignment logic (this will update the professor in the database)
            selected_voice = self.voice_service.select_voice_for_professor(professor)

            if selected_voice:
                voice_name = selected_voice.get("name", "Unknown")
                voice_id = selected_voice.get("db_voice_id", "Unknown")
                self.logger.info(
                    f"Successfully assigned voice '{voice_name}' (ID: {voice_id}) "
                    f"to professor {professor.name}"
                )

                # Get the updated professor from the database to return
                updated_professor = self.get_professor(professor_id)
                return updated_professor
            else:
                self.logger.warning(
                    f"Voice selection did not return a valid voice for {professor.name}"
                )
                return professor

        except Exception as e:
            error_msg = f"Failed to assign voice to professor {professor.name}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e

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

    # --- Relationship Methods --- #

    def list_professor_courses(self, professor_id: int) -> List[Course]:
        """
        Lists all courses taught by a specific professor.

        Args:
            professor_id: The ID of the professor.

        Returns:
            A list of Course objects taught by the professor.

        Raises:
            ProfessorNotFoundError: If the professor is not found.
            DatabaseError: If there's an issue querying the database.
        """
        self.logger.info(f"Listing courses for professor ID: {professor_id}")

        # First, ensure the professor exists
        if not self.repository_factory.professor.get(professor_id):
            error_msg = f"Professor with ID {professor_id} not found."
            self.logger.warning(error_msg)
            raise ProfessorNotFoundError(error_msg)

        try:
            # Fetch all courses (or courses based on supported filters by .list())
            # and then filter by professor_id in Python.
            # Assuming self.repository_factory.course.list() without arguments lists all courses.
            # If it expects other arguments (e.g., department_id) or has mandatory ones,
            # this might need further adjustment based on CourseRepository's actual signature.
            all_courses = self.repository_factory.course.list()
            courses = [course for course in all_courses if course.professor_id == professor_id]
            self.logger.info(f"Found {len(courses)} courses for prof ID: {professor_id}")
            return courses
        except Exception as e:
            # Preserve the original, more detailed error message if preferred
            # err_str = str(e)
            # error_msg = f"Course list failed for prof {professor_id}: {err_str}"
            error_msg = f"Failed to list courses for professor {professor_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise DatabaseError(error_msg) from e
