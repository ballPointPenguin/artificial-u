"""
Main system class for ArtificialU.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any

from artificial_u.generators.factory import create_generator
from artificial_u.models.database import Repository
from artificial_u.models.core import Professor, Course, Lecture, Department
from artificial_u.config.config_manager import ConfigManager
from artificial_u.services.professor_service import ProfessorService
from artificial_u.services.course_service import CourseService
from artificial_u.services.lecture_service import LectureService
from artificial_u.services.audio_service import AudioService
from artificial_u.services.voice_service import VoiceService
from artificial_u.services.tts_service import TTSService
from artificial_u.services.storage_service import StorageService
from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.audio.speech_processor import SpeechProcessor
from artificial_u.audio.audio_utils import AudioUtils
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
        db_url: Optional[str] = None,
        content_backend: Optional[str] = None,
        content_model: Optional[str] = None,
        log_level: Optional[str] = None,
        enable_caching: Optional[bool] = None,
        cache_metrics: Optional[bool] = None,
        storage_type: Optional[str] = None,
        storage_endpoint_url: Optional[str] = None,
        storage_public_url: Optional[str] = None,
    ):
        """
        Initialize the university system.

        Args:
            anthropic_api_key: API key for Anthropic
            elevenlabs_api_key: API key for ElevenLabs
            db_url: PostgreSQL database URL
            content_backend: Backend to use for content generation ('anthropic' or 'ollama')
            content_model: Model to use with the chosen backend
            log_level: Logging level
            enable_caching: Whether to enable prompt caching
            cache_metrics: Whether to track cache metrics
            storage_type: Storage type ('minio' or 's3')
            storage_endpoint_url: URL for MinIO/S3 endpoint
            storage_public_url: Public URL for MinIO
        """
        # Initialize configuration manager
        self.config = ConfigManager(
            anthropic_api_key=anthropic_api_key,
            elevenlabs_api_key=elevenlabs_api_key,
            db_url=db_url,
            content_backend=content_backend,
            content_model=content_model,
            log_level=log_level,
            enable_caching=enable_caching,
            cache_metrics=cache_metrics,
            storage_type=storage_type,
            storage_endpoint_url=storage_endpoint_url,
            storage_public_url=storage_public_url,
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

            # Initialize repository
            self.repository = Repository(db_url=config["db_url"])

            # Initialize audio components
            self.elevenlabs_client = ElevenLabsClient(
                api_key=config["elevenlabs_api_key"]
            )
            self.speech_processor = SpeechProcessor()
            self.audio_utils = AudioUtils(base_audio_path=config["temp_audio_path"])

            # Initialize storage service
            self.storage_service = StorageService(
                logger=logging.getLogger("artificial_u.services.storage_service")
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize core components: {str(e)}")
            raise ConfigurationError(f"System initialization failed: {str(e)}") from e

    def _init_services(self):
        """Initialize service layer components."""
        config = self.config.get_config_dict()

        # Initialize voice service
        self.voice_service = VoiceService(
            api_key=config["elevenlabs_api_key"],
            client=self.elevenlabs_client,
            logger=logging.getLogger("artificial_u.services.voice_service"),
        )

        # Initialize TTS service
        self.tts_service = TTSService(
            api_key=config["elevenlabs_api_key"],
            audio_path=config["temp_audio_path"],
            client=self.elevenlabs_client,
            speech_processor=self.speech_processor,
            audio_utils=self.audio_utils,
            logger=logging.getLogger("artificial_u.services.tts_service"),
        )

        # Initialize professor service
        self.professor_service = ProfessorService(
            repository=self.repository,
            content_generator=self.content_generator,
            voice_service=self.voice_service,
            elevenlabs_api_key=config["elevenlabs_api_key"],
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
            audio_processor=None,  # No longer used
            text_export_path=None,  # No longer used for persistent export
            content_backend=config["content_backend"],
            content_model=config["content_model"],
            enable_caching=config["enable_caching"],
            storage_service=self.storage_service,
            logger=logging.getLogger("artificial_u.services.lecture_service"),
        )

        # Initialize audio service
        self.audio_service = AudioService(
            repository=self.repository,
            api_key=config["elevenlabs_api_key"],
            voice_service=self.voice_service,
            tts_service=self.tts_service,
            storage_service=self.storage_service,
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

    async def export_lecture_text(
        self, lecture: Lecture, course: Course, professor: Professor
    ) -> str:
        """Export lecture content to a text file in storage."""
        return await self.lecture_service.export_lecture_text(
            lecture, course, professor
        )

    def create_lecture_series(self, **kwargs) -> List[Lecture]:
        """Generate a series of related lectures for a course."""
        return self.lecture_service.create_lecture_series(**kwargs)

    def get_lecture_preview(self, **kwargs) -> List[Dict[str, Any]]:
        """Get a preview of lectures with relevant metadata."""
        return self.lecture_service.get_lecture_preview(**kwargs)

    def get_lecture_export_path(self, course_code: str, week: int, number: int) -> str:
        """Get the storage URL for the exported lecture file."""
        return self.lecture_service.get_lecture_export_path(course_code, week, number)

    # === Audio Methods ===

    async def create_lecture_audio(self, **kwargs) -> Tuple[str, Lecture]:
        """Create audio for a lecture."""
        return await self.audio_service.create_lecture_audio(**kwargs)

    def list_available_voices(self, **kwargs) -> List[Dict[str, Any]]:
        """List available voices with optional filtering."""
        return self.audio_service.list_available_voices(**kwargs)

    def test_audio_connection(self) -> Dict[str, Any]:
        """Test connection to the TTS service."""
        return self.audio_service.test_tts_connection()

    async def play_audio(self, audio_data_or_path):
        """Play audio from data or file path."""
        await self.audio_service.play_audio(audio_data_or_path)

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
