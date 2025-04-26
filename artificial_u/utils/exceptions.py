"""
Custom exceptions for the ArtificialU system.
"""


class ArtificialUException(Exception):
    """Base exception for all ArtificialU errors."""

    pass


class ProfessorNotFoundError(ArtificialUException):
    """Raised when a professor cannot be found."""

    pass


class CourseNotFoundError(ArtificialUException):
    """Raised when a course cannot be found."""

    pass


class LectureNotFoundError(ArtificialUException):
    """Raised when a lecture cannot be found."""

    pass


class ContentGenerationError(ArtificialUException):
    """Raised when content generation fails."""

    pass


class AudioProcessingError(ArtificialUException):
    """Raised when audio processing fails."""

    pass


class DatabaseError(ArtificialUException):
    """Raised when a database operation fails."""

    pass


class ConfigurationError(ArtificialUException):
    """Raised when there is a configuration error."""

    pass


class DepartmentNotFoundError(ArtificialUException):
    """Raised when a department cannot be found."""

    pass


class DependencyError(ArtificialUException):
    """Raised when a dependency error occurs."""

    pass


class GenerationError(ArtificialUException):
    """Raised when a generation error occurs."""

    pass
