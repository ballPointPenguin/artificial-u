"""
Department service for handling business logic related to departments.
"""

import logging
from math import ceil
from typing import Optional

from fastapi import HTTPException, status

from artificial_u.api.models.departments import (
    CourseBrief,
    DepartmentCoursesResponse,
    DepartmentCreate,
    DepartmentProfessorsResponse,
    DepartmentResponse,
    DepartmentsListResponse,
    DepartmentUpdate,
    ProfessorBrief,
)
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import CourseService as CoreCourseService
from artificial_u.services.department_service import DepartmentService
from artificial_u.services.professor_service import ProfessorService


class DepartmentApiService:
    """Service for department-related operations."""

    def __init__(
        self,
        repository: RepositoryFactory,
        professor_service: ProfessorService,
        course_service: CoreCourseService,
        logger=None,
    ):
        """
        Initialize with required services.

        Args:
            repository: Database repository factory
            professor_service: Professor service for professor-related operations
            course_service: Course service for course-related operations
            logger: Optional logger instance
        """
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)

        # Initialize core service with dependencies
        self.core_service = DepartmentService(
            repository=repository,
            professor_service=professor_service.core_service,
            course_service=course_service.core_service,
            logger=self.logger,
        )

    def get_departments(
        self,
        page: int = 1,
        size: int = 10,
        faculty: Optional[str] = None,
        name: Optional[str] = None,
    ) -> DepartmentsListResponse:
        """
        Get a paginated list of departments with optional filtering.

        Args:
            page: Page number (starting from 1)
            size: Number of items per page
            faculty: Filter by faculty
            name: Filter by name (partial match)

        Returns:
            DepartmentsListResponse with paginated departments
        """
        # Get all departments from core service
        departments = self.core_service.list_departments(faculty)

        # Apply name filter if provided
        if name:
            departments = [d for d in departments if name.lower() in d.name.lower()]

        # Count total before pagination
        total = len(departments)

        # Apply pagination
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_departments = departments[start_idx:end_idx]

        # Calculate total pages
        total_pages = ceil(total / size) if total > 0 else 1

        # Convert to response models
        department_responses = [
            DepartmentResponse.model_validate(d.model_dump())
            for d in paginated_departments
        ]

        return DepartmentsListResponse(
            items=department_responses,
            total=total,
            page=page,
            size=size,
            pages=total_pages,
        )

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
            return DepartmentResponse.model_validate(department.model_dump())
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
            return DepartmentResponse.model_validate(department.model_dump())
        except Exception:
            return None

    def create_department(
        self, department_data: DepartmentCreate
    ) -> DepartmentResponse:
        """
        Create a new department.

        Args:
            department_data: Department data for creation

        Returns:
            Created department with ID
        """
        # Create department using core service
        department = self.core_service.create_department(
            name=department_data.name,
            code=department_data.code,
            faculty=department_data.faculty,
            description=department_data.description,
        )

        # Convert to response model
        return DepartmentResponse.model_validate(department.model_dump())

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
            return DepartmentResponse.model_validate(department.model_dump())
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

    def get_department_courses(
        self, department_id: int
    ) -> Optional[DepartmentCoursesResponse]:
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
                    credits=c.credits,
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
