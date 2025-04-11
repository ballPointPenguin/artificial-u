"""
Configuration management for ArtificialU.

This module maintains backwards compatibility with the existing ConfigManager
interface while delegating to the new Pydantic-based settings.
"""

import logging
import warnings
from typing import Optional, Dict, Any

from artificial_u.config.settings import get_settings
from artificial_u.config.defaults import (
    DEFAULT_CONTENT_BACKEND,
    DEFAULT_LOG_LEVEL,
    DEFAULT_STORAGE_TYPE,
)

# Default caching settings
DEFAULT_ENABLE_CACHING = False
DEFAULT_CACHE_METRICS = True


class ConfigManager:
    """
    Centralized configuration management for ArtificialU.

    This class is maintained for backwards compatibility.
    New code should use artificial_u.config.settings.get_settings() directly.
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        elevenlabs_api_key: Optional[str] = None,
        db_url: Optional[str] = None,
        content_backend: str = DEFAULT_CONTENT_BACKEND,
        content_model: Optional[str] = None,
        log_level: str = DEFAULT_LOG_LEVEL,
        enable_caching: bool = DEFAULT_ENABLE_CACHING,
        cache_metrics: bool = DEFAULT_CACHE_METRICS,
        storage_type: str = DEFAULT_STORAGE_TYPE,
        storage_endpoint_url: Optional[str] = None,
        storage_public_url: Optional[str] = None,
        storage_access_key: Optional[str] = None,
        storage_secret_key: Optional[str] = None,
        storage_region: Optional[str] = None,
    ):
        """
        Initialize configuration manager.

        This constructor now delegates to the new settings system while maintaining
        the same interface for backwards compatibility (minus removed paths).
        """
        # Show deprecation warning
        warnings.warn(
            "ConfigManager is deprecated. Use artificial_u.config.settings.get_settings() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Get the settings singleton
        self._settings = get_settings()

        # Override settings with any explicitly provided values
        if anthropic_api_key:
            self._settings.ANTHROPIC_API_KEY = anthropic_api_key
        if elevenlabs_api_key:
            self._settings.ELEVENLABS_API_KEY = elevenlabs_api_key
        if db_url:
            self._settings.DATABASE_URL = db_url
        if content_model:
            self._settings.content_model = content_model

        # Storage settings
        if storage_endpoint_url:
            self._settings.STORAGE_ENDPOINT_URL = storage_endpoint_url
        if storage_public_url:
            self._settings.STORAGE_PUBLIC_URL = storage_public_url
        if storage_access_key:
            self._settings.STORAGE_ACCESS_KEY = storage_access_key
        if storage_secret_key:
            self._settings.STORAGE_SECRET_KEY = storage_secret_key
        if storage_region:
            self._settings.STORAGE_REGION = storage_region

        # Always override these settings with explicitly provided values
        self._settings.content_backend = content_backend
        self._settings.enable_caching = enable_caching
        self._settings.cache_metrics = cache_metrics
        self._settings.STORAGE_TYPE = storage_type

        # Set up logging if a custom level was provided
        if log_level != DEFAULT_LOG_LEVEL:
            self._settings.LOG_LEVEL = log_level
            self.logger = self._settings.setup_logging()
        else:
            self.logger = logging.getLogger("artificial_u")

        # Log configuration
        self._log_configuration()

    @property
    def anthropic_api_key(self) -> Optional[str]:
        """Get Anthropic API key"""
        return self._settings.ANTHROPIC_API_KEY

    @anthropic_api_key.setter
    def anthropic_api_key(self, value: str):
        """Set Anthropic API key"""
        self._settings.ANTHROPIC_API_KEY = value

    @property
    def elevenlabs_api_key(self) -> Optional[str]:
        """Get ElevenLabs API key"""
        return self._settings.ELEVENLABS_API_KEY

    @elevenlabs_api_key.setter
    def elevenlabs_api_key(self, value: str):
        """Set ElevenLabs API key"""
        self._settings.ELEVENLABS_API_KEY = value

    @property
    def db_url(self) -> str:
        """Get database URL"""
        return self._settings.DATABASE_URL

    @db_url.setter
    def db_url(self, value: str):
        """Set database URL"""
        self._settings.DATABASE_URL = value

    @property
    def content_backend(self) -> str:
        """Get content backend"""
        return self._settings.content_backend

    @content_backend.setter
    def content_backend(self, value: str):
        """Set content backend"""
        self._settings.content_backend = value

    @property
    def content_model(self) -> Optional[str]:
        """Get content model"""
        return self._settings.content_model

    @content_model.setter
    def content_model(self, value: Optional[str]):
        """Set content model"""
        self._settings.content_model = value

    @property
    def enable_caching(self) -> bool:
        """Get caching enabled status"""
        return self._settings.enable_caching

    @enable_caching.setter
    def enable_caching(self, value: bool):
        """Set caching enabled status"""
        self._settings.enable_caching = value

    @property
    def cache_metrics(self) -> bool:
        """Get cache metrics status"""
        return self._settings.cache_metrics

    @cache_metrics.setter
    def cache_metrics(self, value: bool):
        """Set cache metrics status"""
        self._settings.cache_metrics = value

    @property
    def storage_type(self) -> str:
        """Get storage type"""
        return self._settings.STORAGE_TYPE

    @storage_type.setter
    def storage_type(self, value: str):
        """Set storage type"""
        self._settings.STORAGE_TYPE = value

    @property
    def storage_endpoint_url(self) -> str:
        """Get storage endpoint URL"""
        return self._settings.STORAGE_ENDPOINT_URL

    @storage_endpoint_url.setter
    def storage_endpoint_url(self, value: str):
        """Set storage endpoint URL"""
        self._settings.STORAGE_ENDPOINT_URL = value

    @property
    def storage_public_url(self) -> str:
        """Get storage public URL"""
        return self._settings.STORAGE_PUBLIC_URL

    @storage_public_url.setter
    def storage_public_url(self, value: str):
        """Set storage public URL"""
        self._settings.STORAGE_PUBLIC_URL = value

    @property
    def storage_access_key(self) -> str:
        """Get storage access key"""
        return self._settings.STORAGE_ACCESS_KEY

    @storage_access_key.setter
    def storage_access_key(self, value: str):
        """Set storage access key"""
        self._settings.STORAGE_ACCESS_KEY = value

    @property
    def storage_secret_key(self) -> str:
        """Get storage secret key"""
        return self._settings.STORAGE_SECRET_KEY

    @storage_secret_key.setter
    def storage_secret_key(self, value: str):
        """Set storage secret key"""
        self._settings.STORAGE_SECRET_KEY = value

    @property
    def storage_region(self) -> str:
        """Get storage region"""
        return self._settings.STORAGE_REGION

    @storage_region.setter
    def storage_region(self, value: str):
        """Set storage region"""
        self._settings.STORAGE_REGION = value

    @property
    def storage_audio_bucket(self) -> str:
        """Get storage audio bucket"""
        return self._settings.STORAGE_AUDIO_BUCKET

    @property
    def storage_lectures_bucket(self) -> str:
        """Get storage lectures bucket"""
        return self._settings.STORAGE_LECTURES_BUCKET

    @property
    def storage_images_bucket(self) -> str:
        """Get storage images bucket"""
        return self._settings.STORAGE_IMAGES_BUCKET

    @property
    def temp_audio_path(self) -> str:
        """Get temporary audio path"""
        return self._settings.TEMP_AUDIO_PATH

    def _log_configuration(self) -> None:
        """Log the current configuration."""
        self.logger.info(f"Using database: {self.db_url}")
        self.logger.info(f"Content backend: {self.content_backend}")
        if self.content_model:
            self.logger.info(f"Content model: {self.content_model}")
        self.logger.info(f"Caching enabled: {self.enable_caching}")
        self.logger.info(f"Temporary audio path: {self.temp_audio_path}")
        self.logger.info(f"Storage type: {self.storage_type}")
        if self.storage_type == "minio":
            self.logger.info(f"MinIO endpoint: {self.storage_endpoint_url}")
            self.logger.info(f"MinIO public URL: {self.storage_public_url}")

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
            "temp_audio_path": self.temp_audio_path,
            "anthropic_api_key": self.anthropic_api_key,
            "elevenlabs_api_key": self.elevenlabs_api_key,
            "storage_type": self.storage_type,
            "storage_endpoint_url": self.storage_endpoint_url,
            "storage_public_url": self.storage_public_url,
            "storage_access_key": self.storage_access_key,
            "storage_secret_key": self.storage_secret_key,
            "storage_region": self.storage_region,
            "storage_audio_bucket": self.storage_audio_bucket,
            "storage_lectures_bucket": self.storage_lectures_bucket,
            "storage_images_bucket": self.storage_images_bucket,
        }
