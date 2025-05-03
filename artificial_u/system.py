"""
Main system class for ArtificialU.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from artificial_u.audio.speech_processor import SpeechProcessor
from artificial_u.config import get_settings
from artificial_u.generators.factory import create_generator
from artificial_u.integrations.elevenlabs.client import ElevenLabsClient
from artificial_u.integrations.elevenlabs.voice_mapper import VoiceMapper
from artificial_u.models.core import Course, Department, Lecture, Professor
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services.audio_service import AudioService
from artificial_u.services.content_service import ContentService
from artificial_u.services.course_service import CourseService
from artificial_u.services.image_service import ImageService
from artificial_u.services.lecture_service import LectureService
from artificial_u.services.professor_service import ProfessorService
from artificial_u.services.storage_service import StorageService
from artificial_u.services.tts_service import TTSService
from artificial_u.services.voice_service import VoiceService
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
        google_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        db_url: Optional[str] = None,
        content_backend: Optional[str] = None,
        content_model: Optional[str] = None,
        log_level: Optional[str] = None,
        storage_type: Optional[str] = None,
        storage_endpoint_url: Optional[str] = None,
        storage_public_url: Optional[str] = None,
    ):
        """
        Initialize the university system.

        Args:
            anthropic_api_key: API key for Anthropic
            elevenlabs_api_key: API key for ElevenLabs
            google_api_key: API key for Google
            openai_api_key: API key for OpenAI
            db_url: PostgreSQL database URL
            content_backend: Backend to use for content generation ('anthropic' or 'ollama')
            content_model: Model to use with the chosen backend
            log_level: Logging level
            storage_type: Storage type ('minio' or 's3')
            storage_endpoint_url: URL for MinIO/S3 endpoint
            storage_public_url: Public URL for MinIO
        """
        # Initialize settings
        self.settings = get_settings()

        # Configure all settings
        self._configure_api_keys(
            anthropic_api_key, elevenlabs_api_key, google_api_key, openai_api_key
        )
        self._configure_database(db_url)
        self._configure_content(content_backend, content_model)
        self._configure_storage(storage_type, storage_endpoint_url, storage_public_url)

        # Set log level if provided
        if log_level:
            self.settings.LOG_LEVEL = log_level

        # Get logger
        self.logger = logging.getLogger(__name__)

        # Initialize core components
        self._init_core_components()

        # Initialize services
        self._init_services()

        self.logger.info("University system initialized")

    def _configure_api_keys(
        self,
        anthropic_api_key: Optional[str],
        elevenlabs_api_key: Optional[str],
        google_api_key: Optional[str],
        openai_api_key: Optional[str],
    ):
        """Configure API keys"""
        if anthropic_api_key:
            self.settings.ANTHROPIC_API_KEY = anthropic_api_key
        if elevenlabs_api_key:
            self.settings.ELEVENLABS_API_KEY = elevenlabs_api_key
        if google_api_key:
            self.settings.GOOGLE_API_KEY = google_api_key
        if openai_api_key:
            self.settings.OPENAI_API_KEY = openai_api_key

    def _configure_database(self, db_url: Optional[str]):
        """Configure database settings"""
        if db_url:
            self.settings.DATABASE_URL = db_url

    def _configure_content(
        self,
        content_backend: Optional[str],
        content_model: Optional[str],
    ):
        """Configure content generation settings"""
        if content_backend:
            self.settings.content_backend = content_backend
        if content_model:
            self.settings.content_model = content_model

    def _configure_storage(
        self,
        storage_type: Optional[str],
        storage_endpoint_url: Optional[str],
        storage_public_url: Optional[str],
    ):
        """Configure storage settings"""
        if storage_type:
            self.settings.STORAGE_TYPE = storage_type
        if storage_endpoint_url:
            self.settings.STORAGE_ENDPOINT_URL = storage_endpoint_url
        if storage_public_url:
            self.settings.STORAGE_PUBLIC_URL = storage_public_url

    def _init_core_components(self):
        """Initialize core system components."""
        try:
            # Initialize content generator
            backend_kwargs = {}

            if self.settings.content_backend == "anthropic":
                backend_kwargs["api_key"] = self.settings.ANTHROPIC_API_KEY
            elif self.settings.content_backend == "ollama":
                backend_kwargs["model"] = self.settings.content_model

            self.content_generator = create_generator(
                backend=self.settings.content_backend, **backend_kwargs
            )

            # Initialize repository factory directly
            self.repository_factory = RepositoryFactory(db_url=self.settings.DATABASE_URL)

            # Initialize audio components
            self.elevenlabs_client = ElevenLabsClient(api_key=self.settings.ELEVENLABS_API_KEY)
            self.speech_processor = SpeechProcessor()

            # Initialize voice mapper
            self.voice_mapper = VoiceMapper(
                logger=logging.getLogger("artificial_u.integrations.elevenlabs.voice_mapper")
            )

            # Initialize storage service
            self.storage_service = StorageService(
                logger=logging.getLogger("artificial_u.services.storage_service")
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize core components: {str(e)}")
            raise ConfigurationError(f"System initialization failed: {str(e)}") from e

    def _init_services(self):
        """Initialize service layer components."""
        # --- Instantiate services needed by others first ---

        # Initialize ContentService (assuming it configures itself from settings)
        self.content_service = ContentService(
            logger=logging.getLogger("artificial_u.services.content_service")
        )

        # Initialize ImageService
        self.image_service = ImageService(storage_service=self.storage_service)

        # Initialize TTS service
        self.tts_service = TTSService(
            api_key=self.settings.ELEVENLABS_API_KEY,
            audio_path=self.settings.TEMP_AUDIO_PATH,
            client=self.elevenlabs_client,
            speech_processor=self.speech_processor,
            repository_factory=self.repository_factory,
            logger=logging.getLogger("artificial_u.services.tts_service"),
        )

        # --- Instantiate services that depend on the above ---

        # Initialize VoiceService
        self.voice_service = VoiceService(
            repository_factory=self.repository_factory,
            client=self.elevenlabs_client,
            logger=logging.getLogger("artificial_u.services.voice_service"),
        )

        # Initialize ProfessorService
        self.professor_service = ProfessorService(
            repository_factory=self.repository_factory,
            content_service=self.content_service,
            image_service=self.image_service,
            voice_service=self.voice_service,
            logger=logging.getLogger("artificial_u.services.professor_service"),
        )

        # Initialize CourseService
        self.course_service = CourseService(
            repository_factory=self.repository_factory,
            professor_service=self.professor_service,
            content_service=self.content_service,
            logger=logging.getLogger("artificial_u.services.course_service"),
        )

        # Initialize LectureService
        self.lecture_service = LectureService(
            repository_factory=self.repository_factory,
            content_generator=self.content_generator,  # Still using this for now
            professor_service=self.professor_service,
            course_service=self.course_service,
            storage_service=self.storage_service,
            logger=logging.getLogger("artificial_u.services.lecture_service"),
        )

        # Initialize AudioService
        self.audio_service = AudioService(
            repository_factory=self.repository_factory,
            api_key=self.settings.ELEVENLABS_API_KEY,
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
        """Create a new course with topics."""
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
        return await self.lecture_service.export_lecture_text(lecture, course, professor)

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

    def test_audio_connection(self) -> Dict[str, Any]:
        """Test connection to the TTS service."""
        return self.audio_service.test_tts_connection()

    async def play_audio(self, audio_data_or_path):
        """Play audio from data or file path."""
        await self.audio_service.play_audio(audio_data_or_path)

    # === Voice Methods ===

    def list_available_voices(self, **kwargs) -> List[Dict[str, Any]]:
        """List available voices with optional filtering."""
        return self.voice_service.list_available_voices(**kwargs)

    def select_voice_for_professor(self, professor: Professor, **kwargs) -> Dict[str, Any]:
        """Select a voice for a professor."""
        return self.voice_service.select_voice_for_professor(professor, **kwargs)

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
