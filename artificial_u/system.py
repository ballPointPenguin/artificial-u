"""
Main system class for ArtificialU.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

from artificial_u.generators.factory import create_generator
from artificial_u.audio.processor import AudioProcessor
from artificial_u.models.database import Repository
from artificial_u.models.core import Professor, Course, Lecture, Department
from artificial_u.config.config_manager import ConfigManager
from artificial_u.services.professor_service import ProfessorService
from artificial_u.services.course_service import CourseService
from artificial_u.services.lecture_service import LectureService
from artificial_u.services.audio_service import AudioService
from artificial_u.utils.exceptions import ConfigurationError


class UniversitySystem:
    """
    Core system class for ArtificialU.
    Orchestrates services for content generation, audio processing, and data storage.
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None,
        db_path: Optional[str] = None,  # Deprecated, kept for backward compatibility
        db_url: Optional[str] = None,
        audio_path: Optional[str] = None,
        content_backend: Optional[str] = None,
        content_model: Optional[str] = None,
        text_export_path: Optional[str] = None,
        log_level: Optional[str] = None,
        enable_caching: Optional[bool] = None,
        cache_metrics: Optional[bool] = None,
    ):
        """
        Initialize the university system.

        Args:
            anthropic_api_key: API key for Anthropic
            elevenlabs_api_key: API key for ElevenLabs
            db_path: Deprecated, use db_url instead
            db_url: PostgreSQL database URL
            audio_path: Path to store audio files
            content_backend: Backend to use for content generation ('anthropic' or 'ollama')
            content_model: Model to use with the chosen backend
            text_export_path: Path to export lecture text files
            log_level: Logging level
            enable_caching: Whether to enable prompt caching
            cache_metrics: Whether to track cache metrics
        """
        # Initialize configuration manager
        self.config = ConfigManager(
            anthropic_api_key=anthropic_api_key,
            elevenlabs_api_key=elevenlabs_api_key,
            db_url=db_url,
            audio_path=audio_path,
            content_backend=content_backend,
            content_model=content_model,
            text_export_path=text_export_path,
            log_level=log_level,
            enable_caching=enable_caching,
            cache_metrics=cache_metrics,
        )

        # Get logger
        self.logger = logging.getLogger(__name__)

        # Initialize core components
        self._init_core_components()

        # Initialize services
        self._init_services()

        self.logger.info("University system initialized")

    def _init_core_components(self):
        """Initialize core system components."""
        try:
            # Initialize content generator
            config = self.config.get_config_dict()
            backend_kwargs = {}

            if config["content_backend"] == "anthropic":
                backend_kwargs["api_key"] = config["anthropic_api_key"]
                backend_kwargs["enable_caching"] = config["enable_caching"]
                backend_kwargs["cache_metrics"] = config["cache_metrics"]
            elif config["content_backend"] == "ollama":
                backend_kwargs["model"] = config["content_model"]

            self.content_generator = create_generator(
                backend=config["content_backend"], **backend_kwargs
            )

            # Initialize audio processor
            self.audio_processor = AudioProcessor(api_key=config["elevenlabs_api_key"])

            # Initialize repository
            self.repository = Repository(db_url=config["db_url"])

        except Exception as e:
            self.logger.error(f"Failed to initialize core components: {str(e)}")
            raise ConfigurationError(f"System initialization failed: {str(e)}") from e

    def _init_services(self):
        """Initialize service layer components."""
        config = self.config.get_config_dict()

        # Initialize professor service
        self.professor_service = ProfessorService(
            repository=self.repository,
            content_generator=self.content_generator,
            audio_processor=self.audio_processor,
            logger=logging.getLogger("artificial_u.services.professor_service"),
        )

        # Initialize course service
        self.course_service = CourseService(
            repository=self.repository,
            content_generator=self.content_generator,
            professor_service=self.professor_service,
            logger=logging.getLogger("artificial_u.services.course_service"),
        )

        # Initialize lecture service
        self.lecture_service = LectureService(
            repository=self.repository,
            content_generator=self.content_generator,
            professor_service=self.professor_service,
            course_service=self.course_service,
            audio_processor=self.audio_processor,
            text_export_path=config["text_export_path"],
            content_backend=config["content_backend"],
            content_model=config["content_model"],
            enable_caching=config["enable_caching"],
            logger=logging.getLogger("artificial_u.services.lecture_service"),
        )

        # Initialize audio service
        self.audio_service = AudioService(
            audio_processor=self.audio_processor,
            repository=self.repository,
            logger=logging.getLogger("artificial_u.services.audio_service"),
        )

    # === Professor Methods ===

    def create_professor(self, **kwargs) -> Professor:
        """Create a new professor with the given attributes."""
        return self.professor_service.create_professor(**kwargs)

    # === Course Methods ===

    def create_course(self, **kwargs) -> Tuple[Course, Professor]:
        """Create a new course with syllabus."""
        return self.course_service.create_course(**kwargs)

    def list_departments(self) -> List[Department]:
        """List all departments."""
        return self.course_service.list_departments()

    def list_courses(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all courses with professor information."""
        return self.course_service.list_courses(department)

    # === Lecture Methods ===

    def generate_lecture(self, **kwargs) -> Tuple[Lecture, Course, Professor]:
        """Generate a lecture for a specific course and week."""
        return self.lecture_service.generate_lecture(**kwargs)

    def export_lecture_text(
        self, lecture: Lecture, course: Course, professor: Professor
    ) -> str:
        """Export lecture content to a text file."""
        return self.lecture_service.export_lecture_text(lecture, course, professor)

    def create_lecture_series(self, **kwargs) -> List[Lecture]:
        """Generate a series of related lectures for a course."""
        return self.lecture_service.create_lecture_series(**kwargs)

    def get_lecture_preview(self, **kwargs) -> List[Dict[str, Any]]:
        """Get a preview of lectures with relevant metadata."""
        return self.lecture_service.get_lecture_preview(**kwargs)

    def get_lecture_export_path(self, course_code: str, week: int, number: int) -> str:
        """Get the path to the exported lecture file."""
        return self.lecture_service.get_lecture_export_path(course_code, week, number)

    # === Audio Methods ===

    def create_lecture_audio(self, **kwargs) -> Tuple[str, Lecture]:
        """Create audio for a lecture."""
        return self.audio_service.create_lecture_audio(**kwargs)

    # === Other Methods ===

    def get_sample_lecture(self) -> str:
        """
        Get sample lecture content for testing.

        Returns:
            str: Sample lecture content
        """
        self.logger.debug("Retrieving sample lecture content")

        # Simple sample lecture content
        return """
        # Introduction to Neural Networks
        
        *[Professor enters the lecture hall]*
        
        Good morning, everyone. Today we'll be discussing the fundamentals of neural networks...
        
        *[The rest of the lecture would go here]*
        """
