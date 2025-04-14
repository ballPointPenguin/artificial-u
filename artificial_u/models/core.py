"""
Core data models for the ArtificialU system.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class Department(BaseModel):
    """Department model representing an academic department."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Computer Science",
                "code": "CS",
                "faculty": "Science and Engineering",
                "description": "The Computer Science department focuses on the theory and practice of computation.",
            }
        }
    )

    id: Optional[int] = None
    name: str
    code: str
    faculty: str  # e.g., "Science and Engineering"
    description: str
    generated_at: datetime = Field(default_factory=datetime.now)


class Voice(BaseModel):
    """Voice model representing an ElevenLabs voice."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "el_voice_id": "MF4J4IDTRo0AxOO4dpFR",
                "name": "Devi - Clear Hindi pronunciation",
                "accent": "standard",
                "gender": "female",
                "age": "young",
                "descriptive": "professional",
                "use_case": "informative_educational",
                "category": "high_quality",
                "language": "hi",
                "locale": "hi-IN",
                "description": "Devi is the pen name of a young Indian female artist with clear Hindi instructions.",
                "preview_url": "https://storage.googleapis.com/eleven-public-prod/voices/example.mp3",
                "verified_languages": {
                    "languages": [
                        {
                            "language": "hi",
                            "model_id": "eleven_turbo_v2_5",
                            "accent": "standard",
                            "locale": "hi-IN",
                        }
                    ]
                },
                "popularity_score": 138250,
            }
        }
    )

    id: Optional[int] = None
    el_voice_id: str
    name: str
    accent: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    descriptive: Optional[str] = None
    use_case: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None
    verified_languages: Dict[str, Any] = Field(default_factory=dict)
    popularity_score: Optional[int] = None
    last_updated: datetime = Field(default_factory=datetime.now)


class Professor(BaseModel):
    """Professor model representing a virtual faculty member."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Dr. Mikhail Volkov",
                "title": "Professor of Computer Science",
                "department_id": 1,
                "specialization": "Artificial Intelligence",
                "background": "58-year-old Russian-American CS professor (Moscow State, Bell Labs)",
                "personality": "Methodical, philosophical, occasional dry humor",
                "teaching_style": "Combines methodical explanations with philosophical perspectives",
                "gender": "Male",
                "accent": "Russian",
                "description": "Distinguished, salt-and-pepper hair, mustache, glasses. Formal wear, bow tie.",
                "age": 58,
                "voice_id": 1,
            }
        }
    )

    id: Optional[int] = None
    name: str
    title: str
    department_id: Optional[int] = None
    specialization: str
    background: str
    personality: str
    teaching_style: str
    gender: Optional[str] = None
    accent: Optional[str] = None
    description: Optional[str] = None
    age: Optional[int] = None
    image_url: Optional[str] = None
    voice_id: Optional[int] = None


class Course(BaseModel):
    """Course model representing a complete academic course."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "CS4511",
                "title": "Introduction to Artificial Intelligence",
                "department_id": 1,
                "level": "Undergraduate",
                "credits": 3,
                "professor_id": 1,
                "description": "Foundational concepts and techniques in AI.",
                "lectures_per_week": 2,
                "total_weeks": 14,
            }
        }
    )

    id: Optional[int] = None
    code: str
    title: str
    department_id: Optional[int] = None
    level: str  # Undergraduate, Graduate, etc.
    credits: int = Field(default=3, ge=0)
    professor_id: Optional[int] = None
    description: str
    lectures_per_week: int = Field(default=2, gt=0)
    total_weeks: int = Field(default=14, gt=0)
    syllabus: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.now)


class Lecture(BaseModel):
    """Lecture model representing a single class session."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Introduction: What is AI?",
                "course_id": 1,
                "week_number": 1,
                "order_in_week": 1,
                "description": "Overview of AI definitions, history, and intelligent agents",
                "content": "Good morning, students. Welcome to CSCI-4511...",
                "audio_url": "https://storage.example.com/audio_files/CS4511/week1/lecture1.mp3",
            }
        }
    )

    id: Optional[int] = None
    title: str
    course_id: int
    week_number: int = Field(gt=0)
    order_in_week: int = Field(default=1, gt=0)
    description: str
    content: str
    audio_url: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.now)
