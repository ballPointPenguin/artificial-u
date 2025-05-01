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
                department_id=course.department_id,
                level=course.level,
                credits=course.credits,
                professor_id=course.professor_id,
                description=course.description,
                lectures_per_week=course.lectures_per_week,
                total_weeks=course.total_weeks,
                topics=course.topics,
            )

            session.add(db_course)
            session.commit()
            session.refresh(db_course)

            course.id = db_course.id
            course.topics = db_course.topics
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
                department_id=db_course.department_id,
                level=db_course.level,
                credits=db_course.credits,
                professor_id=db_course.professor_id,
                description=db_course.description,
                lectures_per_week=db_course.lectures_per_week,
                total_weeks=db_course.total_weeks,
                topics=db_course.topics,
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
                department_id=db_course.department_id,
                level=db_course.level,
                credits=db_course.credits,
                professor_id=db_course.professor_id,
                description=db_course.description,
                lectures_per_week=db_course.lectures_per_week,
                total_weeks=db_course.total_weeks,
                topics=db_course.topics,
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
                    id=c.id,
                    code=c.code,
                    title=c.title,
                    department_id=c.department_id,
                    level=c.level,
                    credits=c.credits,
                    professor_id=c.professor_id,
                    description=c.description,
                    lectures_per_week=c.lectures_per_week,
                    total_weeks=c.total_weeks,
                    topics=c.topics,
                )
                for c in db_courses
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
            db_course.department_id = course.department_id
            db_course.level = course.level
            db_course.credits = course.credits
            db_course.professor_id = course.professor_id
            db_course.description = course.description
            db_course.lectures_per_week = course.lectures_per_week
            db_course.total_weeks = course.total_weeks
            db_course.topics = course.topics

            session.commit()
            course.topics = db_course.topics
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
