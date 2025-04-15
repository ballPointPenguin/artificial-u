"""
Course service for handling business logic related to courses.
"""

import logging
from math import ceil
from typing import Optional

from fastapi import HTTPException, status

from artificial_u.api.models.courses import (
    CourseCreate,
    CourseLecturesResponse,
    CourseResponse,
    CoursesListResponse,
    CourseUpdate,
    DepartmentBrief,
    LectureBrief,
    ProfessorBrief,
)
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import CourseService
from artificial_u.services.content_service import ContentService
from artificial_u.services.professor_service import ProfessorService


class CourseApiService:
    """Service for course-related operations."""

    def __init__(
        self,
        repository: RepositoryFactory,
        content_service: ContentService,
        professor_service: ProfessorService,
        logger=None,
    ):
        """
        Initialize with required services.

        Args:
            repository: Database repository factory
            professor_service: Professor service for professor-related operations
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

        # Initialize core service with dependencies
        self.core_service = CourseService(
            repository=repository,
            content_service=content_service,
            professor_service=professor_service,
            logger=self.logger,
        )

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

        Args:
            page: Page number (starting from 1)
            size: Number of items per page
            department_id: Filter by department ID
            professor_id: Filter by professor ID
            level: Filter by course level (e.g., 'Undergraduate', 'Graduate')
            title: Filter by course title (partial match)

        Returns:
            CoursesListResponse with paginated courses
        """
        try:
            # Get courses from core service
            courses = self.core_service.list_courses(department=department_id)

            # Apply additional filters if provided
            if professor_id:
                courses = [
                    c for c in courses if c["course"].professor_id == professor_id
                ]
            if level:
                courses = [c for c in courses if c["course"].level == level]
            if title:
                courses = [
                    c for c in courses if title.lower() in c["course"].title.lower()
                ]

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
                CourseResponse.model_validate(c["course"].model_dump())
                for c in paginated_courses
            ]

            return CoursesListResponse(
                items=course_responses,
                total=total,
                page=page,
                size=size,
                pages=total_pages,
            )
        except Exception as e:
            self.logger.error(f"Error getting courses: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve courses",
            )

    def get_course(self, course_id: int) -> Optional[CourseResponse]:
        """
        Get a course by ID.

        Args:
            course_id: ID of the course to retrieve

        Returns:
            CourseResponse or None if not found
        """
        try:
            course = self.core_service.get_course(course_id)
            if not course:
                return None
            return CourseResponse.model_validate(course.model_dump())
        except Exception as e:
            self.logger.error(f"Error getting course {course_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve course",
            )

    def get_course_by_code(self, code: str) -> Optional[CourseResponse]:
        """
        Get a course by its course code.

        Args:
            code: Course code to look up

        Returns:
            CourseResponse or None if not found
        """
        try:
            course = self.core_service.get_course_by_code(code)
            if not course:
                return None
            return CourseResponse.model_validate(course.model_dump())
        except Exception as e:
            self.logger.error(f"Error getting course by code {code}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve course",
            )

    def create_course(self, course_data: CourseCreate) -> CourseResponse:
        """
        Create a new course.

        Args:
            course_data: Course data for creation

        Returns:
            Created course with ID
        """
        try:
            # Create course using core service
            course, _ = self.core_service.create_course(
                title=course_data.title,
                code=course_data.code,
                department=course_data.department_id,  # Note: This might need adjustment
                level=course_data.level,
                professor_id=course_data.professor_id,
                description=course_data.description,
                weeks=course_data.total_weeks,
                lectures_per_week=course_data.lectures_per_week,
            )

            # Convert to response model
            return CourseResponse.model_validate(course.model_dump())
        except Exception as e:
            self.logger.error(f"Error creating course: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

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
        try:
            # Get existing course
            existing_course = self.core_service.get_course(course_id)
            if not existing_course:
                return None

            # Update fields from the provided data
            update_data = course_data.model_dump(exclude_unset=True)

            # Create updated course object
            updated_course = existing_course.model_copy(update=update_data)

            # Save changes using core service
            # Note: This assumes the core service has an update method
            # If not, we need to implement it
            updated_course = self.core_service.update_course(updated_course)

            # Convert to response model
            return CourseResponse.model_validate(updated_course.model_dump())
        except Exception as e:
            self.logger.error(f"Error updating course: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    def delete_course(self, course_id: int) -> bool:
        """
        Delete a course.

        Args:
            course_id: ID of the course to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Check if course exists
            course = self.core_service.get_course(course_id)
            if not course:
                return False

            # Delete the course using core service
            # Note: This assumes the core service has a delete method
            # If not, we need to implement it
            return self.core_service.delete_course(course_id)
        except Exception as e:
            self.logger.error(f"Error deleting course: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

    def get_course_professor(self, course_id: int) -> Optional[ProfessorBrief]:
        """
        Get the professor who teaches a course.

        Args:
            course_id: ID of the course

        Returns:
            ProfessorBrief or None if course or professor not found
        """
        try:
            # Get the course
            course = self.core_service.get_course(course_id)
            if not course:
                return None

            # Get the professor using the professor service
            professor = self.core_service.professor_service.get_professor(
                course.professor_id
            )
            if not professor:
                return None

            # Convert to brief format
            return ProfessorBrief(
                id=professor.id,
                name=professor.name,
                title=professor.title,
                department_id=professor.department_id,
                specialization=professor.specialization,
            )
        except Exception as e:
            self.logger.error(f"Error getting course professor: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve course professor",
            )

    def get_course_department(self, course_id: int) -> Optional[DepartmentBrief]:
        """
        Get the department of a course.

        Args:
            course_id: ID of the course

        Returns:
            DepartmentBrief or None if course or department not found
        """
        try:
            # Get the course
            course = self.core_service.get_course(course_id)
            if not course or not course.department_id:
                return None

            # Get the department using the core service
            # Note: This assumes the core service has a method to get department
            # If not, we need to implement it
            department = self.core_service.get_department(course.department_id)
            if not department:
                return None

            # Convert to brief format
            return DepartmentBrief(
                id=department.id,
                name=department.name,
                code=department.code,
                faculty=department.faculty,
            )
        except Exception as e:
            self.logger.error(f"Error getting course department: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve course department",
            )

    def get_course_lectures(self, course_id: int) -> Optional[CourseLecturesResponse]:
        """
        Get lectures for a course.

        Args:
            course_id: ID of the course

        Returns:
            CourseLecturesResponse or None if course not found
        """
        try:
            # First check if course exists
            course = self.core_service.get_course(course_id)
            if not course:
                return None

            # Get lectures for the course using core service
            # Note: This assumes the core service has a method to get lectures
            # If not, we need to implement it
            lectures = self.core_service.get_course_lectures(course_id)

            # Convert to brief format
            lecture_briefs = [
                LectureBrief(
                    id=lecture.id,
                    title=lecture.title,
                    week_number=lecture.week_number,
                    order_in_week=lecture.order_in_week,
                    description=lecture.description,
                    audio_url=lecture.audio_url,
                )
                for lecture in lectures
            ]

            return CourseLecturesResponse(
                course_id=course_id,
                lectures=lecture_briefs,
                total=len(lecture_briefs),
            )
        except Exception as e:
            self.logger.error(f"Error getting course lectures: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve course lectures",
            )
