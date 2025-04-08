"""
Main system class for ArtificialU.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import uuid
import random

from artificial_u.generators.content import ContentGenerator
from artificial_u.generators.factory import create_generator
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
        content_backend: str = "anthropic",
        content_model: Optional[str] = None,
    ):
        """
        Initialize the university system.

        Args:
            anthropic_api_key: API key for Anthropic, uses ANTHROPIC_API_KEY env var if not provided
            elevenlabs_api_key: API key for ElevenLabs, uses ELEVENLABS_API_KEY env var if not provided
            db_path: Path to SQLite database, uses DATABASE_PATH env var or 'university.db' if not provided
            audio_path: Path to store audio files, uses AUDIO_PATH env var or 'audio_files' if not provided
            content_backend: Backend to use for content generation ('anthropic' or 'ollama')
            content_model: Model to use with the chosen backend (depends on backend)
        """
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Setup content generator
        backend_kwargs = {}
        if content_backend == "anthropic":
            backend_kwargs["api_key"] = anthropic_api_key
        elif content_backend == "ollama":
            backend_kwargs["model"] = content_model or "tinyllama"

        self.content_generator = create_generator(
            backend=content_backend, **backend_kwargs
        )

        # Setup audio processor
        self.audio_processor = AudioProcessor(api_key=elevenlabs_api_key)

        # Setup database repository
        self.repository = Repository(db_path=db_path)

        # Setup audio path
        self.audio_path = audio_path or os.environ.get("AUDIO_PATH", "audio_files")
        Path(self.audio_path).mkdir(parents=True, exist_ok=True)

    def create_professor(
        self,
        name: Optional[str] = None,
        title: Optional[str] = None,
        department: Optional[str] = None,
        specialization: Optional[str] = None,
        background: Optional[str] = None,
        teaching_style: Optional[str] = None,
        personality: Optional[str] = None,
    ) -> Professor:
        """
        Create a new professor with the given attributes.

        If parameters are not provided, default or AI-generated values will be used.
        """
        # Generate default name if not provided
        if name is None:
            # Use a simple default name rather than requiring the ContentGenerator to have generate_random_name
            random_last_names = [
                "Smith",
                "Johnson",
                "Williams",
                "Brown",
                "Jones",
                "Miller",
                "Davis",
                "Wilson",
                "Taylor",
                "Clark",
            ]
            name = f"Dr. {random.choice(random_last_names)}"

        # Generate default department if not provided
        if department is None:
            departments = [
                "Computer Science",
                "Physics",
                "Biology",
                "Mathematics",
                "History",
                "Psychology",
            ]
            department = random.choice(departments)

        # Generate default specialization if not provided
        if specialization is None:
            specializations = {
                "Computer Science": [
                    "Machine Learning",
                    "Software Engineering",
                    "Cybersecurity",
                ],
                "Physics": ["Quantum Mechanics", "Astrophysics", "Particle Physics"],
                "Biology": ["Molecular Biology", "Genetics", "Ecology"],
                "Mathematics": [
                    "Number Theory",
                    "Applied Statistics",
                    "Differential Equations",
                ],
                "History": [
                    "Ancient Civilizations",
                    "Modern History",
                    "Political History",
                ],
                "Psychology": [
                    "Cognitive Psychology",
                    "Clinical Psychology",
                    "Developmental Psychology",
                ],
            }
            dept_specializations = specializations.get(department, ["General"])
            specialization = random.choice(dept_specializations)

        # Generate default title if not provided
        if title is None:
            # Randomly choose an academic title
            academic_titles = [
                "Professor",
                "Associate Professor",
                "Assistant Professor",
                "Adjunct Professor",
            ]
            academic_rank = random.choice(academic_titles)
            title = f"{academic_rank} of {department}"

        # Generate default background if not provided
        if background is None:
            background = f"Experienced educator with expertise in {specialization}"

        # Generate default teaching style if not provided
        if teaching_style is None:
            styles = [
                "Interactive",
                "Lecture-based",
                "Discussion-oriented",
                "Practical",
                "Research-focused",
            ]
            teaching_style = random.choice(styles)

        # Generate default personality if not provided
        if personality is None:
            personalities = [
                "Enthusiastic",
                "Methodical",
                "Inspiring",
                "Analytical",
                "Patient",
                "Innovative",
            ]
            personality = random.choice(personalities)

        professor = Professor(
            name=name,
            title=title,
            department=department,
            specialization=specialization,
            background=background,
            teaching_style=teaching_style,
            personality=personality,
        )

        # Create voice for professor
        voice_id = self.audio_processor.create_professor_voice(professor)

        # Don't set voice_id directly as it's not a field in the Professor model
        # The voice_id is already stored in professor.voice_settings by create_professor_voice

        # Save professor to repository to get an ID
        saved_professor = self.repository.create_professor(professor)

        return saved_professor

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
            professor = self.create_professor()

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
