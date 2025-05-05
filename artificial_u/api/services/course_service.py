"""
Course service for handling business logic related to courses.
"""

import logging
from math import ceil
from typing import List, Optional

from fastapi import HTTPException, status

from artificial_u.api.models.courses import (
    CourseCreate,
    CourseGenerate,
    CourseLecturesResponse,
    CourseResponse,
    CoursesListResponse,
    CourseUpdate,
    DepartmentBrief,
    LectureBrief,
    ProfessorBrief,
)
from artificial_u.models.database import LectureModel

# Import RepositoryFactory directly instead of legacy Repository wrapper
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import (
    ContentService,
    CourseService,
    ProfessorService,
)
from artificial_u.utils import (
    ContentGenerationError,
    CourseNotFoundError,
    DatabaseError,
    LectureNotFoundError,
    ProfessorNotFoundError,
)


class CourseApiService:
    """API Service for course-related operations, using the core CourseService."""

    def __init__(
        self,
        content_service: ContentService,
        professor_service: ProfessorService,
        repository_factory: RepositoryFactory,
        logger=None,
    ):
        """
        Initialize with required services and the repository factory.

        Args:
            repository_factory: RepositoryFactory instance.
            content_service: Content generation service instance.
            professor_service: Core ProfessorService instance.
            logger: Optional logger instance.
        """
        self.repository_factory = repository_factory
        self.logger = logger or logging.getLogger(__name__)

        # Initialize core service with dependencies
        self.core_service = CourseService(
            repository_factory=repository_factory,
            content_service=content_service,
            professor_service=professor_service,
            logger=self.logger,
        )
        # Keep reference to core professor service if needed for direct lookups
        self.professor_service = professor_service

    def get_courses(
        self,
        page: int = 1,
        size: int = 10,
        department_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        level: Optional[str] = None,
        title: Optional[str] = None,
    ) -> CoursesListResponse:
        """
        Get a paginated list of courses with optional filtering.
        Filters by department in the core service, others applied here.
        """
        try:
            # Get courses from core service (only filters by department_id)
            # Core service returns List[Dict[str, Any]] with 'course' and 'professor' keys
            # The 'course' value is a dict representation from course_model_to_dict
            core_courses_list = self.core_service.list_courses(department_id=department_id)

            filtered_courses = core_courses_list

            # Apply additional filters manually
            if professor_id:
                filtered_courses = [
                    item
                    for item in filtered_courses
                    if item.get("course", {}).get("professor_id") == professor_id
                ]
            if level:
                filtered_courses = [
                    item
                    for item in filtered_courses
                    if item.get("course", {}).get("level") == level
                ]
            if title:
                filtered_courses = [
                    item
                    for item in filtered_courses
                    if title.lower() in item.get("course", {}).get("title", "").lower()
                ]

            # Count total after filtering
            total = len(filtered_courses)

            # Apply pagination to the filtered list
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_items = filtered_courses[start_idx:end_idx]

            # Calculate total pages
            total_pages = ceil(total / size) if total > 0 else 1

            # Convert the 'course' dictionary part to response models
            course_responses = [
                CourseResponse.model_validate(item["course"])
                for item in paginated_items
                if "course" in item
            ]

            return CoursesListResponse(
                items=course_responses,
                total=total,
                page=page,
                size=size,
                pages=total_pages,
            )
        except DatabaseError as e:
            self.logger.error(f"Database error getting courses: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve courses due to a database issue.",
            )
        except Exception as e:
            self.logger.error(f"Unexpected error getting courses: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while retrieving courses.",
            )

    def get_course(self, course_id: int) -> CourseResponse:
        """
        Get a course by ID using the core service.
        """
        try:
            course_model = self.core_service.get_course(course_id)
            return CourseResponse.model_validate(course_model)  # Core returns CourseModel
        except CourseNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found",
            )
        except DatabaseError as e:
            self.logger.error(f"Database error getting course {course_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error retrieving course {course_id}.",
            )
        except Exception as e:
            self.logger.error(f"Unexpected error getting course {course_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred retrieving course {course_id}.",
            )

    def get_course_by_code(self, code: str) -> CourseResponse:
        """
        Get a course by its course code using the core service.
        """
        try:
            course_model = self.core_service.get_course_by_code(code)
            return CourseResponse.model_validate(course_model)  # Core returns CourseModel
        except CourseNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with code '{code}' not found",
            )
        except DatabaseError as e:
            self.logger.error(f"Database error getting course by code {code}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error retrieving course code '{code}'.",
            )
        except Exception as e:
            self.logger.error(f"Unexpected error getting course by code {code}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred retrieving course code '{code}'.",
            )

    def create_course(self, course_data: CourseCreate) -> CourseResponse:
        """
        Create a new course using the core service.
        """
        try:
            # Core service expects individual arguments
            # Department ID might need conversion if core expects int vs str
            # Professor ID might need conversion if core expects int vs str
            created_course_model, _ = self.core_service.create_course(
                title=course_data.title,
                code=course_data.code,
                department_id=str(course_data.department_id),  # Assuming core needs str
                level=course_data.level,
                professor_id=str(course_data.professor_id),  # Assuming core needs str
                description=course_data.description,
                credits=course_data.credits,
                weeks=course_data.total_weeks,
                lectures_per_week=course_data.lectures_per_week,
                # topics=None # Pass if needed and supported by API model
            )
            # Convert the returned CourseModel to the API response model
            return CourseResponse.model_validate(created_course_model)
        except ProfessorNotFoundError as e:
            self.logger.warning(f"Professor not found during course creation: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Professor with ID {course_data.professor_id} not found.",
            )
        except DatabaseError as e:
            self.logger.error(f"Database error creating course: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error creating course: {e}",
            )
        except Exception as e:
            self.logger.error(f"Unexpected error creating course: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred creating the course: {e}",
            )

    def update_course(self, course_id: int, course_data: CourseUpdate) -> CourseResponse:
        """
        Update an existing course using the core service.
        """
        try:
            # Core service expects a dictionary of fields to update
            update_data = course_data.model_dump(exclude_unset=True)

            # Convert IDs if necessary (assuming core service needs int/str consistently)
            if "department_id" in update_data:
                update_data["department_id"] = str(update_data["department_id"])
            if "professor_id" in update_data:
                update_data["professor_id"] = str(update_data["professor_id"])

            updated_course_model = self.core_service.update_course(course_id, update_data)

            # Convert the returned CourseModel to the API response model
            return CourseResponse.model_validate(updated_course_model)
        except CourseNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found for update.",
            )
        except ProfessorNotFoundError as e:
            # Handle case where update tries to set a non-existent professor
            self.logger.warning(f"Professor not found during course update: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Professor specified in update not found.",
            )
        except DatabaseError as e:
            self.logger.error(f"Database error updating course {course_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error updating course {course_id}.",
            )
        except Exception as e:
            self.logger.error(f"Unexpected error updating course {course_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred updating course {course_id}.",
            )

    def delete_course(self, course_id: int) -> bool:
        """
        Delete a course using the core service.
        """
        try:
            # Core service returns True on success
            deleted = self.core_service.delete_course(course_id)
            if not deleted:  # Should not happen if core raises CourseNotFound, but check anyway
                raise CourseNotFoundError(
                    f"Course {course_id} not found for deletion (core returned False)."
                )
            return True
        except CourseNotFoundError:
            # Let the router handle the 404 based on the boolean return or this exception
            return False
        except DatabaseError as e:
            # Check for dependency errors if applicable
            if "foreign key constraint" in str(e).lower():
                self.logger.warning(f"Cannot delete course {course_id} due to dependencies: {e}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Cannot delete course {course_id} as it has "
                        "associated resources (e.g., lectures)."
                    ),
                )
            else:
                self.logger.error(f"Database error deleting course {course_id}: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database error deleting course {course_id}.",
                )
        except Exception as e:
            self.logger.error(f"Unexpected error deleting course {course_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred deleting course {course_id}.",
            )

    def get_course_professor(self, course_id: int) -> ProfessorBrief:
        """
        Get the professor who teaches a course.
        Fetches course via core service, then professor via repository factory.
        """
        try:
            # Get the course using the core service
            course = self.core_service.get_course(course_id)

            # Get the professor using the repository factory directly
            professor = self.repository_factory.professor.get(course.professor_id)
            if not professor:
                # This case implies data inconsistency if course exists but professor doesn't
                self.logger.error(
                    f"Professor {course.professor_id} linked to course {course_id} not found."
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Professor for course {course_id} not found (data inconsistency?).",
                )

            # Convert ProfessorModel to ProfessorBrief API model
            return ProfessorBrief(
                id=professor.id,
                name=professor.name,
                title=professor.title,
                department_id=professor.department_id,
                specialization=professor.specialization,
            )
        except CourseNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )
        except DatabaseError as e:
            self.logger.error(
                f"Database error getting professor for course {course_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error retrieving professor for course {course_id}.",
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error getting professor for course {course_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred retrieving professor for course {course_id}.",
            )

    def get_course_department(self, course_id: int) -> DepartmentBrief:
        """
        Get the department of a course.
        Fetches course via core service, then department via repository factory.
        """
        try:
            # Get the course using the core service
            course = self.core_service.get_course(course_id)

            if not course.department_id:
                self.logger.warning(f"Course {course_id} has no associated department ID.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Department information not available for course {course_id}.",
                )

            # Get the department using the repository factory directly
            department = self.repository_factory.department.get(course.department_id)
            if not department:
                # This case implies data inconsistency
                self.logger.error(
                    f"Department {course.department_id} linked to course {course_id} not found."
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Department for course {course_id} not found (data inconsistency?).",
                )

            # Convert DepartmentModel to DepartmentBrief API model
            return DepartmentBrief(
                id=department.id,
                name=department.name,
                code=department.code,
                faculty=department.faculty,
            )
        except CourseNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )
        except DatabaseError as e:
            self.logger.error(
                f"Database error getting department for course {course_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error retrieving department for course {course_id}.",
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error getting department for course {course_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"An unexpected error occurred retrieving "
                    f"department for course {course_id}."
                ),
            )

    def get_course_lectures(self, course_id: int) -> CourseLecturesResponse:
        """
        Get lectures for a course using the repository factory.
        """
        try:
            # First check if course exists using the core service
            self.core_service.get_course(course_id)

            # Get lectures for the course using the repository factory
            lectures: List[LectureModel] = self.repository_factory.lecture.list(course_id=course_id)

            # Convert LectureModel instances to LectureBrief API models
            lecture_briefs = [
                LectureBrief(
                    id=lecture.id,
                    title=lecture.title,
                    week_number=lecture.week_number,
                    order_in_week=lecture.order_in_week,
                    description=lecture.description,
                )
                for lecture in lectures
            ]

            return CourseLecturesResponse(
                course_id=course_id,
                lectures=lecture_briefs,
                total=len(lecture_briefs),
            )
        except CourseNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )
        except LectureNotFoundError:  # If repository.list raises this specifically
            # This scenario (course exists but no lectures found) is not an error
            # The repository should return an empty list in this case.
            # If LectureNotFoundError means the *repository itself* failed, handle as DB error.
            self.logger.warning(f"Lecture lookup failed unexpectedly for course {course_id}")
            # Treat as empty list for now, repository should handle this gracefully.
            return CourseLecturesResponse(course_id=course_id, lectures=[], total=0)
        except DatabaseError as e:
            self.logger.error(
                f"Database error getting lectures for course {course_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error retrieving lectures for course {course_id}.",
            )
        except Exception as e:
            self.logger.error(
                f"Unexpected error getting lectures for course {course_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred retrieving lectures for course {course_id}.",
            )

    async def generate_course(self, generation_data: CourseGenerate) -> CourseResponse:
        """
        Generate course content and structure using AI based on partial data.
        This method *generates* the data but does not create/save the course.

        Args:
            generation_data: Input data containing optional partial attributes and prompt.

        Returns:
            CourseResponse: The generated course data (not saved).

        Raises:
            HTTPException: If generation fails or prerequisites are not found.
        """
        log_attrs = (
            list(generation_data.partial_attributes.keys())
            if generation_data.partial_attributes
            else "None"
        )
        self.logger.info(
            f"Received request to generate course with partial attributes: {log_attrs}"
        )
        try:
            # Prepare attributes for the core service
            partial_attrs = generation_data.partial_attributes or {}  # Start with partial attrs
            if generation_data.freeform_prompt:  # Add prompt if provided
                partial_attrs["freeform_prompt"] = generation_data.freeform_prompt

            # Call the core service to generate the course content dictionary
            generated_dict = await self.core_service.generate_course_content(
                partial_attributes=partial_attrs
            )

            # Convert the dictionary to the API response model
            # Add placeholder ID and validate
            generated_dict["id"] = -1  # Placeholder for validation

            # Validate and convert using the standard response model
            response = CourseResponse.model_validate(generated_dict)

            self.logger.info(
                f"Successfully generated course data: {response.code} - {response.title}"
            )
            return response

        except (ContentGenerationError, DatabaseError, ValueError) as e:
            # Handle errors from core service (generation, DB lookups, parsing)
            self.logger.error(f"Course generation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate course data: {e}",
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during course generation: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=("An unexpected error occurred during course generation."),
            )
