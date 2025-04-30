"""
Database models for ArtificialU.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship

from artificial_u.config.defaults import DEFAULT_COURSE_WEEKS, DEFAULT_LECTURES_PER_WEEK
from artificial_u.models.core import Lecture


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
    image_url = Column(String, nullable=True)

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
    lectures_per_week = Column(
        Integer, nullable=True, default=DEFAULT_LECTURES_PER_WEEK
    )
    total_weeks = Column(Integer, nullable=True, default=DEFAULT_COURSE_WEEKS)
    syllabus = Column(Text, nullable=True)

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
    )
