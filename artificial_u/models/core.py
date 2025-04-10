"""
Core data models for the ArtificialU system.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


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

    id: Optional[str] = None
    name: str
    code: str
    faculty: str  # e.g., "Science and Engineering"
    description: str


class Professor(BaseModel):
    """Professor model representing a virtual faculty member."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Dr. Mikhail Volkov",
                "title": "Professor of Computer Science",
                "department": "Computer Science",
                "specialization": "Artificial Intelligence",
                "background": "58-year-old Russian-American computer scientist with background at Moscow State University and Bell Labs",
                "personality": "Methodical, philosophical, occasional dry humor",
                "teaching_style": "Combines methodical explanations with philosophical perspectives",
                "gender": "Male",
                "accent": "Russian",
                "description": "He has a distinguished appearance with salt-and-pepper hair neatly combed to the side and a well-groomed thick mustache but no beard. He wears tortoiseshell glasses that rest on a prominent nose. His face shows the subtle lines of experience, particularly around his eyes when he smiles, which is infrequent but warm. He typically dresses in academic formal wear - often a tweed or navy blazer with elbow patches, pressed slacks, a crisp button-down shirt, and his signature accessory: an assortment of bow ties (today's is burgundy). He stands with perfect posture, shoulders back, at about 5'10\". When lecturing, he often holds a piece of chalk delicately between his long fingers, occasionally tapping it thoughtfully against his palm. His expression is serious and contemplative, with piercing blue-gray eyes that suggest both analytical precision and philosophical depth. The lecture hall behind him features a traditional chalkboard filled with neat, methodical writing. On his desk sits a vintage leather satchel containing meticulously organized lecture notes and several dog-eared technical papers marked with precise annotations.",
                "age": 58,
                "voice_settings": {
                    "voice_id": "example_id",
                    "stability": 0.5,
                    "clarity": 0.8,
                },
            }
        }
    )

    id: Optional[str] = None
    name: str
    title: str
    department: str
    specialization: str
    background: str
    personality: str
    teaching_style: str
    gender: Optional[str] = None
    accent: Optional[str] = None
    description: Optional[str] = None
    age: Optional[int] = None
    voice_settings: Dict[str, Any] = Field(default_factory=dict)
    image_path: Optional[str] = None


class Course(BaseModel):
    """Course model representing a complete academic course."""

    model_config = ConfigDict(
        json_schema_extra={
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
    )

    id: Optional[str] = None
    code: str
    title: str
    department: str
    level: str  # Undergraduate, Graduate, etc.
    credits: int = Field(default=3, ge=0)
    professor_id: str
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
                "course_id": "CS4511",
                "week_number": 1,
                "order_in_week": 1,
                "description": "Overview of AI definitions, history, and intelligent agents",
                "content": "Good morning, students. Welcome to CSCI-4511...",
                "audio_path": "audio_files/CS4511/week1/lecture1.mp3",
            }
        }
    )

    id: Optional[str] = None
    title: str
    course_id: str
    week_number: int = Field(gt=0)
    order_in_week: int = Field(default=1, gt=0)
    description: str
    content: str
    audio_path: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.now)
