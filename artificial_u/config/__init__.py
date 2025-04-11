"""
Configuration modules for the ArtificialU system.
"""

# Re-export defaults for direct import from artificial_u.config
from artificial_u.config.defaults import (
    DEFAULT_DB_URL,
    DEFAULT_AUDIO_PATH,
    DEFAULT_TEXT_EXPORT_PATH,
    DEFAULT_CONTENT_BACKEND,
    DEFAULT_OLLAMA_MODEL,
    PROFESSOR_TITLES,
    PROFESSOR_LAST_NAMES,
    DEPARTMENTS,
    DEPARTMENT_SPECIALIZATIONS,
    TEACHING_STYLES,
    PERSONALITIES,
    DEFAULT_COURSE_LEVEL,
    DEFAULT_COURSE_WEEKS,
    DEFAULT_LECTURES_PER_WEEK,
    DEFAULT_LECTURE_WORD_COUNT,
    DEFAULT_LOG_LEVEL,
)

# Export the new consolidated settings functionality
from artificial_u.config.settings import (
    Settings,
    get_settings,
    Environment,
)

# For backwards compatibility, ensure ConfigManager is available
from artificial_u.config.config_manager import ConfigManager

__all__ = [
    # Settings
    "Settings",
    "get_settings",
    "Environment",
    "ConfigManager",
    # Default constants
    "DEFAULT_DB_URL",
    "DEFAULT_AUDIO_PATH",
    "DEFAULT_TEXT_EXPORT_PATH",
    "DEFAULT_CONTENT_BACKEND",
    "DEFAULT_OLLAMA_MODEL",
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
