"""
Configuration modules for the ArtificialU system.
"""

# For backwards compatibility, ensure ConfigManager is available
from artificial_u.config.config_manager import ConfigManager

# Re-export defaults for direct import from artificial_u.config
from artificial_u.config.defaults import (
    DEFAULT_CONTENT_BACKEND,
    DEFAULT_COURSE_LEVEL,
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
    DEFAULT_TEXT_EXPORT_PATH,
    DEPARTMENT_SPECIALIZATIONS,
    DEPARTMENTS,
    PERSONALITIES,
    PROFESSOR_LAST_NAMES,
    PROFESSOR_TITLES,
    TEACHING_STYLES,
)

# Export the new consolidated settings functionality
from artificial_u.config.settings import Environment, Settings, get_settings

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    "Environment",
    "ConfigManager",
    # Default constants
    "DEFAULT_DB_URL",
    "DEFAULT_TEXT_EXPORT_PATH",
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
    "PROFESSOR_TITLES",
    "PROFESSOR_LAST_NAMES",
    "DEPARTMENTS",
    "DEPARTMENT_SPECIALIZATIONS",
    "TEACHING_STYLES",
    "PERSONALITIES",
    "DEFAULT_COURSE_LEVEL",
    "DEFAULT_COURSE_WEEKS",
    "DEFAULT_LECTURES_PER_WEEK",
    "DEFAULT_LECTURE_WORD_COUNT",
    "DEFAULT_LOG_LEVEL",
]
