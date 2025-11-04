"""
Lecture repository for database operations.
"""

from typing import Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from artificial_u.models.core import Lecture
from artificial_u.models.database import CourseModel, LectureModel
from artificial_u.models.repositories.base import BaseRepository


class LectureRepository(BaseRepository):
    """Repository for Lecture operations."""

    def create(self, lecture: Lecture) -> Lecture:
        """Create a new lecture."""
        with self.get_session() as session:
            # If revision is not provided, calculate the next revision for the topic.
            if lecture.revision is None:
                max_revision = (
                    session.query(func.max(LectureModel.revision))
                    .filter(LectureModel.topic_id == lecture.topic_id)
                    .scalar()
                )
                lecture.revision = (max_revision or 0) + 1

            db_lecture = LectureModel(
                revision=lecture.revision,
                content=lecture.content,
                summary=lecture.summary,
                title=lecture.title,
                audio_url=lecture.audio_url,
                transcript_url=lecture.transcript_url,
                course_id=lecture.course_id,
                topic_id=lecture.topic_id,
                created_by=lecture.created_by,
                created_with=lecture.created_with,
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
            db_lecture = (
                session.query(LectureModel)
                .options(joinedload(LectureModel.student))
                .filter_by(id=lecture_id)
                .first()
            )
            if not db_lecture:
                return None

            # Build student dict if present
            student_dict = None
            if db_lecture.student:
                student_dict = {
                    "id": db_lecture.student.id,
                    "name": db_lecture.student.name,
                    "email": db_lecture.student.email,
                }

            return Lecture(
                id=db_lecture.id,
                revision=db_lecture.revision,
                content=db_lecture.content,
                summary=db_lecture.summary,
                title=db_lecture.title,
                audio_url=db_lecture.audio_url,
                transcript_url=db_lecture.transcript_url,
                course_id=db_lecture.course_id,
                topic_id=db_lecture.topic_id,
                created_by=db_lecture.created_by,
                created_with=db_lecture.created_with,
                created_at=db_lecture.created_at,
                updated_at=db_lecture.updated_at,
                student=student_dict,
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
        List all lectures for a specific course, returning only the latest revision for each topic.

        Args:
            course_id: ID of the course to get lectures for

        Returns:
            List[Lecture]: List of lectures for the specified course (latest revision per topic)
        """
        with self.get_session() as session:
            # Subquery to get the latest revision for each topic
            latest_revisions = (
                session.query(
                    LectureModel.topic_id, func.max(LectureModel.revision).label("max_revision")
                )
                .filter(LectureModel.course_id == course_id)
                .group_by(LectureModel.topic_id)
                .subquery()
            )

            # Query to get lectures with the latest revision
            query = session.query(LectureModel).join(
                latest_revisions,
                (LectureModel.topic_id == latest_revisions.c.topic_id)
                & (LectureModel.revision == latest_revisions.c.max_revision),
            )
            # Eager-load student relationship for attribution metadata
            query = query.options(joinedload(LectureModel.student))

            db_lectures = query.all()

            results: List[Lecture] = []
            for lecture in db_lectures:
                student_dict = None
                if lecture.student:
                    student_dict = {
                        "id": lecture.student.id,
                        "name": lecture.student.name,
                        "email": lecture.student.email,
                    }

                results.append(
                    Lecture(
                        id=lecture.id,
                        revision=lecture.revision,
                        content=lecture.content,
                        summary=lecture.summary,
                        title=lecture.title,
                        audio_url=lecture.audio_url,
                        transcript_url=lecture.transcript_url,
                        course_id=lecture.course_id,
                        topic_id=lecture.topic_id,
                        created_by=lecture.created_by,
                        created_with=lecture.created_with,
                        created_at=lecture.created_at,
                        updated_at=lecture.updated_at,
                        student=student_dict,
                    )
                )

            return results

    def list_by_topic(self, topic_id: int) -> List[Lecture]:
        """
        List all lectures for a specific topic, returning only the latest revision.

        Args:
            topic_id: ID of the topic to get lectures for

        Returns:
            List[Lecture]: List containing the latest revision lecture for the specified topic
        """
        with self.get_session() as session:
            # Get the latest revision for this topic
            latest_revision = (
                session.query(func.max(LectureModel.revision))
                .filter(LectureModel.topic_id == topic_id)
                .scalar()
            )

            if latest_revision is None:
                return []

            # Get the lecture with the latest revision
            db_lecture = (
                session.query(LectureModel)
                .options(joinedload(LectureModel.student))
                .filter(LectureModel.topic_id == topic_id, LectureModel.revision == latest_revision)
                .first()
            )

            if not db_lecture:
                return []

            # Build student dict if present
            student_dict = None
            if db_lecture.student:
                student_dict = {
                    "id": db_lecture.student.id,
                    "name": db_lecture.student.name,
                    "email": db_lecture.student.email,
                }

            return [
                Lecture(
                    id=db_lecture.id,
                    revision=db_lecture.revision,
                    content=db_lecture.content,
                    summary=db_lecture.summary,
                    title=db_lecture.title,
                    audio_url=db_lecture.audio_url,
                    transcript_url=db_lecture.transcript_url,
                    course_id=db_lecture.course_id,
                    topic_id=db_lecture.topic_id,
                    created_by=db_lecture.created_by,
                    created_with=db_lecture.created_with,
                    created_at=db_lecture.created_at,
                    updated_at=db_lecture.updated_at,
                    student=student_dict,
                )
            ]

    def count(
        self,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """
        Count lectures with filtering, counting only the latest revision for each topic.

        Args:
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            topic_id: Filter by topic ID
            search_query: Search query for content/summary/title

        Returns:
            int: Total count of latest revision lectures matching the filters
        """
        with self.get_session() as session:
            # Subquery to get the latest revision for each topic
            latest_revisions = (
                session.query(
                    LectureModel.topic_id, func.max(LectureModel.revision).label("max_revision")
                )
                .group_by(LectureModel.topic_id)
                .subquery()
            )

            # Query to count lectures with the latest revision
            query = session.query(LectureModel).join(
                latest_revisions,
                (LectureModel.topic_id == latest_revisions.c.topic_id)
                & (LectureModel.revision == latest_revisions.c.max_revision),
            )

            # Apply filters
            if course_id is not None:
                query = query.filter(LectureModel.course_id == course_id)

            if professor_id is not None:
                # Join with CourseModel to filter by professor_id
                query = query.join(CourseModel).filter(CourseModel.professor_id == professor_id)

            if topic_id is not None:
                query = query.filter(LectureModel.topic_id == topic_id)

            if search_query:
                # Search in content, summary, and title
                query = query.filter(
                    or_(
                        LectureModel.content.ilike(f"%{search_query}%"),
                        LectureModel.summary.ilike(f"%{search_query}%"),
                        LectureModel.title.ilike(f"%{search_query}%"),
                    )
                )

            return query.count()

    def list(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List[Lecture]:
        """
        List lectures with filtering and pagination,
        returning only the latest revision for each topic.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            topic_id: Filter by topic ID
            search_query: Search query for content/summary/title

        Returns:
            List[Lecture]: List of lectures (latest revision per topic)
        """
        with self.get_session() as session:
            # Subquery to get the latest revision for each topic
            latest_revisions = (
                session.query(
                    LectureModel.topic_id, func.max(LectureModel.revision).label("max_revision")
                )
                .group_by(LectureModel.topic_id)
                .subquery()
            )

            # Query to get lectures with the latest revision
            query = session.query(LectureModel).join(
                latest_revisions,
                (LectureModel.topic_id == latest_revisions.c.topic_id)
                & (LectureModel.revision == latest_revisions.c.max_revision),
            )

            # Apply filters
            if course_id is not None:
                query = query.filter(LectureModel.course_id == course_id)

            if professor_id is not None:
                # Join with CourseModel to filter by professor_id
                query = query.join(CourseModel).filter(CourseModel.professor_id == professor_id)

            if topic_id is not None:
                query = query.filter(LectureModel.topic_id == topic_id)

            if search_query:
                # Search in content, summary, and title
                query = query.filter(
                    or_(
                        LectureModel.content.ilike(f"%{search_query}%"),
                        LectureModel.summary.ilike(f"%{search_query}%"),
                        LectureModel.title.ilike(f"%{search_query}%"),
                    )
                )

            # Apply pagination
            offset = (page - 1) * size
            query = query.order_by(LectureModel.id).offset(offset).limit(size)

            # Execute query
            db_lectures = query.all()

            results: List[Lecture] = []
            for lecture in db_lectures:
                student_dict = None
                if lecture.student:
                    student_dict = {
                        "id": lecture.student.id,
                        "name": lecture.student.name,
                        "email": lecture.student.email,
                    }

                results.append(
                    Lecture(
                        id=lecture.id,
                        revision=lecture.revision,
                        content=lecture.content,
                        summary=lecture.summary,
                        title=lecture.title,
                        audio_url=lecture.audio_url,
                        transcript_url=lecture.transcript_url,
                        course_id=lecture.course_id,
                        topic_id=lecture.topic_id,
                        created_by=lecture.created_by,
                        created_with=lecture.created_with,
                        created_at=lecture.created_at,
                        updated_at=lecture.updated_at,
                        student=student_dict,
                    )
                )

            return results

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
            db_lecture.title = lecture.title
            db_lecture.audio_url = lecture.audio_url
            db_lecture.transcript_url = lecture.transcript_url
            db_lecture.course_id = lecture.course_id
            db_lecture.topic_id = lecture.topic_id
            db_lecture.created_by = lecture.created_by
            db_lecture.created_with = lecture.created_with

            session.add(db_lecture)
            session.commit()

            return lecture

    def update_fields(self, lecture_id: int, update_data: Dict[str, any]) -> Lecture:
        """
        Partially update fields on an existing lecture, avoiding lost updates.

        Only the fields provided in update_data will be modified.

        Args:
            lecture_id: ID of the lecture to update
            update_data: Mapping of column names to new values

        Returns:
            Lecture: The updated lecture model

        Raises:
            ValueError: If the lecture does not exist
        """
        with self.get_session() as session:
            db_lecture = session.get(LectureModel, lecture_id)
            if not db_lecture:
                raise ValueError(f"Lecture with ID {lecture_id} not found")

            # Apply only provided fields
            allowed_fields = {
                "content",
                "revision",
                "summary",
                "title",
                "audio_url",
                "transcript_url",
                "course_id",
                "topic_id",
                "created_by",
                "created_with",
            }
            for key, value in update_data.items():
                if key in allowed_fields:
                    setattr(db_lecture, key, value)

            session.add(db_lecture)
            session.commit()
            session.refresh(db_lecture)

            return Lecture(
                id=db_lecture.id,
                revision=db_lecture.revision,
                content=db_lecture.content,
                summary=db_lecture.summary,
                title=db_lecture.title,
                audio_url=db_lecture.audio_url,
                transcript_url=db_lecture.transcript_url,
                course_id=db_lecture.course_id,
                topic_id=db_lecture.topic_id,
                created_by=db_lecture.created_by,
                created_with=db_lecture.created_with,
                created_at=db_lecture.created_at,
                updated_at=db_lecture.updated_at,
            )

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
