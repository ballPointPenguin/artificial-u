"""
Utility modules for the ArtificialU system.
"""

from artificial_u.utils.exceptions import (
    ArtificialUException,
    AudioProcessingError,
    ConfigurationError,
    ContentGenerationError,
    CourseNotFoundError,
    DatabaseError,
    DepartmentNotFoundError,
    DependencyError,
    GenerationError,
    LectureNotFoundError,
    ProfessorNotFoundError,
    TopicNotFoundError,
)
from artificial_u.utils.xml_utils import (
    calculate_estimated_tokens,
    close_unclosed_tags,
    detect_truncation,
    ensure_xml_wrapper,
    extract_complete_elements,
    extract_metadata,
    extract_partial_xml_content,
    extract_xml_between_tags,
)

__all__ = [
    # Exceptions
    "ArtificialUException",
    "AudioProcessingError",
    "ConfigurationError",
    "ContentGenerationError",
    "CourseNotFoundError",
    "DatabaseError",
    "DepartmentNotFoundError",
    "DependencyError",
    "GenerationError",
    "LectureNotFoundError",
    "ProfessorNotFoundError",
    "TopicNotFoundError",
    # XML utilities
    "calculate_estimated_tokens",
    "close_unclosed_tags",
    "detect_truncation",
    "ensure_xml_wrapper",
    "extract_complete_elements",
    "extract_metadata",
    "extract_partial_xml_content",
    "extract_xml_between_tags",
]
