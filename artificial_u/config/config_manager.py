"""
Configuration management for ArtificialU.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from artificial_u.config.defaults import (
    DEFAULT_DB_URL,
    DEFAULT_AUDIO_PATH,
    DEFAULT_TEXT_EXPORT_PATH,
    DEFAULT_CONTENT_BACKEND,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_LOG_LEVEL,
)

# Default caching settings
DEFAULT_ENABLE_CACHING = False
DEFAULT_CACHE_METRICS = True


class ConfigManager:
    """
    Centralized configuration management for ArtificialU.
    Handles environment variables, defaults, and configuration validation.
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None,
        db_url: Optional[str] = None,
        audio_path: Optional[str] = None,
        content_backend: str = DEFAULT_CONTENT_BACKEND,
        content_model: Optional[str] = None,
        text_export_path: Optional[str] = None,
        log_level: str = DEFAULT_LOG_LEVEL,
        enable_caching: bool = DEFAULT_ENABLE_CACHING,
        cache_metrics: bool = DEFAULT_CACHE_METRICS,
    ):
        """
        Initialize configuration manager.

        Args:
            anthropic_api_key: API key for Anthropic, uses ANTHROPIC_API_KEY env var if not provided
            elevenlabs_api_key: API key for ElevenLabs, uses ELEVENLABS_API_KEY env var if not provided
            db_url: Database URL, uses DATABASE_URL env var or default if not provided
            audio_path: Path to store audio files, uses AUDIO_PATH env var or default if not provided
            content_backend: Backend to use for content generation ('anthropic' or 'ollama')
            content_model: Model to use with the chosen backend (depends on backend)
            text_export_path: Path to export lecture text files, uses TEXT_EXPORT_PATH env var or default if not provided
            log_level: Logging level (INFO, DEBUG, etc.)
            enable_caching: Whether to enable prompt caching for Anthropic API calls
            cache_metrics: Whether to track cache metrics
        """
        self.logger = self._setup_logging(log_level)

        # API keys
        self.anthropic_api_key = anthropic_api_key or os.environ.get(
            "ANTHROPIC_API_KEY"
        )
        self.elevenlabs_api_key = elevenlabs_api_key or os.environ.get(
            "ELEVENLABS_API_KEY"
        )

        # Database configuration
        self.db_url = db_url or os.environ.get("DATABASE_URL", DEFAULT_DB_URL)

        # Content generation configuration
        self.content_backend = content_backend
        self.content_model = content_model or self._get_default_model(content_backend)
        self.enable_caching = enable_caching
        self.cache_metrics = cache_metrics

        # Paths
        self.audio_path = audio_path or os.environ.get("AUDIO_PATH", DEFAULT_AUDIO_PATH)
        self.text_export_path = text_export_path or os.environ.get(
            "TEXT_EXPORT_PATH", DEFAULT_TEXT_EXPORT_PATH
        )

        # Create necessary directories
        self._create_directories()

        # Log configuration
        self._log_configuration()

    def _setup_logging(self, log_level: str) -> logging.Logger:
        """
        Set up logging configuration.

        Args:
            log_level: Logging level string (INFO, DEBUG, etc.)

        Returns:
            Logger instance
        """
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger(__name__)

    def _get_default_model(self, backend: str) -> Optional[str]:
        """
        Get the default model for a given backend.

        Args:
            backend: Backend name

        Returns:
            Default model name for the backend or None
        """
        if backend == "ollama":
            return DEFAULT_OLLAMA_MODEL
        return None

    def _create_directories(self) -> None:
        """Create necessary directories for the application."""
        Path(self.audio_path).mkdir(parents=True, exist_ok=True)
        Path(self.text_export_path).mkdir(parents=True, exist_ok=True)

    def _log_configuration(self) -> None:
        """Log the current configuration."""
        self.logger.info(f"Using database: {self.db_url}")
        self.logger.info(f"Content backend: {self.content_backend}")
        if self.content_model:
            self.logger.info(f"Content model: {self.content_model}")
        self.logger.info(f"Caching enabled: {self.enable_caching}")
        self.logger.info(f"Audio path: {self.audio_path}")
        self.logger.info(f"Text export path: {self.text_export_path}")

    def get_config_dict(self) -> Dict[str, Any]:
        """
        Get configuration as a dictionary.

        Returns:
            Dictionary with configuration values
        """
        return {
            "db_url": self.db_url,
            "content_backend": self.content_backend,
            "content_model": self.content_model,
            "enable_caching": self.enable_caching,
            "cache_metrics": self.cache_metrics,
            "audio_path": self.audio_path,
            "text_export_path": self.text_export_path,
            "anthropic_api_key": self.anthropic_api_key,
            "elevenlabs_api_key": self.elevenlabs_api_key,
        }
