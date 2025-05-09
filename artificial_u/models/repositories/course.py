"""
Course repository for database operations.
"""

from typing import List, Optional

from artificial_u.models.core import Course
from artificial_u.models.database import CourseModel
from artificial_u.models.repositories.base import BaseRepository


class CourseRepository(BaseRepository):
    """Repository for Course operations."""

    def create(self, course: Course) -> Course:
        """Create a new course."""
        with self.get_session() as session:
            db_course = CourseModel(
                code=course.code,
                title=course.title,
                credits=course.credits,
                description=course.description,
                lectures_per_week=course.lectures_per_week,
                level=course.level,
                total_weeks=course.total_weeks,
                department_id=course.department_id,
                professor_id=course.professor_id,
            )

            session.add(db_course)
            session.commit()
            session.refresh(db_course)

            course.id = db_course.id
            return course

    def get(self, course_id: int) -> Optional[Course]:
        """Get a course by ID."""
        with self.get_session() as session:
            db_course = session.query(CourseModel).filter_by(id=course_id).first()

            if not db_course:
                return None

            return Course(
                id=db_course.id,
                code=db_course.code,
                title=db_course.title,
                credits=db_course.credits,
                description=db_course.description,
                lectures_per_week=db_course.lectures_per_week,
                level=db_course.level,
                total_weeks=db_course.total_weeks,
                department_id=db_course.department_id,
                professor_id=db_course.professor_id,
            )

    def get_by_code(self, code: str) -> Optional[Course]:
        """Get a course by course code."""
        with self.get_session() as session:
            db_course = session.query(CourseModel).filter_by(code=code).first()

            if not db_course:
                return None

            return Course(
                id=db_course.id,
                code=db_course.code,
                title=db_course.title,
                credits=db_course.credits,
                description=db_course.description,
                lectures_per_week=db_course.lectures_per_week,
                level=db_course.level,
                total_weeks=db_course.total_weeks,
                department_id=db_course.department_id,
                professor_id=db_course.professor_id,
            )

    def list(self, department_id: Optional[int] = None) -> List[Course]:
        """List courses with optional department filter."""
        with self.get_session() as session:
            query = session.query(CourseModel)

            if department_id:
                query = query.filter_by(department_id=department_id)

            db_courses = query.all()

            return [
                Course(
                    id=course.id,
                    code=course.code,
                    title=course.title,
                    credits=course.credits,
                    description=course.description,
                    lectures_per_week=course.lectures_per_week,
                    level=course.level,
                    total_weeks=course.total_weeks,
                    department_id=course.department_id,
                    professor_id=course.professor_id,
                )
                for course in db_courses
            ]

    def update(self, course: Course) -> Course:
        """Update an existing course."""
        with self.get_session() as session:
            db_course = session.query(CourseModel).filter_by(id=course.id).first()

            if not db_course:
                raise ValueError(f"Course with ID {course.id} not found")

            # Update fields
            db_course.code = course.code
            db_course.title = course.title
            db_course.credits = course.credits
            db_course.description = course.description
            db_course.lectures_per_week = course.lectures_per_week
            db_course.level = course.level
            db_course.total_weeks = course.total_weeks
            db_course.department_id = course.department_id
            db_course.professor_id = course.professor_id

            session.commit()
            return course

    def delete(self, course_id: int) -> bool:
        """
        Delete a course by ID.

        Args:
            course_id: ID of the course to delete

        Returns:
            True if deleted successfully, False if course not found
        """
        with self.get_session() as session:
            db_course = session.query(CourseModel).filter_by(id=course_id).first()

            if not db_course:
                return False

            session.delete(db_course)
            session.commit()
            return True
