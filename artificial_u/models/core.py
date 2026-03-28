"""
Core data models for the ArtificialU system.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Faculty(BaseModel):
    """Faculty model representing an academic faculty."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Science and Engineering",
                "description": "The Faculty of Science and Engineering encompasses "
                "departments focused on scientific and technological disciplines.",
                "language": "en",
            }
        }
    )

    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    language: Optional[str] = None
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Department(BaseModel):
    """Department model representing an academic department."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Computer Science",
                "code": "CS",
                "faculty_id": 1,
                "description": "The Computer Science department focuses on the theory and "
                "practice of computation.",
                "language": "en",
            }
        }
    )

    id: Optional[int] = None
    name: str
    code: str
    faculty_id: Optional[int] = None
    description: Optional[str] = None
    language: Optional[str] = None
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Voice(BaseModel):
    """Voice model representing an ElevenLabs voice."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "el_voice_id": "MF4J4IDTRo0AxOO4dpFR",
                "name": "Devi - Clear Hindi pronunciation",
                "accent": "standard",
                "age": "young",
                "category": "high_quality",
                "description": "Devi is the pen name of a young Indian female artist with "
                "clear Hindi instructions.",
                "descriptive": "professional",
                "gender": "female",
                "language": "hi",
                "locale": "hi-IN",
                "popularity_score": 138250,
                "preview_url": "https://storage.googleapis.com/eleven-public-prod/voices/"
                "example.mp3",
                "use_case": "informative_educational",
                "verified_languages": [
                    {
                        "language": "hi",
                        "model_id": "eleven_turbo_v2_5",
                        "accent": "standard",
                        "locale": "hi-IN",
                        "preview_url": "https://storage.googleapis.com/eleven-public-prod/"
                        "voices/example.mp3",
                    }
                ],
                "last_updated": "2025-05-05T00:00:00Z",
            }
        }
    )

    id: Optional[int] = None
    el_voice_id: str
    name: Optional[str] = None
    accent: Optional[str] = None
    age: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    descriptive: Optional[str] = None
    gender: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None
    popularity_score: Optional[int] = None
    preview_url: Optional[str] = None
    use_case: Optional[str] = None
    verified_languages: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)


class Professor(BaseModel):
    """Professor model representing a virtual faculty member."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "Dr. Mikhail Volkov",
                "title": "Professor of Computer Science",
                "accent": "Russian",
                "age": 58,
                "background": "58-year-old Russian-American CS professor (Moscow State, Bell Labs)",
                "description": "Distinguished, salt-and-pepper hair, mustache, glasses. "
                "Formal wear, bow tie.",
                "gender": "Male",
                "personality": "Methodical, philosophical, occasional dry humor",
                "specialization": "Artificial Intelligence",
                "teaching_style": "Combines methodical explanations with philosophical "
                "perspectives",
                "department_id": 1,
                "voice_id": 1,
                "image_url": "https://storage.example.com/professors/mikhail_volkov.jpg",
            }
        }
    )

    id: Optional[int] = None
    name: str
    title: Optional[str] = None
    accent: Optional[str] = None
    age: Optional[int] = None
    background: Optional[str] = None
    description: Optional[str] = None
    gender: Optional[str] = None
    personality: Optional[str] = None
    specialization: Optional[str] = None
    teaching_style: Optional[str] = None
    image_url: Optional[str] = None
    image_created_with: Optional[str] = None
    department_id: Optional[int] = None
    voice_id: Optional[int] = None
    # Attribution
    created_by: Optional[int] = None
    created_with: Optional[str] = None
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Related objects
    student: Optional["Student"] = None


class Course(BaseModel):
    """Course model representing a complete academic course."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "code": "CS4511",
                "title": "Introduction to Artificial Intelligence",
                "description": "Foundational concepts and techniques in AI.",
                "lectures_per_week": 1,
                "level": "Undergraduate",
                "total_weeks": 12,
                "language": "en",
                "department_id": 1,
                "professor_id": 1,
            }
        }
    )

    id: Optional[int] = None
    code: str
    title: str
    description: Optional[str] = None
    lectures_per_week: int = 1
    level: Optional[str] = None
    total_weeks: int = 12
    language: Optional[str] = None
    status: Literal["hidden", "published"] = "hidden"
    department_id: Optional[int] = None
    professor_id: Optional[int] = None
    # Attribution
    created_by: Optional[int] = None
    created_with: Optional[str] = None
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Related objects
    professor: Optional["Professor"] = None
    department: Optional["Department"] = None
    student: Optional["Student"] = None
    # Audio/Topic Counts
    lectures_with_audio_count: Optional[int] = 0
    topics_count: Optional[int] = 0


