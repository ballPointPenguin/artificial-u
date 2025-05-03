"""
Configuration modules for the ArtificialU system.
"""

# Re-export defaults for direct import from artificial_u.config
from artificial_u.config.defaults import (
    DEFAULT_CONTENT_BACKEND,
    DEFAULT_COURSE_WEEKS,
    DEFAULT_DB_URL,
    DEFAULT_LECTURE_WORD_COUNT,
    DEFAULT_LECTURES_PER_WEEK,
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
    DEPARTMENTS,
)

# Export the consolidated settings functionality
from artificial_u.config.settings import Environment, Settings, get_settings

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    "Environment",
    # Default constants
    "DEFAULT_DB_URL",
    "DEFAULT_CONTENT_BACKEND",
    "DEFAULT_OLLAMA_MODEL",
    "DEFAULT_STORAGE_TYPE",
    "DEFAULT_STORAGE_ENDPOINT_URL",
    "DEFAULT_STORAGE_PUBLIC_URL",
    "DEFAULT_STORAGE_ACCESS_KEY",
    "DEFAULT_STORAGE_SECRET_KEY",
    "DEFAULT_STORAGE_REGION",
    "DEFAULT_STORAGE_AUDIO_BUCKET",
    "DEFAULT_STORAGE_LECTURES_BUCKET",
    "DEFAULT_STORAGE_IMAGES_BUCKET",
    "DEPARTMENTS",
    "DEFAULT_COURSE_WEEKS",
    "DEFAULT_LECTURES_PER_WEEK",
    "DEFAULT_LECTURE_WORD_COUNT",
    "DEFAULT_LOG_LEVEL",
]
