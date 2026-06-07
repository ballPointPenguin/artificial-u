"""
Database models for ArtificialU.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship


# SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# SQLAlchemy Models
class CourseModel(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    lectures_per_week = Column(Integer, nullable=True, default=1)
    level = Column(String, nullable=True)
    total_weeks = Column(Integer, nullable=True, default=12)
    language = Column(String, nullable=True)
    status = Column(String, nullable=False, default="hidden")
    notes = Column(Text, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=True)
    # New attribution fields
    created_by = Column(Integer, ForeignKey("students.id"), nullable=True)
    created_with = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    image_created_with = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    department = relationship("DepartmentModel", back_populates="courses")
    professor = relationship("ProfessorModel", back_populates="courses")
    lectures = relationship("LectureModel", back_populates="course")
    topics = relationship("TopicModel", back_populates="course")
    student = relationship("StudentModel", foreign_keys=[created_by])
    connections_as_source = relationship(
        "CourseConnectionModel",
        foreign_keys="CourseConnectionModel.course_id",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    connections_as_target = relationship(
        "CourseConnectionModel",
        foreign_keys="CourseConnectionModel.connected_course_id",
        back_populates="connected_course",
        cascade="all, delete-orphan",
    )

    @property
    def connected_course_ids(self) -> list[int]:
        source_ids = [connection.connected_course_id for connection in self.connections_as_source]
        target_ids = [connection.course_id for connection in self.connections_as_target]
        return sorted(set(source_ids + target_ids))


class CourseConnectionModel(Base):
    __tablename__ = "course_connections"

    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    connected_course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True
    )
    created_at = Column(DateTime, nullable=False, server_default=text("now()"))

    course = relationship(
        "CourseModel", foreign_keys=[course_id], back_populates="connections_as_source"
    )
    connected_course = relationship(
        "CourseModel",
        foreign_keys=[connected_course_id],
        back_populates="connections_as_target",
    )

    __table_args__ = (
        CheckConstraint("course_id < connected_course_id", name="ck_course_connections_ordering"),
    )


class FacultyModel(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    language = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    departments = relationship("DepartmentModel", back_populates="faculty")


class DepartmentModel(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    code = Column(String, nullable=False, unique=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"), nullable=True)
    description = Column(Text, nullable=True)
    language = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    faculty = relationship("FacultyModel", back_populates="departments")
    professors = relationship("ProfessorModel", back_populates="department")
    courses = relationship("CourseModel", back_populates="department")


class LectureModel(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    revision = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    title = Column(String, nullable=False)
    audio_url = Column(String, nullable=True)
    transcript_url = Column(String, nullable=True)
    timeline_url = Column(String, nullable=True)
    images_timeline_url = Column(String, nullable=True)
    language = Column(String, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    voice_id = Column(Integer, ForeignKey("voices.id"), nullable=True)
    word_count = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # Audio duration in seconds
    # Attribution fields
    created_by = Column(Integer, ForeignKey("students.id"), nullable=True)
    created_with = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    course = relationship("CourseModel", back_populates="lectures")
    topic = relationship("TopicModel", back_populates="lectures")
    voice = relationship("VoiceModel")
    student = relationship("StudentModel", foreign_keys=[created_by])


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
    image_created_with = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    voice_id = Column(Integer, ForeignKey("voices.id"), nullable=True)
    tts_backend = Column(String(50), nullable=True)  # Per-professor TTS backend override
    language = Column(String, nullable=True)
    # Attribution fields
    created_by = Column(Integer, ForeignKey("students.id"), nullable=True)
    created_with = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    department = relationship("DepartmentModel", back_populates="professors")
    courses = relationship("CourseModel", back_populates="professor")
    voice = relationship("VoiceModel", back_populates="professor")
    student = relationship("StudentModel", foreign_keys=[created_by])


class TopicModel(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    order = Column(Integer, nullable=False, default=1)
    week = Column(Integer, nullable=False, index=True)
    content = Column(JSONB, nullable=True)
    language = Column(String, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    # Attribution fields
    created_by = Column(Integer, ForeignKey("students.id"), nullable=True)
    created_with = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    course = relationship("CourseModel", back_populates="topics")
    lectures = relationship("LectureModel", back_populates="topic")
    student = relationship("StudentModel", foreign_keys=[created_by])

    # Ensure unique combination of course_id + week + order
    __table_args__ = (
        UniqueConstraint("course_id", "week", "order", name="uq_topic_course_week_order"),
    )


class VoiceModel(Base):
    __tablename__ = "voices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tts_backend = Column(String(50), nullable=False, default="elevenlabs")
    external_id = Column(String, nullable=True)
    el_voice_id = Column(String, nullable=True, unique=True)
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
    verified_languages = Column(JSONB, nullable=True)
    last_updated = Column(DateTime, nullable=False, default=datetime.now)
    cloned_from = Column(Integer, ForeignKey("voices.id", ondelete="SET NULL"), nullable=True)

    professor = relationship("ProfessorModel", back_populates="voice")

    # Create indexes
    __table_args__ = (
        Index("idx_voices_language", "language"),
        Index("idx_voices_tts_backend", "tts_backend"),
        Index(
            "uq_voices_backend_external_id",
            "tts_backend",
            "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
        # We'll create the text search index manually after migrations
        # to avoid Alembic issues with REGCONFIG type
    )


class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kind = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String, nullable=False, default="queued")
    priority = Column(Integer, nullable=False, default=0)
    run_after = Column(DateTime, nullable=False, default=datetime.now)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    last_error = Column(Text, nullable=True)
    result = Column(JSONB, nullable=True)
    parent_job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("idx_jobs_status_priority_runafter", "status", "priority", "run_after"),
        Index("idx_jobs_status_updatedat", "status", "updated_at"),
        Index("idx_jobs_parent_job_id", "parent_job_id"),
    )


class StudentModel(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    auth0_sub = Column(String, nullable=True, unique=True)
    role = Column(String, nullable=False, default="viewer")
    coins = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (Index("idx_students_email", "email"),)


class PreferenceModel(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    scope = Column(String, nullable=False)
    value = Column(String, nullable=False)
    is_global = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    student = relationship("StudentModel")

    __table_args__ = (
        # For global preferences, scope must be unique
        Index(
            "idx_preferences_global_scope",
            "scope",
            unique=True,
            postgresql_where=Column("is_global").is_(True),
        ),
        # For user preferences, student_id + scope must be unique
        Index(
            "idx_preferences_student_scope",
            "student_id",
            "scope",
            unique=True,
            postgresql_where=Column("is_global").is_(False),
        ),
        # Index for efficient lookup of global preferences
        Index("idx_preferences_is_global", "is_global"),
    )


class FeaturedItemModel(Base):
    """A featured item that appears on the homepage (lecture, professor, or department)."""

    __tablename__ = "featured_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_type = Column(String, nullable=False)  # "lecture", "professor", "department"
    item_id = Column(Integer, nullable=False)  # Reference to the source table's PK
    language = Column(String, nullable=False, default="en")
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("ix_featured_items_type_language", "item_type", "language"),
        UniqueConstraint(
            "item_type", "item_id", "language", name="uq_featured_items_type_id_language"
        ),
    )
