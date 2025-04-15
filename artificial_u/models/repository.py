"""
Backward compatibility module for transitioning from Repository to RepositoryFactory.

This module provides a Repository class that emulates the old Repository class
but uses the new repository architecture under the hood. This allows for a
gradual transition to the new repository architecture.
"""

import logging
import os
from typing import List, Optional

from artificial_u.models.core import Course, Department, Lecture, Professor, Voice
from artificial_u.models.repositories import RepositoryFactory


class Repository:
    """
    Legacy Repository interface that uses the new RepositoryFactory internally.

    This class is provided for backward compatibility with code that uses
    the old Repository class. It delegates all operations to the appropriate
    repository classes in the new architecture.

    New code should use RepositoryFactory directly instead of this class.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the repository.

        Args:
            db_url: SQLAlchemy database URL for PostgreSQL connection.
                   If not provided, uses DATABASE_URL environment variable.
        """
        self.logger = logging.getLogger(__name__)
        self.db_url = db_url or os.environ.get("DATABASE_URL")

        if not self.db_url:
            raise ValueError(
                "Database URL not provided. Set DATABASE_URL environment variable."
            )

        self.factory = RepositoryFactory(db_url=self.db_url)
        self.logger.info(f"Using database URL: {self.db_url}")

        # Create tables if they don't exist
        self.factory.create_tables()

    # Department operations
    def create_department(self, department: Department) -> Department:
        """Create a new department."""
        return self.factory.department.create(department)

    def get_department(self, department_id: int) -> Optional[Department]:
        """Get a department by ID."""
        return self.factory.department.get(department_id)

    def get_department_by_code(self, code: str) -> Optional[Department]:
        """Get a department by code."""
        return self.factory.department.get_by_code(code)

    def list_departments(self, faculty: Optional[str] = None) -> List[Department]:
        """List departments with optional faculty filter."""
        return self.factory.department.list(faculty=faculty)

    def update_department(self, department: Department) -> Department:
        """Update a department."""
        return self.factory.department.update(department)

    def delete_department(self, department_id: int) -> bool:
        """Delete a department by ID."""
        return self.factory.department.delete(department_id)

    # Professor operations
    def create_professor(self, professor: Professor) -> Professor:
        """Create a new professor."""
        return self.factory.professor.create(professor)

    def get_professor(self, professor_id: int) -> Optional[Professor]:
        """Get a professor by ID."""
        return self.factory.professor.get(professor_id)

    def list_professors(self) -> List[Professor]:
        """List all professors."""
        return self.factory.professor.list()

    def update_professor(self, professor: Professor) -> Professor:
        """Update an existing professor."""
        return self.factory.professor.update(professor)

    def update_professor_field(
        self, professor_id: int, **fields
    ) -> Optional[Professor]:
        """Update specific fields of a professor."""
        return self.factory.professor.update_field(professor_id, **fields)

    def delete_professor(self, professor_id: int) -> bool:
        """Delete a professor by ID."""
        return self.factory.professor.delete(professor_id)

    # Course operations
    def create_course(self, course: Course) -> Course:
        """Create a new course."""
        return self.factory.course.create(course)

    def get_course(self, course_id: int) -> Optional[Course]:
        """Get a course by ID."""
        return self.factory.course.get(course_id)

    def get_course_by_code(self, code: str) -> Optional[Course]:
        """Get a course by course code."""
        return self.factory.course.get_by_code(code)

    def list_courses(self, department: Optional[str] = None) -> List[Course]:
        """List courses with optional department filter."""
        # The new repository uses department_id instead of department
        return self.factory.course.list()

    # Lecture operations
    def create_lecture(self, lecture: Lecture) -> Lecture:
        """Create a new lecture."""
        return self.factory.lecture.create(lecture)

    def get_lecture(self, lecture_id: int) -> Optional[Lecture]:
        """Get a lecture by ID."""
        return self.factory.lecture.get(lecture_id)

    def get_lecture_by_course_week_order(
        self, course_id: int, week_number: int, order_in_week: int
    ) -> Optional[Lecture]:
        """Get a lecture by course ID, week number, and order in week."""
        return self.factory.lecture.get_by_course_week_order(
            course_id, week_number, order_in_week
        )

    def get_lecture_content(self, lecture_id: int) -> Optional[str]:
        """Get the content of a lecture by ID."""
        return self.factory.lecture.get_content(lecture_id)

    def get_lecture_audio_url(self, lecture_id: int) -> Optional[str]:
        """Get the audio URL for a lecture."""
        return self.factory.lecture.get_audio_url(lecture_id)

    def list_lectures(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> List[Lecture]:
        """List lectures with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            search_query: Search query for title/description
        """
        return self.factory.lecture.list(
            page=page,
            size=size,
            course_id=course_id,
            professor_id=professor_id,
            search_query=search_query,
        )

    def count_lectures(
        self,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """Count lectures with filtering."""
        return self.factory.lecture.count(
            course_id=course_id,
            professor_id=professor_id,
            search_query=search_query,
        )

    def update_lecture(self, lecture: Lecture) -> Lecture:
        """Update an existing lecture."""
        return self.factory.lecture.update(lecture)

    def delete_lecture(self, lecture_id: int) -> bool:
        """Delete a lecture."""
        return self.factory.lecture.delete(lecture_id)

    def _build_lecture_summary(self, lecture, courses=None, professors=None):
        """Build a summary representation of a lecture."""
        if hasattr(lecture, "id") and lecture.id:
            return self.factory.lecture.build_lecture_summary(lecture)

        # Legacy handling for dictionaries and other object types
        from datetime import datetime

        # Extract fields from lecture object or dict
        lecture_id = lecture.id if hasattr(lecture, "id") else lecture.get("id")
        title = lecture.title if hasattr(lecture, "title") else lecture.get("title")
        course_id = (
            lecture.course_id
            if hasattr(lecture, "course_id")
            else lecture.get("course_id")
        )
        week_number = (
            lecture.week_number
            if hasattr(lecture, "week_number")
            else lecture.get("week_number")
        )
        order_in_week = (
            lecture.order_in_week
            if hasattr(lecture, "order_in_week")
            else lecture.get("order_in_week")
        )
        description = (
            lecture.description
            if hasattr(lecture, "description")
            else lecture.get("description")
        )
        audio_url = (
            lecture.audio_url
            if hasattr(lecture, "audio_url")
            else lecture.get("audio_url")
        )

        # Get course and professor information
        course_title = "Unknown Course"
        professor_id = None

        if course_id:
            course = self.get_course(course_id)
            if course:
                course_title = course.title
                professor_id = course.professor_id

        return {
            "id": lecture_id,
            "title": title,
            "course_id": course_id,
            "course_title": course_title,
            "professor_id": professor_id,
            "week_number": week_number,
            "order_in_week": order_in_week,
            "description": description,
            "created_at": getattr(lecture, "created_at", datetime.now()),
            "has_audio": bool(audio_url),
        }

    def _build_lecture_detail(self, lecture, courses=None, professors=None):
        """Build a detailed representation of a lecture."""
        if hasattr(lecture, "id") and lecture.id:
            return self.factory.lecture.build_lecture_detail(lecture)

        # Legacy handling
        # Get the summary as the base
        summary = self._build_lecture_summary(lecture, courses, professors)

        # Extract additional fields
        content = (
            lecture.content if hasattr(lecture, "content") else lecture.get("content")
        )
        audio_url = (
            lecture.audio_url
            if hasattr(lecture, "audio_url")
            else lecture.get("audio_url")
        )

        # Get professor information
        professor_name = "Unknown Professor"
        professor_id = summary.get("professor_id")

        if professor_id:
            professor = self.get_professor(professor_id)
            if professor:
                professor_name = professor.name

        # Build the detailed response
        return {
            **summary,
            "content": content,
            "sections": None,  # For a future implementation with section breakdown
            "audio_url": audio_url,
            "professor_name": professor_name,
        }

    # Voice operations
    def create_voice(self, voice: Voice) -> Voice:
        """Create a new voice record."""
        return self.factory.voice.create(voice)

    def get_voice(self, voice_id: int) -> Optional[Voice]:
        """Get a voice by ID."""
        return self.factory.voice.get(voice_id)

    def get_voice_by_elevenlabs_id(self, elevenlabs_id: str) -> Optional[Voice]:
        """Get a voice by ElevenLabs voice ID."""
        return self.factory.voice.get_by_elevenlabs_id(elevenlabs_id)

    def list_voices(
        self,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        age: Optional[str] = None,
        language: Optional[str] = None,
        use_case: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Voice]:
        """List voices with optional filters."""
        return self.factory.voice.list(
            gender=gender,
            accent=accent,
            age=age,
            language=language,
            use_case=use_case,
            category=category,
            limit=limit,
            offset=offset,
        )

    def update_voice(self, voice: Voice) -> Voice:
        """Update an existing voice."""
        return self.factory.voice.update(voice)

    def upsert_voice(self, voice: Voice) -> Voice:
        """Create or update a voice based on ElevenLabs voice_id."""
        return self.factory.voice.upsert(voice)
