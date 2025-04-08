"""
Database models and repository for ArtificialU.
"""

import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship, Session, DeclarativeBase

from artificial_u.models.core import Professor, Course, Lecture, Department


# SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# SQLAlchemy Models
class DepartmentModel(Base):
    __tablename__ = "departments"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    code = Column(String, nullable=False, unique=True)
    faculty = Column(String, nullable=False)
    description = Column(Text, nullable=False)


class ProfessorModel(Base):
    __tablename__ = "professors"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    specialization = Column(String, nullable=False)
    background = Column(Text, nullable=False)
    personality = Column(Text, nullable=False)
    teaching_style = Column(Text, nullable=False)
    voice_settings = Column(Text, nullable=True)  # Stored as JSON
    image_path = Column(String, nullable=True)

    courses = relationship("CourseModel", back_populates="professor")


class CourseModel(Base):
    __tablename__ = "courses"

    id = Column(String, primary_key=True)
    code = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    level = Column(String, nullable=False)
    credits = Column(Integer, nullable=False, default=3)
    professor_id = Column(String, ForeignKey("professors.id"), nullable=False)
    description = Column(Text, nullable=False)
    lectures_per_week = Column(Integer, nullable=False, default=2)
    total_weeks = Column(Integer, nullable=False, default=14)
    syllabus = Column(Text, nullable=True)
    generated_at = Column(DateTime, nullable=False, default=datetime.now)

    professor = relationship("ProfessorModel", back_populates="courses")
    lectures = relationship("LectureModel", back_populates="course")


class LectureModel(Base):
    __tablename__ = "lectures"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    week_number = Column(Integer, nullable=False)
    order_in_week = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    audio_path = Column(String, nullable=True)
    generated_at = Column(DateTime, nullable=False, default=datetime.now)

    course = relationship("CourseModel", back_populates="lectures")


class Repository:
    """
    Repository for database operations.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the repository.

        Args:
            db_path: Path to SQLite database file. If not provided, will use DATABASE_PATH
                     environment variable or default to 'university.db'.
        """
        self.db_path = db_path or os.environ.get("DATABASE_PATH", "university.db")
        self.engine = create_engine(f"sqlite:///{self.db_path}")

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

    # Professor operations
    def create_professor(self, professor: Professor) -> Professor:
        """Create a new professor."""
        professor_id = str(uuid.uuid4())

        with Session(self.engine) as session:
            db_professor = ProfessorModel(
                id=professor_id,
                name=professor.name,
                title=professor.title,
                department=professor.department,
                specialization=professor.specialization,
                background=professor.background,
                personality=professor.personality,
                teaching_style=professor.teaching_style,
                voice_settings=json.dumps(professor.voice_settings),
                image_path=professor.image_path,
            )

            session.add(db_professor)
            session.commit()

            professor.id = professor_id
            return professor

    def get_professor(self, professor_id: str) -> Optional[Professor]:
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
                department=db_professor.department,
                specialization=db_professor.specialization,
                background=db_professor.background,
                personality=db_professor.personality,
                teaching_style=db_professor.teaching_style,
                voice_settings=(
                    json.loads(db_professor.voice_settings)
                    if db_professor.voice_settings
                    else {}
                ),
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
                    department=p.department,
                    specialization=p.specialization,
                    background=p.background,
                    personality=p.personality,
                    teaching_style=p.teaching_style,
                    voice_settings=(
                        json.loads(p.voice_settings) if p.voice_settings else {}
                    ),
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
            db_professor.department = professor.department
            db_professor.specialization = professor.specialization
            db_professor.background = professor.background
            db_professor.personality = professor.personality
            db_professor.teaching_style = professor.teaching_style
            db_professor.voice_settings = json.dumps(professor.voice_settings)
            db_professor.image_path = professor.image_path

            session.commit()
            return professor

    # Course operations
    def create_course(self, course: Course) -> Course:
        """Create a new course."""
        course_id = str(uuid.uuid4())

        with Session(self.engine) as session:
            db_course = CourseModel(
                id=course_id,
                code=course.code,
                title=course.title,
                department=course.department,
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

            course.id = course_id
            return course

    def get_course(self, course_id: str) -> Optional[Course]:
        """Get a course by ID."""
        with Session(self.engine) as session:
            db_course = session.query(CourseModel).filter_by(id=course_id).first()

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
        """List all courses, optionally filtered by department."""
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
        lecture_id = str(uuid.uuid4())

        with Session(self.engine) as session:
            db_lecture = LectureModel(
                id=lecture_id,
                title=lecture.title,
                course_id=lecture.course_id,
                week_number=lecture.week_number,
                order_in_week=lecture.order_in_week,
                description=lecture.description,
                content=lecture.content,
                audio_path=lecture.audio_path,
                generated_at=lecture.generated_at,
            )

            session.add(db_lecture)
            session.commit()

            lecture.id = lecture_id
            return lecture

    def get_lecture(self, lecture_id: str) -> Optional[Lecture]:
        """Get a lecture by ID."""
        with Session(self.engine) as session:
            db_lecture = session.query(LectureModel).filter_by(id=lecture_id).first()

            if not db_lecture:
                return None

            return Lecture(
                id=db_lecture.id,
                title=db_lecture.title,
                course_id=db_lecture.course_id,
                week_number=db_lecture.week_number,
                order_in_week=db_lecture.order_in_week,
                description=db_lecture.description,
                content=db_lecture.content,
                audio_path=db_lecture.audio_path,
                generated_at=db_lecture.generated_at,
            )

    def get_lecture_by_course_week_order(
        self, course_id: str, week_number: int, order_in_week: int
    ) -> Optional[Lecture]:
        """Get a lecture by course ID, week number, and order in week."""
        with Session(self.engine) as session:
            db_lecture = (
                session.query(LectureModel)
                .filter_by(
                    course_id=course_id,
                    week_number=week_number,
                    order_in_week=order_in_week,
                )
                .first()
            )

            if not db_lecture:
                return None

            return Lecture(
                id=db_lecture.id,
                title=db_lecture.title,
                course_id=db_lecture.course_id,
                week_number=db_lecture.week_number,
                order_in_week=db_lecture.order_in_week,
                description=db_lecture.description,
                content=db_lecture.content,
                audio_path=db_lecture.audio_path,
                generated_at=db_lecture.generated_at,
            )

    def update_lecture_audio(
        self, lecture_id: str, audio_path: str
    ) -> Optional[Lecture]:
        """Update the audio path for a lecture."""
        with Session(self.engine) as session:
            db_lecture = session.query(LectureModel).filter_by(id=lecture_id).first()

            if not db_lecture:
                return None

            db_lecture.audio_path = audio_path
            session.commit()

            return self.get_lecture(lecture_id)

    def list_lectures_by_course(self, course_id: str) -> List[Lecture]:
        """List all lectures for a course."""
        with Session(self.engine) as session:
            db_lectures = (
                session.query(LectureModel)
                .filter_by(course_id=course_id)
                .order_by(LectureModel.week_number, LectureModel.order_in_week)
                .all()
            )

            return [
                Lecture(
                    id=l.id,
                    title=l.title,
                    course_id=l.course_id,
                    week_number=l.week_number,
                    order_in_week=l.order_in_week,
                    description=l.description,
                    content=l.content,
                    audio_path=l.audio_path,
                    generated_at=l.generated_at,
                )
                for l in db_lectures
            ]
