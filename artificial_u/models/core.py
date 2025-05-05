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
                "id": 1,
                "name": "Computer Science",
                "code": "CS",
                "faculty": "Science and Engineering",
                "description": "The Computer Science department focuses on the theory and "
                "practice of computation.",
            }
        }
    )

    id: Optional[int] = None
    name: str
    code: str
    faculty: Optional[str] = None  # e.g., "Science and Engineering"
    description: Optional[str] = None


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
    verified_languages: Dict[str, Any] = Field(default_factory=dict)
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
    department_id: Optional[int] = None
    voice_id: Optional[int] = None


class Course(BaseModel):
    """Course model representing a complete academic course."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "code": "CS4511",
                "title": "Introduction to Artificial Intelligence",
                "credits": 3,
                "description": "Foundational concepts and techniques in AI.",
                "lectures_per_week": 1,
                "level": "Undergraduate",
                "total_weeks": 14,
                "department_id": 1,
                "professor_id": 1,
            }
        }
    )

    id: Optional[int] = None
    code: str
    title: str
    credits: int = Field(default=3, ge=0)
    description: Optional[str] = None
    lectures_per_week: int = 1
    level: Optional[str] = None
    total_weeks: int = 14
    department_id: Optional[int] = None
    professor_id: Optional[int] = None


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
            }
        }
    )

    id: Optional[int] = None
    title: str
    order: int = Field(default=1, gt=0)
    week: int = Field(default=1, gt=0)
    course_id: int


class Lecture(BaseModel):
    """Lecture model representing a single class session."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "revision": 1,
                "content": "Good morning, students. Welcome to CSCI-4511...",
                "summary": "Overview of AI definitions, history, and intelligent agents",
                "audio_url": "https://example.com/audio_files/CS4511/week1/lecture1.mp3",
                "transcript_url": "https://example.com/transcript_files/CS4511/week1/lecture1.txt",
                "course_id": 1,
                "topic_id": 1,
            }
        }
    )

    id: Optional[int] = None
    revision: int = Field(default=1, gt=0)
    content: Optional[str] = None
    summary: Optional[str] = None
    audio_url: Optional[str] = None
    transcript_url: Optional[str] = None
    course_id: int
    topic_id: int
