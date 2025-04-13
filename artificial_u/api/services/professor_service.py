"""
Professor service for handling business logic related to professors.
"""

from math import ceil
from typing import Optional

from artificial_u.api.models.professors import (
    CourseBrief,
    LectureBrief,
    ProfessorCoursesResponse,
    ProfessorCreate,
    ProfessorLecturesResponse,
    ProfessorResponse,
    ProfessorsListResponse,
    ProfessorUpdate,
)
from artificial_u.models.core import Professor
from artificial_u.models.repositories import RepositoryFactory


class ProfessorService:
    """Service for professor-related operations."""

    def __init__(self, repository: RepositoryFactory):
        """Initialize with database repository."""
        self.repository = repository

    def get_professors(
        self,
        page: int = 1,
        size: int = 10,
        department_id: Optional[int] = None,
        name: Optional[str] = None,
        specialization: Optional[str] = None,
    ) -> ProfessorsListResponse:
        """
        Get a paginated list of professors with optional filtering.

        Args:
            page: Page number (starting from 1)
            size: Number of items per page
            department_id: Filter by department ID
            name: Filter by name (partial match)
            specialization: Filter by specialization (partial match)

        Returns:
            ProfessorsListResponse with paginated professors
        """
        # Get all professors
        professors = self.repository.professor.list()

        # Apply filters if provided
        if department_id:
            professors = [p for p in professors if p.department_id == department_id]
        if name:
            professors = [p for p in professors if name.lower() in p.name.lower()]
        if specialization:
            professors = [
                p
                for p in professors
                if specialization.lower() in p.specialization.lower()
            ]

        # Count total before pagination
        total = len(professors)

        # Apply pagination
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_professors = professors[start_idx:end_idx]

        # Calculate total pages
        total_pages = ceil(total / size) if total > 0 else 1

        # Convert to response models
        professor_responses = [
            ProfessorResponse.model_validate(p.model_dump())
            for p in paginated_professors
        ]

        return ProfessorsListResponse(
            items=professor_responses,
            total=total,
            page=page,
            size=size,
            pages=total_pages,
        )

    def get_professor(self, professor_id: int) -> Optional[ProfessorResponse]:
        """
        Get a professor by ID.

        Args:
            professor_id: ID of the professor to retrieve

        Returns:
            ProfessorResponse or None if not found
        """
        professor = self.repository.professor.get(professor_id)
        if not professor:
            return None
        return ProfessorResponse.model_validate(professor.model_dump())

    def create_professor(self, professor_data: ProfessorCreate) -> ProfessorResponse:
        """
        Create a new professor.

        Args:
            professor_data: Professor data for creation

        Returns:
            Created professor with ID
        """
        # Convert to core model
        professor = Professor(**professor_data.model_dump())

        # Save to database
        created_professor = self.repository.professor.create(professor)

        # Convert back to response model
        return ProfessorResponse.model_validate(created_professor.model_dump())

    def update_professor(
        self, professor_id: int, professor_data: ProfessorUpdate
    ) -> Optional[ProfessorResponse]:
        """
        Update an existing professor.

        Args:
            professor_id: ID of the professor to update
            professor_data: New professor data

        Returns:
            Updated professor or None if not found
        """
        # Check if professor exists
        existing_professor = self.repository.professor.get(professor_id)
        if not existing_professor:
            return None

        # Update fields
        professor_dict = professor_data.model_dump()
        for key, value in professor_dict.items():
            setattr(existing_professor, key, value)

        # Save changes
        updated_professor = self.repository.professor.update(existing_professor)

        # Convert to response model
        return ProfessorResponse.model_validate(updated_professor.model_dump())

    def delete_professor(self, professor_id: int) -> bool:
        """
        Delete a professor.

        Args:
            professor_id: ID of the professor to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        # Check if professor exists
        professor = self.repository.professor.get(professor_id)
        if not professor:
            return False

        # Delete the professor using the repository method
        return self.repository.professor.delete(professor_id)

    def get_professor_courses(
        self, professor_id: int
    ) -> Optional[ProfessorCoursesResponse]:
        """
        Get courses taught by a professor.

        Args:
            professor_id: ID of the professor

        Returns:
            ProfessorCoursesResponse or None if professor not found
        """
        # First check if professor exists
        professor = self.repository.professor.get(professor_id)
        if not professor:
            return None

        # Get all courses
        all_courses = self.repository.course.list()

        # Filter courses by professor_id
        professor_courses = [c for c in all_courses if c.professor_id == professor_id]

        # Convert to brief format
        course_briefs = [
            CourseBrief(
                id=c.id,
                code=c.code,
                title=c.title,
                department_id=c.department_id,
                level=c.level,
                credits=c.credits,
            )
            for c in professor_courses
        ]

        return ProfessorCoursesResponse(
            professor_id=professor_id,
            courses=course_briefs,
            total=len(course_briefs),
        )

    def get_professor_lectures(
        self, professor_id: int
    ) -> Optional[ProfessorLecturesResponse]:
        """
        Get lectures by a professor.

        Args:
            professor_id: ID of the professor

        Returns:
            ProfessorLecturesResponse or None if professor not found
        """
        # First check if professor exists
        professor = self.repository.professor.get(professor_id)
        if not professor:
            return None

        # Get courses taught by the professor
        all_courses = self.repository.course.list()
        professor_courses = [c for c in all_courses if c.professor_id == professor_id]

        # Get lectures for all these courses
        all_lectures = []
        for course in professor_courses:
            course_lectures = self.repository.lecture.list_by_course(course.id)
            all_lectures.extend(course_lectures)

        # Convert to brief format
        lecture_briefs = [
            LectureBrief(
                id=lecture.id,
                title=lecture.title,
                course_id=lecture.course_id,
                week_number=lecture.week_number,
                order_in_week=lecture.order_in_week,
                description=lecture.description,
            )
            for lecture in all_lectures
        ]

        return ProfessorLecturesResponse(
            professor_id=professor_id,
            lectures=lecture_briefs,
            total=len(lecture_briefs),
        )
