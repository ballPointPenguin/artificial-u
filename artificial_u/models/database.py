"""
Database models for ArtificialU.
"""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


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
    age = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    descriptive = Column(String(100), nullable=True)
    gender = Column(String(50), nullable=True)
    language = Column(String(10), nullable=True)
    locale = Column(String(20), nullable=True)
    popularity_score = Column(Integer, nullable=True)
    preview_url = Column(Text, nullable=True)
    use_case = Column(String(100), nullable=True)
    verified_languages = Column(JSON, nullable=True)
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
    accent = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    background = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    gender = Column(String, nullable=True)
    personality = Column(Text, nullable=True)
    specialization = Column(String, nullable=True)
    teaching_style = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    voice_id = Column(Integer, ForeignKey("voices.id"), nullable=True)

    department = relationship("DepartmentModel", back_populates="professors")
    courses = relationship("CourseModel", back_populates="professor")
    voice = relationship("VoiceModel", back_populates="professor")


class CourseModel(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    credits = Column(Integer, nullable=True, default=3)
    description = Column(Text, nullable=True)
    lectures_per_week = Column(Integer, nullable=True, default=1)
    level = Column(String, nullable=True)
    total_weeks = Column(Integer, nullable=True, default=14)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=True)

    department = relationship("DepartmentModel", back_populates="courses")
    professor = relationship("ProfessorModel", back_populates="courses")
    lectures = relationship("LectureModel", back_populates="course")
    topics = relationship("TopicModel", back_populates="course")


class TopicModel(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    order = Column(Integer, nullable=False, default=1)
    week = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)

    course = relationship("CourseModel", back_populates="topics")
    lectures = relationship("LectureModel", back_populates="topic")


class LectureModel(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    revision = Column(Integer, nullable=False, default=1)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    audio_url = Column(String, nullable=True)
    transcript_url = Column(String, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)

    course = relationship("CourseModel", back_populates="lectures")
    topic = relationship("TopicModel", back_populates="lectures")
