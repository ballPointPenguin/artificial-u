"""
Department service for handling business logic related to departments.
"""

from typing import Optional

from fastapi import HTTPException, status

from artificial_u.api.models.departments import (
    CourseBrief,
    DepartmentCoursesResponse,
    DepartmentCreate,
    DepartmentGenerate,
    DepartmentProfessorsResponse,
    DepartmentResponse,
    DepartmentsListResponse,
    DepartmentUpdate,
    ProfessorBrief,
)
from artificial_u.api.services.base_service import BaseApiService
from artificial_u.models.core import Department as CoreDepartment
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import ContentService, CourseService, DepartmentService, ProfessorService
from artificial_u.utils import (
    ContentGenerationError,
    DatabaseError,
)


class DepartmentApiService(
    BaseApiService[CoreDepartment, DepartmentResponse, DepartmentsListResponse]
):
    """Service for department-related operations."""

    def __init__(
        self,
        course_service: CourseService,
        professor_service: ProfessorService,
        repository_factory: RepositoryFactory,
        content_service: ContentService,
        logger=None,
    ):
        """
        Initialize with required services.

        Args:
            repository_factory: Repository factory instance
            professor_service: Professor service for professor-related operations
            course_service: Course service for course-related operations
            content_service: Content generation service
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.repository_factory = repository_factory

        # Initialize core service (CRUD only) with correct dependencies
        self.core_service = DepartmentService(
            repository_factory=repository_factory,
            professor_service=professor_service,
            course_service=course_service,
            logger=self.logger,
        )

        # Initialize generator service for AI generation workflows
        from artificial_u.services.department_generator_service import DepartmentGeneratorService
        from artificial_u.services.job_enqueue_service import JobEnqueueService

        # Create job enqueue service for background processing
        job_enqueue_service = JobEnqueueService(
            repository_factory=repository_factory,
            logger=self.logger,
        )

        self.generator_service = DepartmentGeneratorService(
            department_service=self.core_service,
            content_service=content_service,
            repository_factory=repository_factory,
            job_enqueue_service=job_enqueue_service,
            logger=self.logger,
        )

    def _enrich_department_with_faculty(self, department: CoreDepartment) -> DepartmentResponse:
        """
        Enrich a department with faculty_name from faculty_id.

        Args:
            department: Core department model

        Returns:
            DepartmentResponse with faculty_name populated
        """
        faculty_name = None
        if department.faculty_id:
            faculty = self.repository_factory.faculty.get(department.faculty_id)
            if faculty:
                faculty_name = faculty.name

        # Create response model with faculty_name
        department_dict = department.model_dump()
        department_dict["faculty_name"] = faculty_name
        return DepartmentResponse.model_validate(department_dict)

    def get_departments(
        self,
        page: int = 1,
        size: int = 10,
        faculty_id: Optional[int] = None,
        name: Optional[str] = None,
        language: Optional[str] = None,
    ) -> DepartmentsListResponse:
        """
        Get a paginated list of departments with optional filtering.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            faculty_id: Filter by faculty ID
            name: Filter by name (partial match)

        Returns:
            DepartmentsListResponse with paginated departments
        """
        try:
            # Get all departments from core service
            all_departments = self.core_service.list_departments(
                faculty_id=faculty_id, language=language
            )

            # Apply name filter if provided
            if name:
                all_departments = [d for d in all_departments if name.lower() in d.name.lower()]

            # Sort departments alphabetically by name (case-insensitive)
            all_departments.sort(key=lambda d: d.name.lower())

            # Count total before pagination
            total = len(all_departments)

            # Apply pagination
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_departments = all_departments[start_idx:end_idx]

            # Enrich departments with faculty_name
            response_items = [
                self._enrich_department_with_faculty(dept) for dept in paginated_departments
            ]

            # Create and return list response
            pages = self._calculate_pages(total, size)
            return DepartmentsListResponse(
                items=response_items,
                total=total,
                page=page,
                size=size,
                pages=pages,
            )
        except Exception as e:
            self._handle_general_error("list departments", e)

    def get_department(self, department_id: int) -> Optional[DepartmentResponse]:
        """
        Get a department by ID.

        Args:
            department_id: ID of the department to retrieve

        Returns:
            DepartmentResponse or None if not found
        """
        try:
            department = self.core_service.get_department(department_id)
            if not department:
                return None
            return self._enrich_department_with_faculty(department)
        except Exception:
            return None

    def get_department_by_code(self, code: str) -> Optional[DepartmentResponse]:
        """
        Get a department by its code.

        Args:
            code: Department code (e.g., "CS" for Computer Science)

        Returns:
            DepartmentResponse or None if not found
        """
        try:
            department = self.core_service.get_department_by_code(code)
            if not department:
                return None
            return self._enrich_department_with_faculty(department)
        except Exception:
            return None

    def create_department(self, department_data: DepartmentCreate) -> DepartmentResponse:
        """
        Create a new department.

        Args:
            department_data: Department data for creation

        Returns:
            Created department with ID
        """
        try:
            # Create department using core service
            department = self.core_service.create_department(
                name=department_data.name,
                code=department_data.code,
                faculty_id=department_data.faculty_id,
                description=department_data.description,
                language=department_data.language,
            )

            # Enrich with faculty_name
            return self._enrich_department_with_faculty(department)
        except Exception as e:
            self._handle_general_error("create department", e)

    def update_department(
        self, department_id: int, department_data: DepartmentUpdate
    ) -> Optional[DepartmentResponse]:
        """
        Update an existing department.

        Args:
            department_id: ID of the department to update
            department_data: New department data

        Returns:
            Updated department or None if not found
        """
        try:
            # Update department using core service
            department = self.core_service.update_department(
                department_id=department_id,
                update_data=department_data.model_dump(exclude_unset=True),
            )
            if not department:
                return None
            return self._enrich_department_with_faculty(department)
        except Exception:
            return None

    def delete_department(self, department_id: int) -> bool:
        """
        Delete a department, checking for dependencies first.

        Args:
            department_id: ID of the department to delete

        Returns:
            True if deleted successfully, False otherwise

        Raises:
            HTTPException 409 Conflict if dependencies exist.
        """
        try:
            return self.core_service.delete_department(department_id)
        except Exception as e:
            if "dependencies" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=str(e),
                )
            return False

    def get_department_professors(
        self, department_id: int
    ) -> Optional[DepartmentProfessorsResponse]:
        """
        Get professors in a department.

        Args:
            department_id: ID of the department

        Returns:
            DepartmentProfessorsResponse or None if department not found
        """
        try:
            # Get professors using core service
            professors = self.core_service.get_department_professors(department_id)

            # Convert to brief format
            professor_briefs = [
                ProfessorBrief(
                    id=p.id,
                    name=p.name,
                    title=p.title,
                    specialization=p.specialization,
                    image_url=p.image_url,
                )
                for p in professors
            ]

            return DepartmentProfessorsResponse(
                department_id=department_id,
                professors=professor_briefs,
                total=len(professor_briefs),
            )
        except Exception:
            return None

    def get_department_courses(self, department_id: int) -> Optional[DepartmentCoursesResponse]:
        """
        Get courses in a department.

        Args:
            department_id: ID of the department

        Returns:
            DepartmentCoursesResponse or None if department not found
        """
        try:
            # Get courses using core service
            courses = self.core_service.get_department_courses(department_id)

            # Convert to brief format
            course_briefs = [
                CourseBrief(
                    id=c.id,
                    code=c.code,
                    title=c.title,
                    level=c.level,
                    professor_id=c.professor_id,
                )
                for c in courses
            ]

            return DepartmentCoursesResponse(
                department_id=department_id,
                courses=course_briefs,
                total=len(course_briefs),
            )
        except Exception:
            return None

    async def generate_department(self, generation_data: DepartmentGenerate) -> DepartmentResponse:
        """
        Generate a department using AI.

        This method *generates* the data but does not create/save the department.

        Args:
            generation_data: Input data containing any known attributes
            and optional freeform prompt.

        Returns:
            DepartmentResponse: The generated department data (not saved).

        Raises:
            HTTPException: If generation fails.
        """
        # Convert model to dict, excluding None values
        attrs = generation_data.model_dump(exclude_none=True)
        self.logger.info(f"Received request to generate department with attributes: {attrs}")

        # Extract the actual partial attributes from the request
        partial_attrs = attrs.get("partial_attributes", {})
        freeform_prompt = attrs.get("freeform_prompt")
        department_id = attrs.get("department_id")
        language = attrs.get("language", "en")

        # Add freeform_prompt to partial_attrs if present (core service expects it there)
        if freeform_prompt:
            partial_attrs["freeform_prompt"] = freeform_prompt

        # Add department_id to partial_attrs if present (for context in generation)
        if department_id:
            partial_attrs["department_id"] = department_id

        partial_attr_keys = list(partial_attrs.keys())
        self.logger.info(f"Generating department with partial attributes: {partial_attr_keys}")

        try:
            # Call generator service with the extracted partial attributes
            generated_dict = await self.generator_service.generate_department(
                partial_attributes=partial_attrs,
                language=language,
            )

            # Convert the dictionary to the API response model
            # Add placeholder ID and validate
            generated_dict["id"] = -1  # Placeholder for validation

            # Enrich with faculty_name if faculty_id is present
            faculty_name = None
            if generated_dict.get("faculty_id"):
                faculty = self.repository_factory.faculty.get(generated_dict["faculty_id"])
                if faculty:
                    faculty_name = faculty.name
            generated_dict["faculty_name"] = faculty_name

            response = DepartmentResponse.model_validate(generated_dict)

            self.logger.info(f"Successfully generated department data: {response.name}")
            return response

        except (ContentGenerationError, DatabaseError, ValueError) as e:
            # Handle errors from core service
            self.logger.error(f"Department generation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate department data: {e}",
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during department generation: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=("An unexpected error occurred during department generation."),
            )
