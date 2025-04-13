"""
Lecture repository for database operations.
"""

from typing import List, Optional

from sqlalchemy import func, or_

from artificial_u.models.core import Lecture
from artificial_u.models.database import (
    CourseModel,
    LectureModel,
    lecture_model_to_entity,
)
from artificial_u.models.repositories.base import BaseRepository


class LectureRepository(BaseRepository):
    """Repository for Lecture operations."""

    def create(self, lecture: Lecture) -> Lecture:
        """Create a new lecture."""
        with self.get_session() as session:
            db_lecture = LectureModel(
                title=lecture.title,
                course_id=lecture.course_id,
                week_number=lecture.week_number,
                order_in_week=lecture.order_in_week,
                description=lecture.description,
                content=lecture.content,
                audio_url=lecture.audio_url,
                generated_at=lecture.generated_at,
            )

            session.add(db_lecture)
            session.commit()
            session.refresh(db_lecture)

            lecture.id = db_lecture.id
            return lecture

    def get(self, lecture_id: int) -> Optional[Lecture]:
        """
        Get a lecture by ID.

        Args:
            lecture_id: The ID of the lecture to retrieve

        Returns:
            Optional[Lecture]: The lecture if found, None otherwise
        """
        with self.get_session() as session:
            lecture = session.query(LectureModel).filter_by(id=lecture_id).first()
            return lecture_model_to_entity(lecture) if lecture else None

    def get_by_course_week_order(
        self, course_id: int, week_number: int, order_in_week: int
    ) -> Optional[Lecture]:
        """
        Get a lecture by course ID, week number, and order in week.

        Args:
            course_id: The course ID
            week_number: The week number
            order_in_week: The order in the week

        Returns:
            Optional[Lecture]: The lecture if found, None otherwise
        """
        with self.get_session() as session:
            lecture = (
                session.query(LectureModel)
                .filter_by(
                    course_id=course_id,
                    week_number=week_number,
                    order_in_week=order_in_week,
                )
                .first()
            )

            return lecture_model_to_entity(lecture)

    def get_content(self, lecture_id: int) -> Optional[str]:
        """
        Get the content of a lecture by ID.

        Args:
            lecture_id: The ID of the lecture to retrieve content for

        Returns:
            Optional[str]: The lecture content if found, None otherwise
        """
        with self.get_session() as session:
            lecture = session.query(LectureModel).filter_by(id=lecture_id).first()
            return lecture.content if lecture else None

    def get_audio_url(self, lecture_id: int) -> Optional[str]:
        """Get the audio URL for a lecture."""
        with self.get_session() as session:
            lecture = session.get(LectureModel, lecture_id)
            return lecture.audio_url if lecture else None

    def list_by_course(self, course_id: int) -> List[Lecture]:
        """
        List all lectures for a specific course.

        Args:
            course_id: ID of the course to get lectures for

        Returns:
            List[Lecture]: List of lectures for the specified course
        """
        with self.get_session() as session:
            db_lectures = (
                session.query(LectureModel)
                .filter_by(course_id=course_id)
                .order_by(LectureModel.week_number, LectureModel.order_in_week)
                .all()
            )

            return [lecture_model_to_entity(lecture) for lecture in db_lectures]

    def list(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List[Lecture]:
        """
        List lectures with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            search_query: Search query for title/description

        Returns:
            List[Lecture]: List of lectures
        """
        with self.get_session() as session:
            query = session.query(LectureModel)

            # Apply filters
            if course_id is not None:
                query = query.filter(LectureModel.course_id == course_id)

            if professor_id is not None:
                # Join with CourseModel to filter by professor_id
                query = query.join(CourseModel).filter(
                    CourseModel.professor_id == professor_id
                )

            if search_query:
                # Search in title and description
                query = query.filter(
                    or_(
                        LectureModel.title.ilike(f"%{search_query}%"),
                        LectureModel.description.ilike(f"%{search_query}%"),
                    )
                )

            # Apply pagination
            offset = (page - 1) * size
            query = query.order_by(LectureModel.id).offset(offset).limit(size)

            # Execute query
            db_lectures = query.all()

            return [lecture_model_to_entity(lecture) for lecture in db_lectures]

    def count(
        self,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """
        Count lectures with filtering.

        Args:
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            search_query: Search query for title/description

        Returns:
            int: Total count of matching lectures
        """
        with self.get_session() as session:
            query = session.query(func.count(LectureModel.id))

            # Apply filters
            if course_id is not None:
                query = query.filter(LectureModel.course_id == course_id)

            if professor_id is not None:
                # Join with CourseModel to filter by professor_id
                query = query.join(CourseModel).filter(
                    CourseModel.professor_id == professor_id
                )

            if search_query:
                # Search in title and description
                query = query.filter(
                    or_(
                        LectureModel.title.ilike(f"%{search_query}%"),
                        LectureModel.description.ilike(f"%{search_query}%"),
                    )
                )

            # Execute query
            return query.scalar()

    def update(self, lecture: Lecture) -> Lecture:
        """
        Update an existing lecture.

        Args:
            lecture: Lecture object with updated fields

        Returns:
            Lecture: Updated lecture
        """
        with self.get_session() as session:
            lecture_model = session.get(LectureModel, lecture.id)
            if not lecture_model:
                raise ValueError(f"Lecture with ID {lecture.id} not found")

            # Update fields
            lecture_model.title = lecture.title
            lecture_model.course_id = lecture.course_id
            lecture_model.week_number = lecture.week_number
            lecture_model.order_in_week = lecture.order_in_week
            lecture_model.description = lecture.description
            lecture_model.content = lecture.content
            lecture_model.audio_url = lecture.audio_url

            session.add(lecture_model)
            session.commit()

            return lecture

    def delete(self, lecture_id: int) -> bool:
        """
        Delete a lecture.

        Args:
            lecture_id: ID of the lecture to delete

        Returns:
            bool: True if lecture was deleted, False if not found
        """
        with self.get_session() as session:
            db_lecture = session.query(LectureModel).filter_by(id=lecture_id).first()

            if not db_lecture:
                return False

            session.delete(db_lecture)
            session.commit()

            return True

    def build_lecture_summary(self, lecture: Lecture) -> dict:
        """
        Build a summary representation of a lecture.

        Args:
            lecture: Lecture object

        Returns:
            dict: Summary representation of the lecture
        """
        # First get the course details
        with self.get_session() as session:
            course = session.query(CourseModel).filter_by(id=lecture.course_id).first()
            course_title = course.title if course else "Unknown Course"
            professor_id = course.professor_id if course else None

        return {
            "id": lecture.id,
            "title": lecture.title,
            "course_id": lecture.course_id,
            "course_title": course_title,
            "professor_id": professor_id,
            "week_number": lecture.week_number,
            "order_in_week": lecture.order_in_week,
            "description": lecture.description,
            "created_at": lecture.generated_at,
            "has_audio": bool(lecture.audio_url),
        }

    def build_lecture_detail(self, lecture: Lecture) -> dict:
        """
        Build a detailed representation of a lecture.

        Args:
            lecture: Lecture object

        Returns:
            dict: Detailed representation of the lecture
        """
        # Get the summary as the base
        summary = self.build_lecture_summary(lecture)

        # Get professor information
        professor_name = "Unknown Professor"
        professor_id = summary.get("professor_id")

        if professor_id:
            with self.get_session() as session:
                professor = (
                    session.query(CourseModel.professor)
                    .filter_by(id=professor_id)
                    .first()
                )
                if professor:
                    professor_name = professor.name

        # Build the detailed response
        return {
            **summary,
            "content": lecture.content,
            "sections": None,  # For a future implementation with section breakdown
            "audio_url": lecture.audio_url,
            "professor_name": professor_name,
        }
