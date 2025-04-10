"""
Centralized configuration management for ArtificialU.
Uses Pydantic's BaseSettings for robust environment variable handling with validation.
"""

import os
import sys
import logging
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Union
from pydantic import AnyHttpUrl, Field, field_validator, model_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

from artificial_u.config.defaults import (
    DEFAULT_DB_URL,
    DEFAULT_AUDIO_PATH,
    DEFAULT_TEXT_EXPORT_PATH,
    DEFAULT_CONTENT_BACKEND,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_LOG_LEVEL,
    DEFAULT_STORAGE_TYPE,
    DEFAULT_STORAGE_ENDPOINT_URL,
    DEFAULT_STORAGE_PUBLIC_URL,
    DEFAULT_STORAGE_ACCESS_KEY,
    DEFAULT_STORAGE_SECRET_KEY,
    DEFAULT_STORAGE_REGION,
    DEFAULT_STORAGE_AUDIO_BUCKET,
    DEFAULT_STORAGE_LECTURES_BUCKET,
    DEFAULT_STORAGE_IMAGES_BUCKET,
)


class Environment(str, Enum):
    """Application environment types"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Unified configuration settings for ArtificialU.
    Handles environment variables, defaults, validation, and utility functions.
    """

    # Environment identification
    environment: Environment = Environment.DEVELOPMENT
    testing: bool = Field(
        default=False, description="Flag indicating whether app is in test mode"
    )

    # API settings
    api_prefix: str = "/api/v1"
    debug: bool = False

    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:8000", "http://localhost:3000"]
    )

    # Database settings
    DATABASE_URL: str = DEFAULT_DB_URL

    # Logging settings
    LOG_LEVEL: str = DEFAULT_LOG_LEVEL

    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Storage paths
    AUDIO_STORAGE_PATH: str = DEFAULT_AUDIO_PATH
    AUDIO_PATH: str = "audio"
    TEXT_EXPORT_PATH: str = DEFAULT_TEXT_EXPORT_PATH

    # Storage settings for S3/MinIO
    STORAGE_TYPE: str = DEFAULT_STORAGE_TYPE  # "minio" or "s3"
    STORAGE_ENDPOINT_URL: str = DEFAULT_STORAGE_ENDPOINT_URL
    STORAGE_PUBLIC_URL: str = DEFAULT_STORAGE_PUBLIC_URL
    STORAGE_ACCESS_KEY: str = DEFAULT_STORAGE_ACCESS_KEY
    STORAGE_SECRET_KEY: str = DEFAULT_STORAGE_SECRET_KEY
    STORAGE_REGION: str = DEFAULT_STORAGE_REGION
    STORAGE_AUDIO_BUCKET: str = DEFAULT_STORAGE_AUDIO_BUCKET
    STORAGE_LECTURES_BUCKET: str = DEFAULT_STORAGE_LECTURES_BUCKET
    STORAGE_IMAGES_BUCKET: str = DEFAULT_STORAGE_IMAGES_BUCKET

    # Content generation settings
    content_backend: str = DEFAULT_CONTENT_BACKEND
    content_model: Optional[str] = None
    enable_caching: bool = False
    cache_metrics: bool = True

    # Configure Pydantic to use .env files
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("content_model")
    @classmethod
    def set_default_model(cls, v, info):
        """Set default model based on backend if not provided"""
        if v is None:
            backend = info.data.get("content_backend")
            if backend == "ollama":
                return DEFAULT_OLLAMA_MODEL
        return v

    @model_validator(mode="after")
    def setup_environment(self) -> "Settings":
        """Set up environment-specific configurations"""
        # Detect test environment
        if self.is_test_environment():
            self.environment = Environment.TESTING
            self.testing = True
        elif os.environ.get("ENV") == "production":
            self.environment = Environment.PRODUCTION

        # Create storage directories
        self.create_directories()
        return self

    def is_test_environment(self) -> bool:
        """Check if running in a test environment"""
        return (
            os.environ.get("TESTING") == "true"
            or "pytest" in sys.modules
            or any(arg in sys.argv for arg in ["-m", "pytest", "test"])
        )

    def create_directories(self) -> None:
        """Create necessary directories for the application"""
        Path(self.AUDIO_STORAGE_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.TEXT_EXPORT_PATH).mkdir(parents=True, exist_ok=True)

    def setup_logging(self) -> logging.Logger:
        """Set up logging based on configuration"""
        numeric_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger("artificial_u")

    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as a dictionary"""
        return {
            "environment": self.environment,
            "db_url": self.DATABASE_URL,
            "content_backend": self.content_backend,
            "content_model": self.content_model,
            "enable_caching": self.enable_caching,
            "cache_metrics": self.cache_metrics,
            "audio_path": self.AUDIO_PATH,
            "audio_storage_path": self.AUDIO_STORAGE_PATH,
            "text_export_path": self.TEXT_EXPORT_PATH,
            "anthropic_api_key": self.ANTHROPIC_API_KEY,
            "elevenlabs_api_key": self.ELEVENLABS_API_KEY,
            "openai_api_key": self.OPENAI_API_KEY,
            "storage_type": self.STORAGE_TYPE,
            "storage_endpoint_url": self.STORAGE_ENDPOINT_URL,
            "storage_public_url": self.STORAGE_PUBLIC_URL,
            "storage_region": self.STORAGE_REGION,
            "storage_audio_bucket": self.STORAGE_AUDIO_BUCKET,
            "storage_lectures_bucket": self.STORAGE_LECTURES_BUCKET,
            "storage_images_bucket": self.STORAGE_IMAGES_BUCKET,
        }

    def log_configuration(self) -> None:
        """Log the current configuration"""
        logger = logging.getLogger("artificial_u")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Using database: {self.DATABASE_URL}")
        logger.info(f"Content backend: {self.content_backend}")
        if self.content_model:
            logger.info(f"Content model: {self.content_model}")
        logger.info(f"Caching enabled: {self.enable_caching}")
        logger.info(f"Audio storage path: {self.AUDIO_STORAGE_PATH}")
        logger.info(f"Audio path: {self.AUDIO_PATH}")
        logger.info(f"Text export path: {self.TEXT_EXPORT_PATH}")
        logger.info(f"Storage type: {self.STORAGE_TYPE}")
        if self.STORAGE_TYPE == "minio":
            logger.info(f"MinIO endpoint: {self.STORAGE_ENDPOINT_URL}")
            logger.info(f"MinIO public URL: {self.STORAGE_PUBLIC_URL}")


@lru_cache
def get_settings() -> Settings:
    """
    Create settings instance with environment-appropriate configuration.
    Uses caching for efficiency.
    """
    # Determine which .env file to load based on environment
    env_file = ".env"

    # Check if we're in a test environment
    if "pytest" in sys.modules or any(
        arg in sys.argv for arg in ["-m", "pytest", "test"]
    ):
        # For tests, prefer the test environment configuration
        if os.path.exists(".env.test"):
            env_file = ".env.test"
        os.environ["TESTING"] = "true"

    # Check for explicit environment override
    explicit_env = os.environ.get("ENV_FILE")
    if explicit_env and os.path.exists(explicit_env):
        env_file = explicit_env

    # Create settings with the appropriate env file
    settings = Settings(_env_file=env_file)

    # Initialize logging
    settings.setup_logging()

    # Log configuration details if not in test mode (to avoid cluttering test output)
    if not settings.testing:
        settings.log_configuration()

    return settings
