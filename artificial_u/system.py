"""
Main system class for ArtificialU.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import uuid
from datetime import datetime

from artificial_u.generators.content import ContentGenerator
from artificial_u.generators.factory import create_generator
from artificial_u.audio.processor import AudioProcessor
from artificial_u.models.database import Repository
from artificial_u.models.core import Professor, Course, Lecture, Department
from artificial_u.utils.random_generators import RandomGenerators
from artificial_u.utils.exceptions import (
    ProfessorNotFoundError,
    CourseNotFoundError,
    LectureNotFoundError,
    ContentGenerationError,
    AudioProcessingError,
    DatabaseError,
    ConfigurationError,
)
from artificial_u.config.defaults import (
    DEFAULT_DB_PATH,
    DEFAULT_AUDIO_PATH,
    DEFAULT_TEXT_EXPORT_PATH,
    DEFAULT_CONTENT_BACKEND,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_COURSE_LEVEL,
    DEFAULT_COURSE_WEEKS,
    DEFAULT_LECTURES_PER_WEEK,
    DEFAULT_LECTURE_WORD_COUNT,
    DEFAULT_LOG_LEVEL,
)

# Default caching settings
DEFAULT_ENABLE_CACHING = False
DEFAULT_CACHE_METRICS = True


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
        content_backend: str = DEFAULT_CONTENT_BACKEND,
        content_model: Optional[str] = None,
        text_export_path: Optional[str] = None,
        log_level: str = DEFAULT_LOG_LEVEL,
        enable_caching: bool = DEFAULT_ENABLE_CACHING,
        cache_metrics: bool = DEFAULT_CACHE_METRICS,
    ):
        """
        Initialize the university system.

        Args:
            anthropic_api_key: API key for Anthropic, uses ANTHROPIC_API_KEY env var if not provided
            elevenlabs_api_key: API key for ElevenLabs, uses ELEVENLABS_API_KEY env var if not provided
            db_path: Path to SQLite database, uses DATABASE_PATH env var or default if not provided
            audio_path: Path to store audio files, uses AUDIO_PATH env var or default if not provided
            content_backend: Backend to use for content generation ('anthropic' or 'ollama')
            content_model: Model to use with the chosen backend (depends on backend)
            text_export_path: Path to export lecture text files, uses TEXT_EXPORT_PATH env var or default if not provided
            log_level: Logging level (INFO, DEBUG, etc.)
            enable_caching: Whether to enable prompt caching for Anthropic API calls
            cache_metrics: Whether to track cache metrics
        """
        # Setup logging
        self._setup_logging(log_level)

        # Setup system dependencies
        self._setup_content_generator(
            content_backend=content_backend,
            anthropic_api_key=anthropic_api_key,
            content_model=content_model,
            enable_caching=enable_caching,
            cache_metrics=cache_metrics,
        )
        self._setup_audio_processor(elevenlabs_api_key)
        self._setup_repository(db_path)
        self._setup_paths(audio_path, text_export_path)

        # Store system settings
        self.content_backend = content_backend
        self.content_model = content_model
        self.enable_caching = enable_caching

        # Log initialization
        caching_str = (
            " with caching enabled"
            if enable_caching and content_backend == "anthropic"
            else ""
        )
        self.logger.info(
            f"University system initialized with {content_backend} backend"
            f"{' and ' + content_model if content_model else ''}{caching_str}"
        )

    def _setup_logging(self, log_level: str) -> None:
        """
        Set up logging configuration.

        Args:
            log_level: Logging level string (INFO, DEBUG, etc.)
        """
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Logging configured")

    def _setup_content_generator(
        self,
        content_backend: str,
        anthropic_api_key: Optional[str] = None,
        content_model: Optional[str] = None,
        enable_caching: bool = DEFAULT_ENABLE_CACHING,
        cache_metrics: bool = DEFAULT_CACHE_METRICS,
    ) -> None:
        """
        Set up the content generator based on backend.

        Args:
            content_backend: Backend type ('anthropic' or 'ollama')
            anthropic_api_key: API key for Anthropic (if applicable)
            content_model: Model name for content generation
            enable_caching: Whether to enable prompt caching (Anthropic only)
            cache_metrics: Whether to track cache metrics
        """
        backend_kwargs = {}
        if content_backend == "anthropic":
            backend_kwargs["api_key"] = anthropic_api_key
            backend_kwargs["enable_caching"] = enable_caching
            backend_kwargs["cache_metrics"] = cache_metrics
        elif content_backend == "ollama":
            backend_kwargs["model"] = content_model or DEFAULT_OLLAMA_MODEL
        else:
            raise ConfigurationError(f"Unsupported content backend: {content_backend}")

        try:
            self.content_generator = create_generator(
                backend=content_backend, **backend_kwargs
            )
            caching_str = (
                " with caching"
                if enable_caching and content_backend == "anthropic"
                else ""
            )
            self.logger.debug(
                f"Content generator set up with {content_backend} backend{caching_str}"
            )
        except Exception as e:
            error_msg = f"Failed to initialize content generator: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg) from e

    def _setup_audio_processor(self, elevenlabs_api_key: Optional[str] = None) -> None:
        """
        Set up the audio processor.

        Args:
            elevenlabs_api_key: API key for ElevenLabs
        """
        try:
            self.audio_processor = AudioProcessor(api_key=elevenlabs_api_key)
            self.logger.debug("Audio processor set up")
        except Exception as e:
            error_msg = f"Failed to initialize audio processor: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg) from e

    def _setup_repository(self, db_path: Optional[str] = None) -> None:
        """
        Set up the database repository.

        Args:
            db_path: Path to the SQLite database
        """
        try:
            self.repository = Repository(db_path=db_path or DEFAULT_DB_PATH)
            self.logger.debug("Database repository set up")
        except Exception as e:
            error_msg = f"Failed to initialize repository: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _setup_paths(
        self, audio_path: Optional[str] = None, text_export_path: Optional[str] = None
    ) -> None:
        """
        Set up file system paths for audio and text exports.

        Args:
            audio_path: Path for audio files
            text_export_path: Path for exported text files
        """
        # Setup audio path
        self.audio_path = audio_path or os.environ.get("AUDIO_PATH", DEFAULT_AUDIO_PATH)
        Path(self.audio_path).mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Audio path set to {self.audio_path}")

        # Setup text export path
        self.text_export_path = text_export_path or os.environ.get(
            "TEXT_EXPORT_PATH", DEFAULT_TEXT_EXPORT_PATH
        )
        Path(self.text_export_path).mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Text export path set to {self.text_export_path}")

    def create_professor(
        self,
        name: Optional[str] = None,
        title: Optional[str] = None,
        department: Optional[str] = None,
        specialization: Optional[str] = None,
        background: Optional[str] = None,
        teaching_style: Optional[str] = None,
        personality: Optional[str] = None,
        gender: Optional[str] = None,
        accent: Optional[str] = None,
        description: Optional[str] = None,
        age: Optional[int] = None,
    ) -> Professor:
        """
        Create a new professor with the given attributes.

        If parameters are not provided, default or AI-generated values will be used.

        Args:
            name: Professor's name
            title: Academic title
            department: Academic department
            specialization: Research specialization
            background: Professional background
            teaching_style: Teaching methodology
            personality: Personality traits
            gender: Professor's gender (optional)
            accent: Professor's accent (optional)
            description: Physical description of the professor (optional)
            age: Professor's age (optional)

        Returns:
            Professor: The created professor object
        """
        self.logger.info("Creating new professor")

        # Generate default values for missing attributes
        name = name or RandomGenerators.generate_professor_name()
        self.logger.debug(f"Using professor name: {name}")

        department = department or RandomGenerators.generate_department()
        self.logger.debug(f"Using department: {department}")

        specialization = specialization or RandomGenerators.generate_specialization(
            department
        )
        self.logger.debug(f"Using specialization: {specialization}")

        title = title or RandomGenerators.generate_professor_title(department)
        self.logger.debug(f"Using title: {title}")

        background = background or RandomGenerators.generate_background(specialization)
        self.logger.debug(f"Using background: {background}")

        teaching_style = teaching_style or RandomGenerators.generate_teaching_style()
        self.logger.debug(f"Using teaching style: {teaching_style}")

        personality = personality or RandomGenerators.generate_personality()
        self.logger.debug(f"Using personality: {personality}")

        gender = gender or RandomGenerators.generate_gender()
        self.logger.debug(f"Using gender: {gender}")

        accent = accent or RandomGenerators.generate_accent()
        self.logger.debug(f"Using accent: {accent}")

        description = description or RandomGenerators.generate_description(gender)
        self.logger.debug("Generated physical description")

        age = age or RandomGenerators.generate_age()
        self.logger.debug(f"Using age: {age}")

        # Create professor object
        professor = Professor(
            name=name,
            title=title,
            department=department,
            specialization=specialization,
            background=background,
            teaching_style=teaching_style,
            personality=personality,
            gender=gender,
            accent=accent,
            description=description,
            age=age,
        )

        # Assign a voice to the professor
        self._assign_voice_to_professor(professor)

        # Save professor to repository to get an ID
        try:
            saved_professor = self.repository.create_professor(professor)
            self.logger.info(f"Professor created with ID: {saved_professor.id}")
            return saved_professor
        except Exception as e:
            error_msg = f"Failed to save professor: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _assign_voice_to_professor(self, professor: Professor) -> None:
        """
        Assign a voice to a professor.

        Args:
            professor: Professor object to assign voice to
        """
        try:
            voice_id = self.audio_processor.get_voice_id_for_professor(professor)

            # Store the voice ID in the professor's voice settings
            if not professor.voice_settings:
                professor.voice_settings = {}
            professor.voice_settings["voice_id"] = voice_id

            self.logger.debug(
                f"Voice ID {voice_id} assigned to professor {professor.name}"
            )
        except Exception as e:
            error_msg = f"Failed to assign voice to professor: {str(e)}"
            self.logger.warning(error_msg)
            # Not raising an exception here as this is not critical

    def create_course(
        self,
        title: str,
        code: str,
        department: str,
        level: str = DEFAULT_COURSE_LEVEL,
        professor_id: Optional[str] = None,
        description: Optional[str] = None,
        weeks: int = DEFAULT_COURSE_WEEKS,
        lectures_per_week: int = DEFAULT_LECTURES_PER_WEEK,
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
        self.logger.info(f"Creating new course: {code} - {title}")

        # Get or create professor
        professor = self._get_or_create_professor(professor_id)

        # Generate description if not provided
        if not description:
            description = f"A {level} course on {title} in the {department} department."
            self.logger.debug(f"Generated description: {description}")

        # Create basic course
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
        self._generate_course_syllabus(course, professor)

        # Save to database
        try:
            course = self.repository.create_course(course)
            self.logger.info(f"Course created with ID: {course.id}")
            return course, professor
        except Exception as e:
            error_msg = f"Failed to save course: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _get_or_create_professor(self, professor_id: Optional[str] = None) -> Professor:
        """
        Get an existing professor by ID or create a new one.

        Args:
            professor_id: ID of the professor to retrieve (optional)

        Returns:
            Professor: The retrieved or created professor

        Raises:
            ProfessorNotFoundError: If professor_id is provided but not found
        """
        if professor_id:
            self.logger.debug(f"Retrieving professor with ID: {professor_id}")
            professor = self.repository.get_professor(professor_id)
            if not professor:
                error_msg = f"Professor with ID {professor_id} not found"
                self.logger.error(error_msg)
                raise ProfessorNotFoundError(error_msg)
            return professor
        else:
            self.logger.debug("No professor ID provided, creating new professor")
            return self.create_professor()

    def _generate_course_syllabus(self, course: Course, professor: Professor) -> None:
        """
        Generate a syllabus for a course.

        Args:
            course: Course object
            professor: Professor object
        """
        try:
            self.logger.debug(f"Generating syllabus for course {course.code}")
            syllabus = self.content_generator.create_course_syllabus(course, professor)
            course.syllabus = syllabus
            self.logger.debug("Syllabus generation completed")
        except Exception as e:
            error_msg = f"Failed to generate syllabus: {str(e)}"
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg) from e

    def generate_lecture(
        self,
        course_code: str,
        week: int,
        number: int = 1,
        topic: Optional[str] = None,
        word_count: int = DEFAULT_LECTURE_WORD_COUNT,
    ) -> Tuple[Lecture, Course, Professor]:
        """
        Generate a lecture for a specific course and week.

        Args:
            course_code: Course code
            week: Week number
            number: Lecture number within the week
            topic: Lecture topic (if None, will be derived from syllabus)
            word_count: Word count for the lecture

        Returns:
            Tuple: (Lecture, Course, Professor) - The generated lecture with its course and professor
        """
        self.logger.info(
            f"Generating lecture for course {course_code}, week {week}, number {number}"
        )

        # Get course and professor
        course, professor = self._get_course_and_professor(course_code)

        # Get previous lecture for continuity if available
        previous_lecture = self._get_previous_lecture(course, week, number)

        # Determine topic
        lecture_topic = topic or RandomGenerators.generate_lecture_topic(week, number)
        self.logger.debug(f"Using topic: {lecture_topic}")

        # Generate lecture content
        lecture = self._create_lecture_content(
            course, professor, lecture_topic, week, number, previous_lecture, word_count
        )

        # Save lecture to database
        try:
            lecture = self.repository.create_lecture(lecture)
            self.logger.info(f"Lecture created with ID: {lecture.id}")
        except Exception as e:
            error_msg = f"Failed to save lecture: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

        # Export lecture text to file
        self.export_lecture_text(lecture, course, professor)

        return lecture, course, professor

    def _get_course_and_professor(self, course_code: str) -> Tuple[Course, Professor]:
        """
        Get course and professor objects by course code.

        Args:
            course_code: The course code to look up

        Returns:
            Tuple[Course, Professor]: The course and professor objects

        Raises:
            CourseNotFoundError: If course not found
            ProfessorNotFoundError: If professor not found
        """
        # Get course
        course = self.repository.get_course_by_code(course_code)
        if not course:
            error_msg = f"Course with code {course_code} not found"
            self.logger.error(error_msg)
            raise CourseNotFoundError(error_msg)

        # Get professor
        professor = self.repository.get_professor(course.professor_id)
        if not professor:
            error_msg = f"Professor with ID {course.professor_id} not found"
            self.logger.error(error_msg)
            raise ProfessorNotFoundError(error_msg)

        return course, professor

    def _get_previous_lecture(
        self, course: Course, week: int, number: int
    ) -> Optional[Lecture]:
        """
        Get previous lecture for continuity if available.

        Args:
            course: Course object
            week: Current week number
            number: Current lecture number

        Returns:
            Optional[Lecture]: Previous lecture if available, None otherwise
        """
        if week <= 1 and number <= 1:
            return None

        prev_week = week
        prev_number = number - 1

        if prev_number < 1:
            prev_week -= 1
            prev_number = course.lectures_per_week

        try:
            previous_lecture = self.repository.get_lecture_by_course_week_order(
                course_id=course.id, week_number=prev_week, order_in_week=prev_number
            )
            if previous_lecture:
                self.logger.debug(
                    f"Found previous lecture from week {prev_week}, number {prev_number}"
                )
            return previous_lecture
        except Exception as e:
            self.logger.warning(
                f"Failed to retrieve previous lecture: {str(e)}. Continuing without previous content."
            )
            return None

    def _create_lecture_content(
        self,
        course: Course,
        professor: Professor,
        topic: str,
        week_number: int,
        order_in_week: int,
        previous_lecture: Optional[Lecture] = None,
        word_count: int = DEFAULT_LECTURE_WORD_COUNT,
    ) -> Lecture:
        """
        Generate lecture content using the content generator.

        Args:
            course: Course object
            professor: Professor object
            topic: Lecture topic
            week_number: Week number in the course
            order_in_week: Order of this lecture within the week
            previous_lecture: Optional previous lecture for continuity
            word_count: Target word count for the lecture

        Returns:
            Lecture: Generated lecture object

        Raises:
            ContentGenerationError: If lecture generation fails
        """
        previous_content = previous_lecture.content if previous_lecture else None

        try:
            # Use cached lecture generation if enabled for Anthropic
            if self.enable_caching and self.content_backend == "anthropic":
                self.logger.info(
                    f"Generating lecture for {course.code} Week {week_number}, Lecture {order_in_week} with caching"
                )
                lecture, cache_metrics = (
                    self.content_generator.create_lecture_with_caching(
                        course=course,
                        professor=professor,
                        topic=topic,
                        week_number=week_number,
                        order_in_week=order_in_week,
                        previous_lecture_content=previous_content,
                        word_count=word_count,
                    )
                )

                # Log cache metrics
                if cache_metrics.get("cached", False):
                    self.logger.info(
                        f"Cache metrics - Tokens saved: {cache_metrics.get('estimated_tokens_saved', 0)}, "
                        f"Response time: {cache_metrics.get('response_time_seconds', 0):.2f}s"
                    )
            else:
                # Use standard generation without caching
                self.logger.info(
                    f"Generating lecture for {course.code} Week {week_number}, Lecture {order_in_week}"
                )
                lecture = self.content_generator.create_lecture(
                    course=course,
                    professor=professor,
                    topic=topic,
                    week_number=week_number,
                    order_in_week=order_in_week,
                    previous_lecture_content=previous_content,
                    word_count=word_count,
                )

            # The lecture returned from create_lecture doesn't have an ID yet
            # We'll store it in the database and get an ID
            return lecture

        except Exception as e:
            error_msg = f"Failed to generate lecture content: {str(e)}"
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg) from e

    def export_lecture_text(
        self, lecture: Lecture, course: Course, professor: Professor
    ) -> str:
        """
        Export lecture content to a text file.

        Args:
            lecture: The lecture object
            course: The course object
            professor: The professor object

        Returns:
            str: Path to the exported text file
        """
        self.logger.info(
            f"Exporting lecture text for {course.code} W{lecture.week_number} L{lecture.order_in_week}"
        )

        # Create a filename based on course code, week, and lecture number
        filename = f"{course.code}_W{lecture.week_number}_L{lecture.order_in_week}.md"

        # Create a folder for the course if it doesn't exist
        course_folder = Path(self.text_export_path) / course.code
        course_folder.mkdir(exist_ok=True)

        # Full path to the text file
        file_path = course_folder / filename

        try:
            # Create header metadata
            header = self._generate_lecture_file_header(lecture, course, professor)

            # Write the content to the file
            with open(file_path, "w") as f:
                f.write(header + lecture.content)

            self.logger.info(f"Lecture text exported to {file_path}")
            return str(file_path)
        except Exception as e:
            error_msg = f"Failed to export lecture text: {str(e)}"
            self.logger.error(error_msg)
            # Continue despite error, just log it
            return ""

    def _generate_lecture_file_header(
        self, lecture: Lecture, course: Course, professor: Professor
    ) -> str:
        """
        Generate the header for the lecture file.

        Args:
            lecture: Lecture object
            course: Course object
            professor: Professor object

        Returns:
            str: Formatted header text
        """
        return f"""# {lecture.title}
        
