"""
Main system class for ArtificialU.
"""

import os
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import uuid

from artificial_u.generators.content import ContentGenerator
from artificial_u.audio.processor import AudioProcessor
from artificial_u.models.database import Repository
from artificial_u.models.core import Professor, Course, Lecture, Department


class UniversitySystem:
    """
    Core system class for ArtificialU.
    Integrates content generation, audio processing, and data storage.
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None,
        db_path: Optional[str] = None,
        audio_path: Optional[str] = None,
    ):
        """
        Initialize the university system.

        Args:
            anthropic_api_key: Anthropic API key for content generation
            elevenlabs_api_key: ElevenLabs API key for audio generation
            db_path: Path to SQLite database
            audio_path: Path to store audio files
        """
        self.content_generator = ContentGenerator(api_key=anthropic_api_key)
        self.audio_processor = AudioProcessor(
            api_key=elevenlabs_api_key, audio_path=audio_path
        )
        self.repository = Repository(db_path=db_path)

    def create_professor(
        self,
        name: Optional[str] = None,
        department: str = "Computer Science",
        specialization: str = "Artificial Intelligence",
        gender: Optional[str] = None,
        nationality: Optional[str] = None,
        age_range: Optional[str] = None,
    ) -> Professor:
        """
        Create a new professor with a consistent personality.

        Args:
            name: Professor name (if None, will be generated)
            department: Academic department
            specialization: Area of expertise
            gender: Optional gender specification
            nationality: Optional nationality specification
            age_range: Optional age range

        Returns:
            Professor: The created professor profile
        """
        # Generate professor profile using content generator
        professor = self.content_generator.create_professor(
            department=department,
            specialization=specialization,
            gender=gender,
            nationality=nationality,
            age_range=age_range,
        )

        # Save to database
        return self.repository.create_professor(professor)

    def create_course(
        self,
        title: str,
        code: str,
        department: str,
        level: str = "Undergraduate",
        professor_id: Optional[str] = None,
        description: Optional[str] = None,
        weeks: int = 14,
        lectures_per_week: int = 2,
    ) -> Tuple[Course, Professor]:
        """
        Create a new course with syllabus.

        Args:
            title: Course title
            code: Course code (e.g., "CS101")
            department: Academic department
            level: Course level (Undergraduate, Graduate, etc.)
            professor_id: ID of existing professor (if None, will create new)
            description: Course description (if None, will be generated)
            weeks: Number of weeks in the course
            lectures_per_week: Number of lectures per week

        Returns:
            Tuple: (Course, Professor) - The created course and its professor
        """
        # Get or create professor
        if professor_id:
            professor = self.repository.get_professor(professor_id)
            if not professor:
                raise ValueError(f"Professor with ID {professor_id} not found")
        else:
            professor = self.create_professor(department=department)

        # Create basic course
        if not description:
            description = f"A {level} course on {title} in the {department} department."

        course = Course(
            code=code,
            title=title,
            department=department,
            level=level,
            professor_id=professor.id,
            description=description,
            total_weeks=weeks,
            lectures_per_week=lectures_per_week,
        )

        # Generate syllabus
        syllabus = self.content_generator.create_course_syllabus(course, professor)
        course.syllabus = syllabus

        # Save to database
        course = self.repository.create_course(course)

        return course, professor

    def generate_lecture(
        self, course_code: str, week: int, number: int = 1, topic: Optional[str] = None
    ) -> Tuple[Lecture, Course, Professor]:
        """
        Generate a lecture for a specific course and week.

        Args:
            course_code: Course code
            week: Week number
            number: Lecture number within the week
            topic: Lecture topic (if None, will be derived from syllabus)

        Returns:
            Tuple: (Lecture, Course, Professor) - The generated lecture with its course and professor
        """
        # Get course
        course = self.repository.get_course_by_code(course_code)
        if not course:
            raise ValueError(f"Course with code {course_code} not found")

        # Get professor
        professor = self.repository.get_professor(course.professor_id)
        if not professor:
            raise ValueError(f"Professor with ID {course.professor_id} not found")

        # Get previous lecture if available (for continuity)
        previous_lecture = None
        if week > 1 or (week == 1 and number > 1):
            prev_week = week
            prev_number = number - 1
            if prev_number < 1:
                prev_week -= 1
                prev_number = course.lectures_per_week

            previous_lecture = self.repository.get_lecture_by_course_week_order(
                course_id=course.id, week_number=prev_week, order_in_week=prev_number
            )

        # Use topic from parameters or generate appropriate topic
        if not topic:
            # In a real implementation, would parse syllabus to extract topic
            # For now, use a placeholder
            topic = f"Topic for Week {week}, Lecture {number}"

        # Generate lecture content
        lecture = self.content_generator.create_lecture(
            course=course,
            professor=professor,
            topic=topic,
            week_number=week,
            order_in_week=number,
            previous_lecture_content=(
                previous_lecture.content if previous_lecture else None
            ),
        )

        # Save to database
        lecture = self.repository.create_lecture(lecture)

        return lecture, course, professor

    def create_lecture_audio(
        self, course_code: str, week: int, number: int = 1
    ) -> Tuple[str, Lecture]:
        """
        Create audio for a lecture.

        Args:
            course_code: Course code
            week: Week number
            number: Lecture number within the week

        Returns:
            Tuple: (audio_path, lecture) - Path to the audio file and the lecture
        """
        # Get course
        course = self.repository.get_course_by_code(course_code)
        if not course:
            raise ValueError(f"Course with code {course_code} not found")

        # Get lecture
        lecture = self.repository.get_lecture_by_course_week_order(
            course_id=course.id, week_number=week, order_in_week=number
        )
        if not lecture:
            raise ValueError(
                f"Lecture for course {course_code}, week {week}, number {number} not found"
            )

        # Get professor
        professor = self.repository.get_professor(course.professor_id)
        if not professor:
            raise ValueError(f"Professor with ID {course.professor_id} not found")

        # Generate audio
        audio_path, _ = self.audio_processor.text_to_speech(lecture, professor)

        # Update lecture with audio path
        lecture = self.repository.update_lecture_audio(lecture.id, audio_path)

        return audio_path, lecture

    def list_departments(self) -> List[Department]:
        """
        List all departments.

        Returns:
            List[Department]: List of departments
        """
        # In a complete implementation, would retrieve from database
        # For now, return placeholder data
        return [
            Department(
                id="cs",
                name="Computer Science",
                code="CS",
                faculty="Science and Engineering",
                description="The Computer Science department focuses on the theory and practice of computation.",
            ),
            Department(
                id="math",
                name="Mathematics",
                code="MATH",
                faculty="Science and Engineering",
                description="The Mathematics department explores pure and applied mathematics.",
            ),
            Department(
                id="stat",
                name="Statistics",
                code="STAT",
                faculty="Science and Engineering",
                description="The Statistics department focuses on statistical theory and its applications to data analysis.",
            ),
        ]

    def list_courses(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all courses with professor information.

        Args:
            department: Optional department to filter by

        Returns:
            List[Dict]: List of courses with professor information
        """
        courses = self.repository.list_courses(department)
        result = []

        for course in courses:
            professor = self.repository.get_professor(course.professor_id)
            result.append({"course": course, "professor": professor})

        return result

    def get_sample_lecture(self) -> str:
        """
        Get sample lecture content for testing.

        Returns:
            str: Sample lecture content
        """
        # In a real implementation, this would load from a file or generate dynamically
        sample_path = Path(__file__).parent.parent / "samples" / "sample_lecture.md"
        if sample_path.exists():
            with open(sample_path, "r") as f:
                return f.read()

        # Placeholder if file doesn't exist
        return """
        # Introduction to Neural Networks
        
        *[Professor enters the lecture hall]*
        
        Good morning, everyone. Today we'll be discussing the fundamentals of neural networks...
        
        *[The rest of the lecture would go here]*
        """
