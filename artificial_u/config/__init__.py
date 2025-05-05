"""
Configuration modules for the ArtificialU system.
"""

# Re-export defaults for direct import from artificial_u.config
from artificial_u.config.defaults import (
    DEFAULT_CONTENT_BACKEND,
    DEFAULT_CONTENT_LOGS_PATH,
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
    DEFAULT_TEMP_AUDIO_PATH,
    DEPARTMENTS,
)

# Export the consolidated settings functionality
from artificial_u.config.settings import (
    Environment,
    Settings,
    clear_settings_cache,
    get_settings,
)

__all__ = [
    # Settings management
    "Settings",
    "get_settings",
    "clear_settings_cache",
    "Environment",
    # Default paths and storage
    "DEFAULT_DB_URL",
    "DEFAULT_TEMP_AUDIO_PATH",
    "DEFAULT_CONTENT_LOGS_PATH",
    "DEFAULT_STORAGE_TYPE",
    "DEFAULT_STORAGE_ENDPOINT_URL",
    "DEFAULT_STORAGE_PUBLIC_URL",
    "DEFAULT_STORAGE_ACCESS_KEY",
    "DEFAULT_STORAGE_SECRET_KEY",
    "DEFAULT_STORAGE_REGION",
    "DEFAULT_STORAGE_AUDIO_BUCKET",
    "DEFAULT_STORAGE_LECTURES_BUCKET",
    "DEFAULT_STORAGE_IMAGES_BUCKET",
    # Content generation defaults
    "DEFAULT_CONTENT_BACKEND",
    "DEFAULT_OLLAMA_MODEL",
    # Course and lecture defaults
    "DEFAULT_COURSE_WEEKS",
    "DEFAULT_LECTURES_PER_WEEK",
    "DEFAULT_LECTURE_WORD_COUNT",
    # System defaults
    "DEFAULT_LOG_LEVEL",
    "DEPARTMENTS",
]