## Course: {course.title} ({course.code})
## Professor: {professor.name}
## Week: {lecture.week_number}, Lecture: {lecture.order_in_week}
## Generated with: {self.content_backend}{f" ({self.content_model})" if self.content_model else ""}
## Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""

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
        self.logger.info(
            f"Creating audio for course {course_code}, week {week}, number {number}"
        )

        # Get course, lecture, and professor
        course, lecture, professor = self._get_course_lecture_professor(
            course_code, week, number
        )

        # Generate audio
        try:
            audio_path, _ = self.audio_processor.text_to_speech(lecture, professor)
            self.logger.info(f"Audio generated at {audio_path}")
        except Exception as e:
            error_msg = f"Failed to generate audio: {str(e)}"
            self.logger.error(error_msg)
            raise AudioProcessingError(error_msg) from e

        # Update lecture with audio path
        try:
            lecture = self.repository.update_lecture_audio(lecture.id, audio_path)
            self.logger.debug(f"Lecture updated with audio path: {audio_path}")
        except Exception as e:
            error_msg = f"Failed to update lecture with audio path: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

        return audio_path, lecture

    def _get_course_lecture_professor(
        self, course_code: str, week: int, number: int
    ) -> Tuple[Course, Lecture, Professor]:
        """
        Get course, lecture, and professor objects for audio generation.

        Args:
            course_code: Course code
            week: Week number
            number: Lecture number

        Returns:
            Tuple[Course, Lecture, Professor]: Course, lecture, and professor objects

        Raises:
            CourseNotFoundError: If course not found
            LectureNotFoundError: If lecture not found
            ProfessorNotFoundError: If professor not found
        """
        # Get course
        course = self.repository.get_course_by_code(course_code)
        if not course:
            error_msg = f"Course with code {course_code} not found"
            self.logger.error(error_msg)
            raise CourseNotFoundError(error_msg)

        # Get lecture
        lecture = self.repository.get_lecture_by_course_week_order(
            course_id=course.id, week_number=week, order_in_week=number
        )
        if not lecture:
            error_msg = f"Lecture for course {course_code}, week {week}, number {number} not found"
            self.logger.error(error_msg)
            raise LectureNotFoundError(error_msg)

        # Get professor
        professor = self.repository.get_professor(course.professor_id)
        if not professor:
            error_msg = f"Professor with ID {course.professor_id} not found"
            self.logger.error(error_msg)
            raise ProfessorNotFoundError(error_msg)

        return course, lecture, professor

    def list_departments(self) -> List[Department]:
        """
        List all departments.

        Returns:
            List[Department]: List of departments
        """
        self.logger.debug("Listing departments")

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
        self.logger.info(
            f"Listing courses{f' for department {department}' if department else ''}"
        )

        try:
            courses = self.repository.list_courses(department)
            result = []

            for course in courses:
                professor = self.repository.get_professor(course.professor_id)
                result.append({"course": course, "professor": professor})

            self.logger.debug(f"Found {len(result)} courses")
            return result
        except Exception as e:
            error_msg = f"Failed to list courses: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def get_sample_lecture(self) -> str:
        """
        Get sample lecture content for testing.

        Returns:
            str: Sample lecture content
        """
        self.logger.debug("Retrieving sample lecture content")

        # In a real implementation, this would load from a file or generate dynamically
        sample_path = Path(__file__).parent.parent / "samples" / "sample_lecture.md"

        if sample_path.exists():
            try:
                with open(sample_path, "r") as f:
                    content = f.read()
                    self.logger.debug(f"Sample lecture loaded from {sample_path}")
                    return content
            except Exception as e:
                self.logger.warning(f"Failed to load sample lecture: {str(e)}")
                # Fall through to placeholder
        else:
            self.logger.warning(f"Sample lecture file not found at {sample_path}")

        # Placeholder if file doesn't exist or can't be read
        return """
        # Introduction to Neural Networks
        
        *[Professor enters the lecture hall]*
        
        Good morning, everyone. Today we'll be discussing the fundamentals of neural networks...
        
        *[The rest of the lecture would go here]*
        """

    def get_lecture_preview(
        self, course_code: str = None, model_filter: str = None, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get a preview of lectures with relevant metadata.

        Args:
            course_code: Optional course code to filter lectures
            model_filter: Optional filter to only show lectures from a specific model (e.g., "tinyllama")
            limit: Maximum number of lectures to return

        Returns:
            List of dictionaries containing lecture info
        """
        self.logger.info(
            f"Getting lecture previews"
            f"{f' for course {course_code}' if course_code else ''}"
            f"{f' with model filter {model_filter}' if model_filter else ''}"
        )

        # Get all lectures
        lectures = []

        try:
            courses_info = self.repository.list_courses()

            for course_info in courses_info:
                # Handle either format - dict with "course" key or direct Course object
                if isinstance(course_info, dict) and "course" in course_info:
                    course = course_info["course"]
                else:
                    course = course_info  # Assume it's a Course object directly

                # Skip if filtering by course code and this isn't the right course
                if course_code and course.code != course_code:
                    continue

                lectures.extend(self._get_lectures_for_course(course, model_filter))

            # Sort by most recent first
            lectures.sort(key=lambda x: x.get("generated_at", ""), reverse=True)

            # Limit the results
            return lectures[:limit]
        except Exception as e:
            error_msg = f"Failed to get lecture previews: {str(e)}"
            self.logger.error(error_msg)
            raise DatabaseError(error_msg) from e

    def _get_lectures_for_course(
        self, course: Course, model_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get lecture previews for a specific course.

        Args:
            course: Course object
            model_filter: Optional model filter

        Returns:
            List[Dict[str, Any]]: List of lecture preview dictionaries
        """
        lectures = []

        try:
            professor = self.repository.get_professor(course.professor_id)
            if not professor:
                self.logger.warning(
                    f"Professor not found for course {course.code}, skipping"
                )
                return []

            course_lectures = self.repository.list_lectures_by_course(course.id)

            for lecture in course_lectures:
                # Get model information and skip if it doesn't match the filter
                model_used = self._get_lecture_model_info(course.code, lecture)
                if model_filter and (
                    not model_used or model_filter.lower() not in model_used.lower()
                ):
                    continue

                # Construct lecture preview
                lecture_path = self.get_lecture_export_path(
                    course.code, lecture.week_number, lecture.order_in_week
                )

                lectures.append(
                    {
                        "id": lecture.id,
                        "title": lecture.title,
                        "course_code": course.code,
                        "course_title": course.title,
                        "professor": professor.name,
                        "week": lecture.week_number,
                        "lecture_number": lecture.order_in_week,
                        "content_preview": (
                            lecture.content[:200] + "..." if lecture.content else None
                        ),
                        "generated_at": lecture.generated_at,
                        "model_used": model_used,
                        "text_file": (
                            lecture_path if os.path.exists(lecture_path) else None
                        ),
                        "audio_path": lecture.audio_path,
                    }
                )

            return lectures
        except Exception as e:
            self.logger.warning(
                f"Error getting lectures for course {course.code}: {str(e)}"
            )
            return []

    def _get_lecture_model_info(
        self, course_code: str, lecture: Lecture
    ) -> Optional[str]:
        """
        Extract model information from a lecture file.

        Args:
            course_code: Course code
            lecture: Lecture object

        Returns:
            Optional[str]: Model information if found, None otherwise
        """
        lecture_path = self.get_lecture_export_path(
            course_code, lecture.week_number, lecture.order_in_week
        )

        if not os.path.exists(lecture_path):
            return None

        try:
            with open(lecture_path, "r") as f:
                content = f.read()
                # Look for the model info in the header
                model_lines = [l for l in content.split("\n") if "Generated with:" in l]
                if model_lines:
                    return model_lines[0].replace("## Generated with:", "").strip()
        except Exception as e:
            self.logger.warning(f"Failed to read lecture file {lecture_path}: {str(e)}")

        return None

    def get_lecture_export_path(self, course_code: str, week: int, number: int) -> str:
        """
        Get the path to the exported lecture file.

        Args:
            course_code: Course code
            week: Week number
            number: Lecture number

        Returns:
            str: Path to the exported text file
        """
        filename = f"{course_code}_W{week}_L{number}.md"
        return str(Path(self.text_export_path) / course_code / filename)

    def create_lecture_series(
        self,
        course_code: str,
        topics: List[str],
        starting_week: int = 1,
        word_count: int = DEFAULT_LECTURE_WORD_COUNT,
    ) -> List[Lecture]:
        """
        Generate a series of related lectures for a course using prompt caching.

        This method creates multiple lectures in sequence, maintaining the professor's
        voice and teaching style across all lectures, while building continuity
        between the content. This is more efficient than creating lectures one-by-one
        as it leverages prompt caching for reduced token usage.

        Args:
            course_code: Code for the course to create lectures for
            topics: List of lecture topics in sequence
            starting_week: Week number to start from (default: 1)
            word_count: Target word count for each lecture (default: DEFAULT_LECTURE_WORD_COUNT)

        Returns:
            List of Lecture objects

        Raises:
            CourseNotFoundError: If the course is not found
            ContentGenerationError: If lecture generation fails
        """
        # Find the course
        course = self.repository.get_course_by_code(course_code)
        if not course:
            raise CourseNotFoundError(f"Course {course_code} not found")

        # Find the professor assigned to the course
        professor = self.repository.get_professor(course.professor_id)
        if not professor:
            raise ProfessorNotFoundError(
                f"Professor for course {course_code} not found"
            )

        try:
            # Check if we can use caching
            if self.enable_caching and self.content_backend == "anthropic":
                self.logger.info(
                    f"Generating lecture series for {course.code} with {len(topics)} lectures using caching"
                )

                # Use the lecture series caching method
                lecture_results = (
                    self.content_generator.create_lecture_series_with_caching(
                        course=course,
                        professor=professor,
                        topics=topics,
                        starting_week=starting_week,
                        word_count=word_count,
                    )
                )

                # Store lectures in the database
                lectures = []
                total_tokens_saved = 0

                for lecture_tuple in lecture_results:
                    lecture, metrics = lecture_tuple

                    # Save the lecture to the database
                    lecture_id = self.repository.add_lecture(lecture)
                    lecture.id = lecture_id
                    lectures.append(lecture)

                    # Track token savings
                    total_tokens_saved += metrics.get("estimated_tokens_saved", 0)

                # Log total savings
                if total_tokens_saved > 0:
                    self.logger.info(
                        f"Total tokens saved across series: {total_tokens_saved}"
                    )

                return lectures

            else:
                # Use individual lecture creation if caching is not available
                self.logger.info(
                    f"Generating lecture series for {course.code} without caching (not using Anthropic or caching disabled)"
                )

                lectures = []
                previous_lecture = None

                for i, topic in enumerate(topics):
                    week_number = starting_week + (i // course.lectures_per_week)
                    order_in_week = (i % course.lectures_per_week) + 1

                    # Create the lecture
                    lecture = self._create_lecture_content(
                        course=course,
                        professor=professor,
                        topic=topic,
                        week_number=week_number,
                        order_in_week=order_in_week,
                        previous_lecture=previous_lecture,
                        word_count=word_count,
                    )

                    # Save the lecture to the database
                    lecture_id = self.repository.add_lecture(lecture)
                    lecture.id = lecture_id
                    lectures.append(lecture)

                    # Update previous lecture for the next iteration
                    previous_lecture = lecture

                return lectures

        except Exception as e:
            error_msg = f"Failed to generate lecture series: {str(e)}"
            self.logger.error(error_msg)
            raise ContentGenerationError(error_msg) from e
