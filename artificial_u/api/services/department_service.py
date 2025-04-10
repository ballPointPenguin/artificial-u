"""
Department service for handling business logic related to departments.
"""

from typing import List, Optional
from math import ceil

from artificial_u.models.database import Repository
from artificial_u.models.core import Department, Professor, Course
from artificial_u.api.models.departments import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentsListResponse,
    ProfessorBrief,
    CourseBrief,
    DepartmentProfessorsResponse,
    DepartmentCoursesResponse,
)


class DepartmentService:
    """Service for department-related operations."""

    def __init__(self, repository: Repository):
        """Initialize with database repository."""
        self.repository = repository

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
        # Get all departments
        departments = self.repository.list_departments()

        # Apply filters if provided
        if faculty:
            departments = [d for d in departments if d.faculty == faculty]
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
        department = self.repository.get_department(department_id)
        if not department:
            return None
        return DepartmentResponse.model_validate(department.model_dump())

    def get_department_by_code(self, code: str) -> Optional[DepartmentResponse]:
        """
        Get a department by its code.

        Args:
            code: Department code (e.g., "CS" for Computer Science)

        Returns:
            DepartmentResponse or None if not found
        """
        department = self.repository.get_department_by_code(code)
        if not department:
            return None
        return DepartmentResponse.model_validate(department.model_dump())

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
        # Convert to core model
        department = Department(**department_data.model_dump())

        # Save to database
        created_department = self.repository.create_department(department)

        # Convert back to response model
        return DepartmentResponse.model_validate(created_department.model_dump())

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
        # Check if department exists
        existing_department = self.repository.get_department(department_id)
        if not existing_department:
            return None

        # Update fields
        department_dict = department_data.model_dump()
        for key, value in department_dict.items():
            setattr(existing_department, key, value)

        # Save changes
        updated_department = self.repository.update_department(existing_department)

        # Convert to response model
        return DepartmentResponse.model_validate(updated_department.model_dump())

    def delete_department(self, department_id: int) -> bool:
        """
        Delete a department.

        Args:
            department_id: ID of the department to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        # Check if department exists
        department = self.repository.get_department(department_id)
        if not department:
            return False

        # Check if department has associated resources
        professors = self.repository.list_professors()
        department_professors = [
            p for p in professors if p.department == department.name
        ]

        # Don't delete if has associated professors
        if department_professors:
            return False

        # TODO: Implement actual deletion in the repository
        # This would be:
        # return self.repository.delete_department(department_id)

        return True

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
        # First check if department exists
        department = self.repository.get_department(department_id)
        if not department:
            return None

        # Get all professors
        all_professors = self.repository.list_professors()

        # Filter professors by department name
        department_professors = [
            p for p in all_professors if p.department == department.name
        ]

        # Convert to brief format
        professor_briefs = [
            ProfessorBrief(
                id=p.id,
                name=p.name,
                title=p.title,
                specialization=p.specialization,
            )
            for p in department_professors
        ]

        return DepartmentProfessorsResponse(
            department_id=department_id,
            professors=professor_briefs,
            total=len(professor_briefs),
        )

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
        # First check if department exists
        department = self.repository.get_department(department_id)
        if not department:
            return None

        # Get all courses
        all_courses = self.repository.list_courses()

        # Filter courses by department name
        department_courses = [c for c in all_courses if c.department == department.name]

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
            for c in department_courses
        ]

        return DepartmentCoursesResponse(
            department_id=department_id,
            courses=course_briefs,
            total=len(course_briefs),
        )
