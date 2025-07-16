"""
Custom exceptions for the ArtificialU system.
"""


class ArtificialUException(Exception):
    """Base exception for all ArtificialU errors."""

    pass


class ContentGenerationError(ArtificialUException):
    """Base exception for content generation failures."""

    pass


class TransientError(ContentGenerationError):
    """Exception for temporary errors that might be resolved on retry."""

    pass


class NonTransientError(ContentGenerationError):
    """Exception for permanent errors that should not be retried with the same service."""

    pass


class AudioProcessingError(ArtificialUException):
    """Raised when audio processing fails."""

    pass


class ConfigurationError(ArtificialUException):
    """Base exception for configuration-related errors."""

    pass


class InvalidConfigurationError(ConfigurationError):
    """Exception for invalid configuration values."""

    pass


class MissingConfigurationError(ConfigurationError):
    """Exception for missing configuration keys or values."""

    pass


class DatabaseError(ArtificialUException):
    """Base exception for database-related errors."""

    pass


class EntityNotFoundError(DatabaseError):
    """Exception raised when a database entity is not found."""

    pass


class DuplicateEntityError(DatabaseError):
    """Exception raised when a duplicate entity is found in the database."""

    pass


class StorageError(ArtificialUException):
    """Base exception for storage-related errors."""

    pass


class CourseNotFoundError(ArtificialUException):
    """Raised when a course cannot be found."""

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


class LectureNotFoundError(ArtificialUException):
    """Raised when a lecture cannot be found."""

    pass


class ProfessorNotFoundError(ArtificialUException):
    """Raised when a professor cannot be found."""

    pass


class TopicNotFoundError(ArtificialUException):
    """Raised when a topic cannot be found."""

    pass
