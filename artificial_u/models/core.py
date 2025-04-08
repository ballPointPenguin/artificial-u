"""
Core data models for the ArtificialU system.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class Professor(BaseModel):
    """Professor model representing a virtual faculty member."""

    id: Optional[str] = None
    name: str
    title: str
    department: str
    specialization: str
    background: str
    personality: str
    teaching_style: str
    voice_settings: Dict[str, any] = Field(default_factory=dict)
    image_path: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Dr. Mikhail Volkov",
                "title": "Professor of Computer Science",
                "department": "Computer Science",
                "specialization": "Artificial Intelligence",
                "background": "58-year-old Russian-American computer scientist with background at Moscow State University and Bell Labs",
                "personality": "Methodical, philosophical, occasional dry humor",
                "teaching_style": "Combines methodical explanations with philosophical perspectives",
                "voice_settings": {
                    "voice_id": "example_id",
                    "stability": 0.5,
                    "clarity": 0.8,
                },
            }
        }


class Lecture(BaseModel):
    """Lecture model representing a single class session."""

    id: Optional[str] = None
    title: str
    course_id: str
    week_number: int
    order_in_week: int = 1
    description: str
    content: str
    audio_path: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introduction: What is AI?",
                "course_id": "CS4511",
                "week_number": 1,
                "order_in_week": 1,
                "description": "Overview of AI definitions, history, and intelligent agents",
                "content": "Good morning, students. Welcome to CSCI-4511...",
                "audio_path": "audio_files/CS4511/week1/lecture1.mp3",
            }
        }


class Course(BaseModel):
    """Course model representing a complete academic course."""

    id: Optional[str] = None
    code: str
    title: str
    department: str
    level: str  # Undergraduate, Graduate, etc.
    credits: int = 3
    professor_id: str
    description: str
    lectures_per_week: int = 2
    total_weeks: int = 14
    syllabus: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "code": "CS4511",
                "title": "Introduction to Artificial Intelligence",
                "department": "Computer Science",
                "level": "Undergraduate",
                "credits": 3,
                "professor_id": "prof_volkov",
                "description": "Foundational concepts and techniques in AI, including problem-solving, search, logic, and planning.",
                "lectures_per_week": 2,
                "total_weeks": 14,
            }
        }


class Department(BaseModel):
    """Department model representing an academic department."""

    id: Optional[str] = None
    name: str
    code: str
    faculty: str  # e.g., "Science and Engineering"
    description: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Computer Science",
                "code": "CS",
                "faculty": "Science and Engineering",
                "description": "The Computer Science department focuses on the theory and practice of computation.",
            }
        }
