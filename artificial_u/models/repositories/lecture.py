"""
Lecture repository for database operations.
"""

from typing import List, Optional

from sqlalchemy import or_

from artificial_u.models.core import Lecture
from artificial_u.models.database import CourseModel, LectureModel
from artificial_u.models.repositories.base import BaseRepository


class LectureRepository(BaseRepository):
    """Repository for Lecture operations."""

    def create(self, lecture: Lecture) -> Lecture:
        """Create a new lecture."""
        with self.get_session() as session:
            db_lecture = LectureModel(
                revision=lecture.revision,
                content=lecture.content,
                summary=lecture.summary,
                audio_url=lecture.audio_url,
                transcript_url=lecture.transcript_url,
                course_id=lecture.course_id,
                topic_id=lecture.topic_id,
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
            db_lecture = session.query(LectureModel).filter_by(id=lecture_id).first()
            if not db_lecture:
                return None

            return Lecture(
                id=db_lecture.id,
                revision=db_lecture.revision,
                content=db_lecture.content,
                summary=db_lecture.summary,
                audio_url=db_lecture.audio_url,
                transcript_url=db_lecture.transcript_url,
                course_id=db_lecture.course_id,
                topic_id=db_lecture.topic_id,
            )

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

    def get_transcript_url(self, lecture_id: int) -> Optional[str]:
        """Get the transcript URL for a lecture."""
        with self.get_session() as session:
            lecture = session.get(LectureModel, lecture_id)
            return lecture.transcript_url if lecture else None

    def list_by_course(self, course_id: int) -> List[Lecture]:
        """
        List all lectures for a specific course.

        Args:
            course_id: ID of the course to get lectures for

        Returns:
            List[Lecture]: List of lectures for the specified course
        """
        with self.get_session() as session:
            db_lectures = session.query(LectureModel).filter_by(course_id=course_id).all()

            return [
                Lecture(
                    id=lecture.id,
                    revision=lecture.revision,
                    content=lecture.content,
                    summary=lecture.summary,
                    audio_url=lecture.audio_url,
                    transcript_url=lecture.transcript_url,
                    course_id=lecture.course_id,
                    topic_id=lecture.topic_id,
                )
                for lecture in db_lectures
            ]

    def list_by_topic(self, topic_id: int) -> List[Lecture]:
        """
        List all lectures for a specific topic.

        Args:
            topic_id: ID of the topic to get lectures for

        Returns:
            List[Lecture]: List of lectures for the specified topic
        """
        with self.get_session() as session:
            db_lectures = session.query(LectureModel).filter_by(topic_id=topic_id).all()

            return [
                Lecture(
                    id=lecture.id,
                    revision=lecture.revision,
                    content=lecture.content,
                    summary=lecture.summary,
                    audio_url=lecture.audio_url,
                    transcript_url=lecture.transcript_url,
                    course_id=lecture.course_id,
                    topic_id=lecture.topic_id,
                )
                for lecture in db_lectures
            ]

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
            search_query: Search query for content/summary

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
                query = query.join(CourseModel).filter(CourseModel.professor_id == professor_id)

            if search_query:
                # Search in content and summary
                query = query.filter(
                    or_(
                        LectureModel.content.ilike(f"%{search_query}%"),
                        LectureModel.summary.ilike(f"%{search_query}%"),
                    )
                )

            # Apply pagination
            offset = (page - 1) * size
            query = query.order_by(LectureModel.id).offset(offset).limit(size)

            # Execute query
            db_lectures = query.all()

            return [
                Lecture(
                    id=lecture.id,
                    revision=lecture.revision,
                    content=lecture.content,
                    summary=lecture.summary,
                    audio_url=lecture.audio_url,
                    transcript_url=lecture.transcript_url,
                    course_id=lecture.course_id,
                    topic_id=lecture.topic_id,
                )
                for lecture in db_lectures
            ]

    def update(self, lecture: Lecture) -> Lecture:
        """
        Update an existing lecture.

        Args:
            lecture: Lecture object with updated fields

        Returns:
            Lecture: Updated lecture
        """
        with self.get_session() as session:
            db_lecture = session.get(LectureModel, lecture.id)
            if not db_lecture:
                raise ValueError(f"Lecture with ID {lecture.id} not found")

            # Update fields
            db_lecture.content = lecture.content
            db_lecture.revision = lecture.revision
            db_lecture.summary = lecture.summary
            db_lecture.audio_url = lecture.audio_url
            db_lecture.transcript_url = lecture.transcript_url
            db_lecture.course_id = lecture.course_id
            db_lecture.topic_id = lecture.topic_id

            session.add(db_lecture)
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

    def delete_by_course(self, course_id: int) -> int:
        """
        Delete all lectures for a specific course.

        Args:
            course_id: ID of the course whose lectures should be deleted

        Returns:
            Number of lectures deleted
        """
        with self.get_session() as session:
            result = session.query(LectureModel).filter_by(course_id=course_id).delete()
            session.commit()
            return result

    def delete_by_topic(self, topic_id: int) -> int:
        """
        Delete all lectures for a specific topic.

        Args:
            topic_id: ID of the topic whose lectures should be deleted

        Returns:
            Number of lectures deleted
        """
        with self.get_session() as session:
            result = session.query(LectureModel).filter_by(topic_id=topic_id).delete()
            session.commit()
            return result
