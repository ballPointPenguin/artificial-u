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

__all__ = [
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
]
