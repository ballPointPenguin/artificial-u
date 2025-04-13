"""
Factory for creating and managing repository instances.
"""

from typing import Dict, Optional, Type, TypeVar

from artificial_u.models.repositories.base import BaseRepository
from artificial_u.models.repositories.course import CourseRepository
from artificial_u.models.repositories.department import DepartmentRepository
from artificial_u.models.repositories.lecture import LectureRepository
from artificial_u.models.repositories.professor import ProfessorRepository
from artificial_u.models.repositories.voice import VoiceRepository

R = TypeVar("R", bound=BaseRepository)


class RepositoryFactory:
    """
    Factory for creating and managing repository instances.

    This class provides a centralized way to create and access repositories
    with shared database connections.
    """

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the repository factory.

        Args:
            db_url: SQLAlchemy database URL. If not provided, uses
                   the DATABASE_URL environment variable.
        """
        self.db_url = db_url
        self._repositories: Dict[str, BaseRepository] = {}

    def get_repository(self, repo_class: Type[R]) -> R:
        """
        Get or create a repository of the specified type.

        Args:
            repo_class: The repository class to instantiate

        Returns:
            An instance of the specified repository class
        """
        repo_name = repo_class.__name__

        if repo_name not in self._repositories:
            self._repositories[repo_name] = repo_class(db_url=self.db_url)

        return self._repositories[repo_name]

    @property
    def department(self) -> DepartmentRepository:
        """Get the department repository."""
        return self.get_repository(DepartmentRepository)

    @property
    def professor(self) -> ProfessorRepository:
        """Get the professor repository."""
        return self.get_repository(ProfessorRepository)

    @property
    def course(self) -> CourseRepository:
        """Get the course repository."""
        return self.get_repository(CourseRepository)

    @property
    def lecture(self) -> LectureRepository:
        """Get the lecture repository."""
        return self.get_repository(LectureRepository)

    @property
    def voice(self) -> VoiceRepository:
        """Get the voice repository."""
        return self.get_repository(VoiceRepository)

    def create_tables(self):
        """Create all database tables if they don't exist."""
        # We only need to call this once for any repository
        repo = self.get_repository(DepartmentRepository)
        repo.create_tables()
