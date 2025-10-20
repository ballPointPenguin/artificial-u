"""
Course service for handling business logic related to courses.
"""

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
    GeneratedCourseData,
    LectureBrief,
    ProfessorBrief,
)
from artificial_u.api.services.base_service import BaseApiService
from artificial_u.models.core import Course as CoreCourse
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


class CourseApiService(BaseApiService[CoreCourse, CourseResponse, CoursesListResponse]):
    """API Service for course-related operations, using the core CourseService."""

    def __init__(
        self,
        content_service: ContentService,
        professor_service: ProfessorService,
        repository_factory: RepositoryFactory,
        course_service: CourseService,
        logger=None,
    ):
        """
        Initialize with required services and the repository factory.

        Args:
            repository_factory: RepositoryFactory instance.
            content_service: Content generation service instance.
            professor_service: Core ProfessorService instance.
            course_service: Core CourseService instance with smart selection.
            logger: Optional logger instance.
        """
        super().__init__(logger)
        self.repository_factory = repository_factory

        # Use the provided core service (already configured with smart selection)
        self.core_service = course_service

        # Initialize generator service for AI generation workflows
        from artificial_u.services.course_generator_service import (
            CourseGeneratorService,
        )
        from artificial_u.services.job_enqueue_service import JobEnqueueService

        # Create job enqueue service for background processing
        job_enqueue_service = JobEnqueueService(
            repository_factory=repository_factory,
            logger=self.logger,
        )

        self.generator_service = CourseGeneratorService(
            course_service=self.core_service,
            professor_service=professor_service,
            content_service=content_service,
            repository_factory=repository_factory,
            job_enqueue_service=job_enqueue_service,
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
            paginated_items = self._paginate_items(filtered_courses, page, size)

            # Convert the 'course' dictionary part to response models
            course_responses = []
            for item in paginated_items:
                if "course" in item:
                    course_data = item["course"].copy()
                    # Add student information if available
                    if "student" in item and item["student"]:
                        course_data["student"] = item["student"]
                    # Add professor information if available
                    if "professor" in item and item["professor"]:
                        course_data["professor"] = item["professor"]
                    # Add department information if available
                    if "department" in item and item["department"]:
                        course_data["department"] = item["department"]
                    course_responses.append(CourseResponse.model_validate(course_data))

            return self._create_list_response(
                course_responses, total, page, size, CoursesListResponse
            )
        except DatabaseError as e:
            self._handle_database_error("get courses", e)
        except Exception as e:
            self._handle_general_error("get courses", e)

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
            self._handle_database_error("get course", e)
        except Exception as e:
            self._handle_general_error("get course", e)

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
            self._handle_database_error("get course by code", e)
        except Exception as e:
            self._handle_general_error("get course by code", e)

    async def create_course(
        self,
        course_data: CourseCreate,
        *,
        created_by: Optional[int] = None,
        created_with: Optional[str] = None,
    ) -> CourseResponse:
        """
        Create a new course using the core service with smart selection.
        """
        try:
            # Core service expects Optional[int] for department_id and professor_id
            # Smart selection will resolve these if they're None
            created_course_model, _ = await self.core_service.create_course(
                title=course_data.title,
                code=course_data.code,
                department_id=course_data.department_id,  # Can be None for smart selection
                level=course_data.level,
                professor_id=course_data.professor_id,  # Can be None for smart selection
                description=course_data.description,
                credits=course_data.credits,
                weeks=course_data.total_weeks,
                lectures_per_week=course_data.lectures_per_week,
                created_by=created_by,
                created_with=created_with,
            )
            # Convert the returned CourseModel to the API response model
            return CourseResponse.model_validate(created_course_model)
        except ProfessorNotFoundError as e:
            self.logger.warning(f"Professor not found during course creation: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Professor with ID {course_data.professor_id} not found.",
            )
        except ContentGenerationError as e:
            self.logger.error(f"Smart selection failed during course creation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Smart selection failed: {e}",
            )
        except ValueError as e:
            # Handle cases where smart selection services are not available
            self.logger.error(f"Course creation failed with ValueError: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Course creation failed: {e}",
            )
        except DatabaseError as e:
            self._handle_database_error("create course", e)
        except Exception as e:
            self._handle_general_error("create course", e)

    def update_course(self, course_id: int, course_data: CourseUpdate) -> CourseResponse:
        """
        Update an existing course using the core service.
        """
        try:
            # Core service expects a dictionary of fields to update
            update_data = course_data.model_dump(exclude_unset=True)

            # Core service handles integer IDs, no conversion needed
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
            self._handle_database_error("update course", e)
        except Exception as e:
            self._handle_general_error("update course", e)

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
                self._handle_database_error("delete course", e)
        except Exception as e:
            self._handle_general_error("delete course", e)

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
                image_url=professor.image_url,
            )
        except CourseNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found.",
            )
        except DatabaseError as e:
            self._handle_database_error("get course professor", e)
        except Exception as e:
            self._handle_general_error("get course professor", e)

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
            self._handle_database_error("get course department", e)
        except Exception as e:
            self._handle_general_error("get course department", e)

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
                    course_id=lecture.course_id,
                    topic_id=lecture.topic_id,
                    title=lecture.title,
                    summary=lecture.summary,
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
            self._handle_database_error("get course lectures", e)
        except Exception as e:
            self._handle_general_error("get course lectures", e)

    async def generate_course(self, generation_data: CourseGenerate) -> GeneratedCourseData:
        """
        Generate course content and structure using AI based on partial data.
        This method *generates* the data but does not create/save the course.

        Args:
            generation_data: Input data containing optional partial attributes and prompt.

        Returns:
            GeneratedCourseData: The generated course data (not saved), allowing partial fields.

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

            # Call the generator service to generate the course content dictionary
            generated_dict = await self.generator_service.generate_course(
                partial_attributes=partial_attrs
            )

            # Ensure 'id' is present for the response model, even if it's a placeholder
            # The model itself has a default, but setting it here ensures consistency
            # if the core service might return an 'id'.
            if "id" not in generated_dict or generated_dict["id"] is None:
                generated_dict["id"] = -1

            # Validate and convert using the new GeneratedCourseData model
            response = GeneratedCourseData.model_validate(generated_dict)

            self.logger.info(
                f"Generated course (partial validation): C='{response.code}', T='{response.title}'"
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