class Topic(BaseModel):
    """Topic model representing a course topic."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Introduction: What is AI?",
                "order": 1,
                "week": 1,
                "course_id": 1,
                "language": "en",
                "content": {
                    "lecture": "What is Artificial Intelligence?",
                    "readings": [
                        "Nilsson, Nils. The Quest for Artificial Intelligence (Ch. 1)",
                        "Russell & Norvig. AI: A Modern Approach (Ch. 1)",
                    ],
                    "objectives": [
                        "Define artificial intelligence",
                        "Understand key AI applications",
                    ],
                },
            }
        }
    )

    id: Optional[int] = None
    title: str
    order: int = Field(default=1, gt=0)
    week: int = Field(default=1, gt=0)
    course_id: int
    language: Optional[str] = None
    content: Optional[Dict[str, Any]] = Field(
        default=None, description="Flexible JSONB content for the topic"
    )
    # Attribution
    created_by: Optional[int] = None
    created_with: Optional[str] = None
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Related objects
    student: Optional["Student"] = None


class Lecture(BaseModel):
    """Lecture model representing a single class session."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "revision": 1,
                "content": "Good morning, students. Welcome to CSCI-4511...",
                "summary": "Overview of AI definitions, history, and intelligent agents",
                "title": "Introduction to AI",
                "audio_url": "https://example.com/audio_files/CS4511/week1/lecture1.mp3",
                "transcript_url": "https://example.com/transcript_files/CS4511/week1/lecture1.txt",
                "language": "en",
                "course_id": 1,
                "topic_id": 1,
                "voice_id": 1,
            }
        }
    )

    id: Optional[int] = None
    revision: Optional[int] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    title: Optional[str] = None
    audio_url: Optional[str] = None
    transcript_url: Optional[str] = None
    language: Optional[str] = None
    course_id: int
    topic_id: int
    voice_id: Optional[int] = None
    word_count: Optional[int] = None
    duration: Optional[int] = None  # Audio duration in seconds
    # Attribution
    created_by: Optional[int] = None
    created_with: Optional[str] = None
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Related objects
    student: Optional[Dict[str, Any]] = None


class Student(BaseModel):
    """
    Student model representing an authenticated user profile in our system.
    """

    id: Optional[int] = None
    name: str
    email: Optional[str] = None
    auth0_sub: Optional[str] = None
    role: str = "viewer"
    coins: int = 0
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Preference(BaseModel):
    """
    Preference model representing a user or global application setting.

    Preferences can be either user-specific (student_id is set) or global
    (is_global is True). The scope field identifies what the preference
    controls (e.g., "LECTURE_GENERATION_MODEL"), and value holds the
    setting value.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "student_id": None,
                "scope": "LECTURE_GENERATION_MODEL",
                "value": "claude-opus-4-6",
                "is_global": True,
                "created_at": "2025-12-19T00:00:00Z",
                "updated_at": "2025-12-19T00:00:00Z",
            }
        }
    )

    id: Optional[int] = None
    student_id: Optional[int] = None
    scope: str
    value: str
    is_global: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PreferenceCreate(BaseModel):
    """Request model for creating or updating a preference."""

    scope: str = Field(..., description="The preference scope/key")
    value: str = Field(..., description="The preference value")
    is_global: bool = Field(
        default=False, description="Whether this is a global preference (admin only)"
    )
    student_id: Optional[int] = Field(
        default=None, description="Student ID for user-specific preferences"
    )


class FeaturedItem(BaseModel):
    """A featured item displayed on the homepage."""

    id: Optional[int] = None
    item_type: str  # "lecture", "professor", "department"
    item_id: int
    language: str = "en"
    display_order: int = 0
    created_at: Optional[datetime] = None
