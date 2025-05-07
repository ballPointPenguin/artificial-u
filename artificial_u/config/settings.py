"""
Centralized configuration management for ArtificialU.

Uses Pydantic's BaseSettings for robust environment variable handling with validation.
"""

import logging
import os
import sys
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from artificial_u.config.defaults import (
    DEFAULT_CONTENT_BACKEND,
    DEFAULT_CONTENT_LOGS_PATH,
    DEFAULT_DB_URL,
    DEFAULT_LOG_LEVEL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_STORAGE_ACCESS_KEY,
    DEFAULT_STORAGE_AUDIO_BUCKET,
    DEFAULT_STORAGE_ENDPOINT_URL,
    DEFAULT_STORAGE_IMAGES_BUCKET,
    DEFAULT_STORAGE_LECTURES_BUCKET,
    DEFAULT_STORAGE_PUBLIC_URL,
    DEFAULT_STORAGE_REGION,
    DEFAULT_STORAGE_SECRET_KEY,
    DEFAULT_STORAGE_TYPE,
    DEFAULT_TEMP_AUDIO_PATH,
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
    testing: bool = Field(default=False, description="Flag indicating whether app is in test mode")

    # API settings
    api_prefix: str = "/api/v1"
    debug: bool = False

    # CORS settings
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:8000",
            "http://localhost:3000",
            "http://localhost:5173",
            "https://artificial-u.example.com",
            "https://*.artificial-u.example.com",
            "https://aliencyborg.share.zrok.io",
        ]
    )

    # Database settings
    DATABASE_URL: str = DEFAULT_DB_URL

    # Logging settings
    LOG_LEVEL: str = DEFAULT_LOG_LEVEL

    # API Keys
    ANTHROPIC_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Temporary storage paths
    TEMP_AUDIO_PATH: str = DEFAULT_TEMP_AUDIO_PATH
    CONTENT_LOGS_PATH: str = DEFAULT_CONTENT_LOGS_PATH

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

    # Integration service endpoints
    OLLAMA_HOST: str = "http://localhost:11434"

    # Course generation model
    COURSE_GENERATION_MODEL: str = "gpt-4.1-nano"
    # Department generation model
    DEPARTMENT_GENERATION_MODEL: str = "gpt-4.1-nano"
    # Lecture generation model
    LECTURE_GENERATION_MODEL: str = "claude-3.7-sonnet-latest"
    # Professor generation model
    PROFESSOR_GENERATION_MODEL: str = "gpt-4.1-nano"
    # Topics generation model
    TOPICS_GENERATION_MODEL: str = "gemini-2.5-flash-preview-04-17"
    # Image generation model
    IMAGE_GENERATION_MODEL: str = "gpt-image-1"

    # Configure Pydantic to use .env files
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def __hash__(self) -> int:
        """Make Settings hashable for use with lru_cache."""
        # Use a simple stable string representation for hashing
        # Include only the key parameters that should make a settings instance unique
        return hash(f"{self.environment}:{self.DATABASE_URL}:{self.content_backend}")

    def __eq__(self, other):
        """Implement equality check required for hashable objects."""
        if not isinstance(other, Settings):
            return False
        return (
            self.environment == other.environment
            and self.DATABASE_URL == other.DATABASE_URL
            and self.content_backend == other.content_backend
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
        """Create necessary temporary directories for the application"""
        Path(self.TEMP_AUDIO_PATH).mkdir(parents=True, exist_ok=True)
        Path(self.CONTENT_LOGS_PATH).mkdir(parents=True, exist_ok=True)

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
            "temp_audio_path": self.TEMP_AUDIO_PATH,
            "content_logs_path": self.CONTENT_LOGS_PATH,
            "anthropic_api_key": self.ANTHROPIC_API_KEY,
            "elevenlabs_api_key": self.ELEVENLABS_API_KEY,
            "google_api_key": self.GOOGLE_API_KEY,
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
        logger.info(f"Temporary audio path: {self.TEMP_AUDIO_PATH}")
        logger.info(f"Content logs path: {self.CONTENT_LOGS_PATH}")
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
    if "pytest" in sys.modules or any(arg in sys.argv for arg in ["-m", "pytest", "test"]):
        # For tests, prefer the test environment configuration
        if os.path.exists(".env.test"):
            env_file = ".env.test"
            # Load and set environment variables from .env.test
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
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


def clear_settings_cache():
    """Clear the settings cache for testing or debugging purposes."""
    get_settings.cache_clear()
