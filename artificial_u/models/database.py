"""
Database models and repository for ArtificialU.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from sqlalchemy import or_, func, case, desc

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship, Session, DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError

from artificial_u.models.core import Professor, Course, Lecture, Department, Voice


# SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# SQLAlchemy Models
class DepartmentModel(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    code = Column(String, nullable=False, unique=True)
    faculty = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    professors = relationship("ProfessorModel", back_populates="department")
    courses = relationship("CourseModel", back_populates="department")


class VoiceModel(Base):
    __tablename__ = "voices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    el_voice_id = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    accent = Column(String(100), nullable=True)
    gender = Column(String(50), nullable=True)
    age = Column(String(50), nullable=True)
    descriptive = Column(String(100), nullable=True)
    use_case = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    language = Column(String(10), nullable=True)
    locale = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    preview_url = Column(Text, nullable=True)
    verified_languages = Column(JSON, nullable=True)
    popularity_score = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.now)

    professor = relationship("ProfessorModel", back_populates="voice")

    # Create indexes
    __table_args__ = (
        Index("idx_voices_language", "language"),
        # We'll create the text search index manually after migrations
        # to avoid Alembic issues with REGCONFIG type
    )


class ProfessorModel(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    title = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    specialization = Column(String, nullable=True)
    background = Column(Text, nullable=True)
    personality = Column(Text, nullable=True)
    teaching_style = Column(Text, nullable=True)
    gender = Column(String, nullable=True)
    accent = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    age = Column(Integer, nullable=True)
    voice_id = Column(Integer, ForeignKey("voices.id"), nullable=True)
    image_path = Column(String, nullable=True)

    department = relationship("DepartmentModel", back_populates="professors")
    courses = relationship("CourseModel", back_populates="professor")
    voice = relationship("VoiceModel", back_populates="professor")


class CourseModel(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    level = Column(String, nullable=True)
    credits = Column(Integer, nullable=True, default=3)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=True)
    description = Column(Text, nullable=True)
    lectures_per_week = Column(Integer, nullable=True, default=2)
    total_weeks = Column(Integer, nullable=True, default=14)
    syllabus = Column(Text, nullable=True)
    generated_at = Column(DateTime, nullable=False, default=datetime.now)

    department = relationship("DepartmentModel", back_populates="courses")
    professor = relationship("ProfessorModel", back_populates="courses")
    lectures = relationship("LectureModel", back_populates="course")


class LectureModel(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    order_in_week = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    audio_url = Column(String, nullable=True)
    generated_at = Column(DateTime, nullable=False, default=datetime.now)

    course = relationship("CourseModel", back_populates="lectures")


# Helper functions for converting between models and entities
def lecture_model_to_entity(lecture_model: LectureModel) -> Optional[Lecture]:
    """Convert a LectureModel to a Lecture entity."""
    if not lecture_model:
        return None

    return Lecture(
        id=lecture_model.id,
        title=lecture_model.title,
        course_id=lecture_model.course_id,
        week_number=lecture_model.week_number,
        order_in_week=lecture_model.order_in_week,
        description=lecture_model.description,
        content=lecture_model.content,
        audio_url=lecture_model.audio_url,
        generated_at=lecture_model.generated_at,
    )


class Repository:
    """
    Repository for database operations.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the repository.

        Args:
            db_url: SQLAlchemy database URL for PostgreSQL connection.
                   If not provided, uses DATABASE_URL environment variable.
        """
        # Setup logging
        self.logger = logging.getLogger(__name__)

        self.db_url = db_url or os.environ.get("DATABASE_URL")

        if not self.db_url:
            raise ValueError(
                "PostgreSQL connection URL not provided. Set DATABASE_URL environment variable."
            )

        self.engine = create_engine(self.db_url)
        self.logger.info(f"Using database URL: {self.db_url}")

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

    def _build_lecture_summary(self, lecture, courses=None, professors=None):
        """
        Build a summary representation of a lecture.

        Args:
            lecture: Lecture object or dict
            courses: Optional list of courses for lookup
            professors: Optional list of professors for lookup

        Returns:
            dict: Summary representation of the lecture
        """
        # Handle both Lecture objects and dictionaries
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

        # Get course information if not provided
        course_title = "Unknown Course"
        professor_id = None

        if courses:
            course = next((c for c in courses if c.id == course_id), None)
            if course:
                course_title = course.title
                professor_id = course.professor_id
        else:
            with Session(self.engine) as session:
                course = session.query(CourseModel).filter_by(id=course_id).first()
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
        """
        Build a detailed representation of a lecture.

        Args:
            lecture: Lecture object or dict
            courses: Optional list of courses for lookup
            professors: Optional list of professors for lookup

        Returns:
            dict: Detailed representation of the lecture
        """
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
        course_id = summary.get("course_id")
        professor_id = summary.get("professor_id")

        if professors and professor_id:
            professor = next((p for p in professors if p.id == professor_id), None)
            if professor:
                professor_name = professor.name
        elif professor_id:
            with Session(self.engine) as session:
                professor = (
                    session.query(ProfessorModel).filter_by(id=professor_id).first()
                )
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
        with Session(self.engine) as session:
            db_voice = VoiceModel(
                el_voice_id=voice.el_voice_id,
                name=voice.name,
                accent=voice.accent,
                gender=voice.gender,
                age=voice.age,
                descriptive=voice.descriptive,
                use_case=voice.use_case,
                category=voice.category,
                language=voice.language,
                locale=voice.locale,
                description=voice.description,
                preview_url=voice.preview_url,
                verified_languages=voice.verified_languages,
                popularity_score=voice.popularity_score,
                last_updated=datetime.now(),
            )

            session.add(db_voice)
            session.commit()
            session.refresh(db_voice)

            voice.id = db_voice.id
            return voice

    def get_voice(self, voice_id: int) -> Optional[Voice]:
        """Get a voice by ID."""
        with Session(self.engine) as session:
            db_voice = session.query(VoiceModel).filter_by(id=voice_id).first()

            if not db_voice:
                return None

            return Voice(
                id=db_voice.id,
                el_voice_id=db_voice.el_voice_id,
                name=db_voice.name,
                accent=db_voice.accent,
                gender=db_voice.gender,
                age=db_voice.age,
                descriptive=db_voice.descriptive,
                use_case=db_voice.use_case,
                category=db_voice.category,
                language=db_voice.language,
                locale=db_voice.locale,
                description=db_voice.description,
                preview_url=db_voice.preview_url,
                verified_languages=db_voice.verified_languages or {},
                popularity_score=db_voice.popularity_score,
                last_updated=db_voice.last_updated,
            )

    def get_voice_by_elevenlabs_id(self, elevenlabs_id: str) -> Optional[Voice]:
        """Get a voice by ElevenLabs voice ID."""
        with Session(self.engine) as session:
            db_voice = (
                session.query(VoiceModel).filter_by(el_voice_id=elevenlabs_id).first()
            )

            if not db_voice:
                return None

            return Voice(
                id=db_voice.id,
                el_voice_id=db_voice.el_voice_id,
                name=db_voice.name,
                accent=db_voice.accent,
                gender=db_voice.gender,
                age=db_voice.age,
                descriptive=db_voice.descriptive,
                use_case=db_voice.use_case,
                category=db_voice.category,
                language=db_voice.language,
                locale=db_voice.locale,
                description=db_voice.description,
                preview_url=db_voice.preview_url,
                verified_languages=db_voice.verified_languages or {},
                popularity_score=db_voice.popularity_score,
                last_updated=db_voice.last_updated,
            )

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
        with Session(self.engine) as session:
            query = session.query(VoiceModel)

            # Apply filters
            if gender:
                query = query.filter(VoiceModel.gender == gender)
            if accent:
                query = query.filter(VoiceModel.accent == accent)
            if age:
                query = query.filter(VoiceModel.age == age)
            if language:
                query = query.filter(VoiceModel.language == language)
            if use_case:
                query = query.filter(VoiceModel.use_case == use_case)
            if category:
                query = query.filter(VoiceModel.category == category)

            # Apply pagination
            voices = (
                query.order_by(VoiceModel.popularity_score.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )

            return [
                Voice(
                    id=v.id,
                    el_voice_id=v.el_voice_id,
                    name=v.name,
                    accent=v.accent,
                    gender=v.gender,
                    age=v.age,
                    descriptive=v.descriptive,
                    use_case=v.use_case,
                    category=v.category,
                    language=v.language,
                    locale=v.locale,
                    description=v.description,
                    preview_url=v.preview_url,
                    verified_languages=v.verified_languages or {},
                    popularity_score=v.popularity_score,
                    last_updated=v.last_updated,
                )
                for v in voices
            ]

    def update_voice(self, voice: Voice) -> Voice:
        """Update an existing voice."""
        with Session(self.engine) as session:
            db_voice = session.query(VoiceModel).filter_by(id=voice.id).first()

            if not db_voice:
                raise ValueError(f"Voice with ID {voice.id} not found")

            db_voice.el_voice_id = voice.el_voice_id
            db_voice.name = voice.name
            db_voice.accent = voice.accent
            db_voice.gender = voice.gender
            db_voice.age = voice.age
            db_voice.descriptive = voice.descriptive
            db_voice.use_case = voice.use_case
            db_voice.category = voice.category
            db_voice.language = voice.language
            db_voice.locale = voice.locale
            db_voice.description = voice.description
            db_voice.preview_url = voice.preview_url
            db_voice.verified_languages = voice.verified_languages
            db_voice.popularity_score = voice.popularity_score
            db_voice.last_updated = datetime.now()

            session.commit()
            return voice

    def upsert_voice(self, voice: Voice) -> Voice:
        """Create or update a voice based on ElevenLabs voice_id."""
        existing_voice = self.get_voice_by_elevenlabs_id(voice.el_voice_id)
        if existing_voice:
            voice.id = existing_voice.id
            return self.update_voice(voice)
        return self.create_voice(voice)

    # Professor operations
    def create_professor(self, professor: Professor) -> Professor:
        """Create a new professor."""
        with Session(self.engine) as session:
            db_professor = ProfessorModel(
                name=professor.name,
                title=professor.title,
                department_id=professor.department_id,
                specialization=professor.specialization,
                background=professor.background,
                personality=professor.personality,
                teaching_style=professor.teaching_style,
                gender=professor.gender,
                accent=professor.accent,
                description=professor.description,
                age=professor.age,
                image_path=professor.image_path,
                voice_id=professor.voice_id,
            )

            session.add(db_professor)
            session.commit()

            professor.id = db_professor.id
            return professor

    def get_professor(self, professor_id: int) -> Optional[Professor]:
        """Get a professor by ID."""
        with Session(self.engine) as session:
            db_professor = (
                session.query(ProfessorModel).filter_by(id=professor_id).first()
            )

            if not db_professor:
                return None

            return Professor(
                id=db_professor.id,
                name=db_professor.name,
                title=db_professor.title,
                department_id=db_professor.department_id,
                specialization=db_professor.specialization,
                background=db_professor.background,
                personality=db_professor.personality,
                teaching_style=db_professor.teaching_style,
                gender=db_professor.gender,
                accent=db_professor.accent,
                description=db_professor.description,
                age=db_professor.age,
                voice_id=db_professor.voice_id,
                image_path=db_professor.image_path,
            )

    def list_professors(self) -> List[Professor]:
        """List all professors."""
        with Session(self.engine) as session:
            db_professors = session.query(ProfessorModel).all()

            return [
                Professor(
                    id=p.id,
                    name=p.name,
                    title=p.title,
                    department_id=p.department_id,
                    specialization=p.specialization,
                    background=p.background,
                    personality=p.personality,
                    teaching_style=p.teaching_style,
                    gender=p.gender,
                    accent=p.accent,
                    description=p.description,
                    age=p.age,
                    voice_id=p.voice_id,
                    image_path=p.image_path,
                )
                for p in db_professors
            ]

    def update_professor(self, professor: Professor) -> Professor:
        """Update an existing professor."""
        with Session(self.engine) as session:
            db_professor = (
                session.query(ProfessorModel).filter_by(id=professor.id).first()
            )

            if not db_professor:
                raise ValueError(f"Professor with ID {professor.id} not found")

            # Update fields
            db_professor.name = professor.name
            db_professor.title = professor.title
            db_professor.department_id = professor.department_id
            db_professor.specialization = professor.specialization
            db_professor.background = professor.background
            db_professor.personality = professor.personality
            db_professor.teaching_style = professor.teaching_style
            db_professor.gender = professor.gender
            db_professor.accent = professor.accent
            db_professor.description = professor.description
            db_professor.age = professor.age
            db_professor.image_path = professor.image_path
            db_professor.voice_id = professor.voice_id
            session.commit()
            return professor

    def update_professor_field(
        self, professor_id: int, **fields
    ) -> Optional[Professor]:
        """
        Update specific fields of a professor.

        Args:
            professor_id: ID of the professor to update
            **fields: Field name-value pairs to update

        Returns:
            Updated professor or None if not found
        """
        with Session(self.engine) as session:
            db_professor = (
                session.query(ProfessorModel).filter_by(id=professor_id).first()
            )

            if not db_professor:
                return None

            # Update only the specified fields
            for field, value in fields.items():
                if hasattr(db_professor, field):
                    setattr(db_professor, field, value)

            session.commit()

            # Convert to core model and return
            return Professor(
                id=db_professor.id,
                name=db_professor.name,
                title=db_professor.title,
                department_id=db_professor.department_id,
                specialization=db_professor.specialization,
                background=db_professor.background,
                personality=db_professor.personality,
                teaching_style=db_professor.teaching_style,
                gender=db_professor.gender,
                accent=db_professor.accent,
                description=db_professor.description,
                age=db_professor.age,
                voice_id=db_professor.voice_id,
                image_path=db_professor.image_path,
            )

    def delete_professor(self, professor_id: int) -> bool:
        """
        Delete a professor by ID.

        Args:
            professor_id: ID of the professor to delete

        Returns:
            True if deleted successfully, False if professor not found
        """
        with Session(self.engine) as session:
            db_professor = (
                session.query(ProfessorModel).filter_by(id=professor_id).first()
            )

            if not db_professor:
                return False

            session.delete(db_professor)
            session.commit()
            return True

    # Course operations
    def create_course(self, course: Course) -> Course:
        """Create a new course."""
        with Session(self.engine) as session:
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
                syllabus=course.syllabus,
                generated_at=course.generated_at,
            )

            session.add(db_course)
            session.commit()

            course.id = db_course.id
            return course

    def get_course(self, course_id: int) -> Optional[Course]:
        """Get a course by ID."""
        with Session(self.engine) as session:
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
                syllabus=db_course.syllabus,
                generated_at=db_course.generated_at,
            )

    def get_course_by_code(self, code: str) -> Optional[Course]:
        """Get a course by course code."""
        with Session(self.engine) as session:
            db_course = session.query(CourseModel).filter_by(code=code).first()

            if not db_course:
                return None

            return Course(
                id=db_course.id,
                code=db_course.code,
                title=db_course.title,
                department=db_course.department,
                level=db_course.level,
                credits=db_course.credits,
                professor_id=db_course.professor_id,
                description=db_course.description,
                lectures_per_week=db_course.lectures_per_week,
                total_weeks=db_course.total_weeks,
                syllabus=db_course.syllabus,
                generated_at=db_course.generated_at,
            )

    def list_courses(self, department: Optional[str] = None) -> List[Course]:
        """List courses with optional department filter."""
        with Session(self.engine) as session:
            query = session.query(CourseModel)

            if department:
                query = query.filter_by(department=department)

            db_courses = query.all()

            return [
                Course(
                    id=c.id,
                    code=c.code,
                    title=c.title,
                    department=c.department,
                    level=c.level,
                    credits=c.credits,
                    professor_id=c.professor_id,
                    description=c.description,
                    lectures_per_week=c.lectures_per_week,
                    total_weeks=c.total_weeks,
                    syllabus=c.syllabus,
                    generated_at=c.generated_at,
                )
                for c in db_courses
            ]

    # Lecture operations
    def create_lecture(self, lecture: Lecture) -> Lecture:
        """Create a new lecture."""
        with Session(self.engine) as session:
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

            lecture.id = db_lecture.id
            return lecture

    def get_lecture(self, lecture_id: str) -> Optional[Lecture]:
        """
        Get a lecture by ID.

        Args:
            lecture_id: The ID of the lecture to retrieve

        Returns:
            Optional[Lecture]: The lecture if found, None otherwise
        """
        with Session(self.engine) as session:
            lecture = session.query(LectureModel).filter_by(id=lecture_id).first()
            return lecture_model_to_entity(lecture) if lecture else None

    def get_lecture_by_course_week_order(
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
        with Session(self.engine) as session:
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

    def get_lecture_content(self, lecture_id: str) -> Optional[str]:
        """
        Get the content of a lecture by ID.

        Args:
            lecture_id: The ID of the lecture to retrieve content for

        Returns:
            Optional[str]: The lecture content if found, None otherwise
        """
        with Session(self.engine) as session:
            lecture = session.query(LectureModel).filter_by(id=lecture_id).first()
            return lecture.content if lecture else None

    def get_lecture_audio_url(self, lecture_id: str) -> Optional[str]:
        """Get the audio URL for a lecture."""
        with Session(self.engine) as session:
            lecture = session.get(LectureModel, lecture_id)
            return lecture.audio_url if lecture else None

    def get_lectures(self, course_id: Optional[str] = None) -> List[Lecture]:
        """List all lectures for a course."""
        with Session(self.engine) as session:
            db_lectures = (
                session.query(LectureModel)
                .filter_by(course_id=course_id)
                .order_by(LectureModel.week_number, LectureModel.order_in_week)
                .all()
            )

            return [lecture_model_to_entity(l) for l in db_lectures]

    def list_lectures_by_course(self, course_id: int) -> List[Lecture]:
        """
        List all lectures for a specific course.

        Args:
            course_id: ID of the course to get lectures for

        Returns:
            List[Lecture]: List of lectures for the specified course
        """
        with Session(self.engine) as session:
            db_lectures = (
                session.query(LectureModel)
                .filter_by(course_id=course_id)
                .order_by(LectureModel.week_number, LectureModel.order_in_week)
                .all()
            )

            return [lecture_model_to_entity(l) for l in db_lectures]

    def list_lectures(
        self,
        page: int = 1,
        size: int = 10,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None,
    ) -> List[Lecture]:
        """
        List lectures with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            size: Items per page
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            tags: Filter by tags
            search_query: Search query for title/description

        Returns:
            List[Lecture]: List of lectures
        """
        with Session(self.engine) as session:
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

            return [lecture_model_to_entity(l) for l in db_lectures]

    def count_lectures(
        self,
        course_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        search_query: Optional[str] = None,
    ) -> int:
        """
        Count lectures with filtering.

        Args:
            course_id: Filter by course ID
            professor_id: Filter by professor ID
            tags: Filter by tags
            search_query: Search query for title/description

        Returns:
            int: Total count of matching lectures
        """
        with Session(self.engine) as session:
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

    def update_lecture(self, lecture: Lecture) -> Lecture:
        """
        Update an existing lecture.

        Args:
            lecture: Lecture object with updated fields

        Returns:
            Lecture: Updated lecture
        """
        with Session(self.engine) as session:
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

    def delete_lecture(self, lecture_id: int) -> bool:
        """
        Delete a lecture.

        Args:
            lecture_id: ID of the lecture to delete

        Returns:
            bool: True if lecture was deleted, False if not found
        """
        with Session(self.engine) as session:
            db_lecture = session.query(LectureModel).filter_by(id=lecture_id).first()

            if not db_lecture:
                return False

            session.delete(db_lecture)
            session.commit()

            return True

    # Department operations
    def create_department(self, department: Department) -> Department:
        """Create a new department."""
        with Session(self.engine) as session:
            db_department = DepartmentModel(
                name=department.name,
                code=department.code,
                faculty=department.faculty,
                description=department.description,
            )

            session.add(db_department)
            session.commit()
            session.refresh(db_department)

            department.id = db_department.id
            return department

    def get_department(self, department_id: int) -> Optional[Department]:
        """Get a department by ID."""
        with Session(self.engine) as session:
            db_department = (
                session.query(DepartmentModel).filter_by(id=department_id).first()
            )

            if not db_department:
                return None

            return Department(
                id=db_department.id,
                name=db_department.name,
                code=db_department.code,
                faculty=db_department.faculty,
                description=db_department.description,
            )

    def get_department_by_code(self, code: str) -> Optional[Department]:
        """Get a department by code."""
        with Session(self.engine) as session:
            db_department = session.query(DepartmentModel).filter_by(code=code).first()

            if not db_department:
                return None

            return Department(
                id=db_department.id,
                name=db_department.name,
                code=db_department.code,
                faculty=db_department.faculty,
                description=db_department.description,
            )

    def list_departments(self, faculty: Optional[str] = None) -> List[Department]:
        """List departments with optional faculty filter."""
        with Session(self.engine) as session:
            query = session.query(DepartmentModel)

            if faculty:
                query = query.filter_by(faculty=faculty)

            db_departments = query.all()

            return [
                Department(
                    id=d.id,
                    name=d.name,
                    code=d.code,
                    faculty=d.faculty,
                    description=d.description,
                )
                for d in db_departments
            ]

    def update_department(self, department: Department) -> Department:
        """Update a department."""
        with Session(self.engine) as session:
            db_department = (
                session.query(DepartmentModel).filter_by(id=department.id).first()
            )

            if not db_department:
                raise ValueError(f"Department with ID {department.id} not found")

            # Update fields
            db_department.name = department.name
            db_department.code = department.code
            db_department.faculty = department.faculty
            db_department.description = department.description

            session.commit()
            session.refresh(db_department)

            return department

    def delete_department(self, department_id: int) -> bool:
        """
        Delete a department by ID and set department_id to null for associated records.

        Args:
            department_id: ID of the department to delete

        Returns:
            True if deleted successfully, False if department not found
        """
        with Session(self.engine) as session:
            # Check if department exists
            db_department = (
                session.query(DepartmentModel).filter_by(id=department_id).first()
            )

            if not db_department:
                return False

            # Update associated professors to set department_id to null
            session.query(ProfessorModel).filter_by(department_id=department_id).update(
                {ProfessorModel.department_id: None}
            )

            # Update associated courses to set department_id to null
            session.query(CourseModel).filter_by(department_id=department_id).update(
                {CourseModel.department_id: None}
            )

            # Delete the department
            session.delete(db_department)
            session.commit()
            return True
