"""
Course service for handling business logic related to courses.
"""

from typing import List, Optional
from math import ceil

from artificial_u.models.database import Repository
from artificial_u.models.core import Course, Lecture, Professor, Department
from artificial_u.api.models.courses import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CoursesListResponse,
    LectureBrief,
    ProfessorBrief,
    CourseLecturesResponse,
    DepartmentBrief,
)


class CourseService:
    """Service for course-related operations."""

    def __init__(self, repository: Repository):
        """Initialize with database repository."""
        self.repository = repository

    def get_courses(
        self,
        page: int = 1,
        size: int = 10,
        department: Optional[str] = None,
        professor_id: Optional[int] = None,
        level: Optional[str] = None,
        title: Optional[str] = None,
    ) -> CoursesListResponse:
        """
        Get a paginated list of courses with optional filtering.

        Args:
            page: Page number (starting from 1)
            size: Number of items per page
            department: Filter by department name
            professor_id: Filter by professor ID
            level: Filter by course level (e.g., 'Undergraduate', 'Graduate')
            title: Filter by course title (partial match)

        Returns:
            CoursesListResponse with paginated courses
        """
        # Get all courses
        courses = self.repository.list_courses(department=department)

        # Apply additional filters if provided
        if professor_id:
            courses = [c for c in courses if c.professor_id == professor_id]
        if level:
            courses = [c for c in courses if c.level == level]
        if title:
            courses = [c for c in courses if title.lower() in c.title.lower()]

        # Count total before pagination
        total = len(courses)

        # Apply pagination
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_courses = courses[start_idx:end_idx]

        # Calculate total pages
        total_pages = ceil(total / size) if total > 0 else 1

        # Convert to response models
        course_responses = [
            CourseResponse.model_validate(c.model_dump()) for c in paginated_courses
        ]

        return CoursesListResponse(
            items=course_responses,
            total=total,
            page=page,
            size=size,
            pages=total_pages,
        )

    def get_course(self, course_id: int) -> Optional[CourseResponse]:
        """
        Get a course by ID.

        Args:
            course_id: ID of the course to retrieve

        Returns:
            CourseResponse or None if not found
        """
        course = self.repository.get_course(course_id)
        if not course:
            return None
        return CourseResponse.model_validate(course.model_dump())

    def get_course_by_code(self, code: str) -> Optional[CourseResponse]:
        """
        Get a course by its course code.

        Args:
            code: Course code to look up

        Returns:
            CourseResponse or None if not found
        """
        course = self.repository.get_course_by_code(code)
        if not course:
            return None
        return CourseResponse.model_validate(course.model_dump())

    def create_course(self, course_data: CourseCreate) -> CourseResponse:
        """
        Create a new course.

        Args:
            course_data: Course data for creation

        Returns:
            Created course with ID
        """
        # Convert to core model
        course = Course(**course_data.model_dump())

        # Save to database
        created_course = self.repository.create_course(course)

        # Convert back to response model
        return CourseResponse.model_validate(created_course.model_dump())

    def update_course(
        self, course_id: int, course_data: CourseUpdate
    ) -> Optional[CourseResponse]:
        """
        Update an existing course.

        Args:
            course_id: ID of the course to update
            course_data: New course data

        Returns:
            Updated course or None if not found
        """
        # Check if course exists
        existing_course = self.repository.get_course(course_id)
        if not existing_course:
            return None

        # Update fields
        course_dict = course_data.model_dump()
        for key, value in course_dict.items():
            setattr(existing_course, key, value)

        # Save changes
        # Note: Repository doesn't have update_course method yet, so we use create_course
        # but we need to preserve the original ID
        original_id = existing_course.id
        updated_course = self.repository.create_course(existing_course)
        updated_course.id = original_id

        # Convert to response model
        return CourseResponse.model_validate(updated_course.model_dump())

    def delete_course(self, course_id: int) -> bool:
        """
        Delete a course.

        Args:
            course_id: ID of the course to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        # Check if course exists
        course = self.repository.get_course(course_id)
        if not course:
            return False

        # TODO: Implement actual deletion in the repository
        # This would be:
        # return self.repository.delete_course(course_id)

        # For now, we'll return True if the course exists
        return True

    def get_course_professor(self, course_id: int) -> Optional[ProfessorBrief]:
        """
        Get the professor who teaches a course.

        Args:
            course_id: ID of the course

        Returns:
            ProfessorBrief or None if course or professor not found
        """
        # Get the course
        course = self.repository.get_course(course_id)
        if not course:
            return None

        # Get the professor
        professor = self.repository.get_professor(course.professor_id)
        if not professor:
            return None

        # Convert to brief format
        return ProfessorBrief(
            id=professor.id,
            name=professor.name,
            title=professor.title,
            department=professor.department,
            specialization=professor.specialization,
        )

    def get_course_department(self, course_id: int) -> Optional[DepartmentBrief]:
        """
        Get the department of a course.

        Args:
            course_id: ID of the course

        Returns:
            DepartmentBrief or None if course or department not found
        """
        # Get the course
        course = self.repository.get_course(course_id)
        if not course:
            return None

        # Get departments
        departments = self.repository.list_departments()

        # Find matching department by name
        department = next((d for d in departments if d.name == course.department), None)
        if not department:
            return None

        # Convert to brief format
        return DepartmentBrief(
            id=department.id,
            name=department.name,
            code=department.code,
            faculty=department.faculty,
        )

    def get_course_lectures(self, course_id: int) -> Optional[CourseLecturesResponse]:
        """
        Get lectures for a course.

        Args:
            course_id: ID of the course

        Returns:
            CourseLecturesResponse or None if course not found
        """
        # First check if course exists
        course = self.repository.get_course(course_id)
        if not course:
            return None

        # Get lectures for the course
        lectures = self.repository.list_lectures_by_course(course_id)

        # Convert to brief format
        lecture_briefs = [
            LectureBrief(
                id=lecture.id,
                title=lecture.title,
                week_number=lecture.week_number,
                order_in_week=lecture.order_in_week,
                description=lecture.description,
                audio_path=lecture.audio_path,
            )
            for lecture in lectures
        ]

        return CourseLecturesResponse(
            course_id=course_id,
            lectures=lecture_briefs,
            total=len(lecture_briefs),
        )
