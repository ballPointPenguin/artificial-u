"""
Factory for creating and managing repository instances.
"""

import logging
import os
from typing import Dict, Optional, Type, TypeVar, cast

from sqlalchemy.engine import Engine

from artificial_u.models.engine import dispose_engine, get_engine, get_pool_status
from artificial_u.models.repositories.base import BaseRepository
from artificial_u.models.repositories.course import CourseRepository
from artificial_u.models.repositories.department import DepartmentRepository
from artificial_u.models.repositories.faculty import FacultyRepository
from artificial_u.models.repositories.featured import FeaturedItemRepository
from artificial_u.models.repositories.job import JobRepository
from artificial_u.models.repositories.lecture import LectureRepository
from artificial_u.models.repositories.preference import PreferenceRepository
from artificial_u.models.repositories.professor import ProfessorRepository
from artificial_u.models.repositories.student import StudentRepository
from artificial_u.models.repositories.tag import TagRepository
from artificial_u.models.repositories.topic import TopicRepository
from artificial_u.models.repositories.voice import VoiceRepository

R = TypeVar("R", bound=BaseRepository)

logger = logging.getLogger(__name__)


class RepositoryFactory:
    """
    Factory for creating and managing repository instances.

    This class provides a centralized way to create and access repositories
    with a SHARED database engine. All repositories created by a factory
    instance share the same engine and connection pool, preventing connection
    exhaustion on small RDS instances.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
        pool_pre_ping: bool = True,
    ):
        """
        Initialize the repository factory with a shared database engine.

        Args:
            db_url: SQLAlchemy database URL. If not provided, uses
                   the DATABASE_URL environment variable.
            pool_size: Number of connections to maintain in the pool (default: 5)
            max_overflow: Max additional connections above pool_size (default: 10)
            pool_timeout: Seconds to wait for a connection from pool (default: 30)
            pool_recycle: Seconds before recycling a connection (default: 1800)
            pool_pre_ping: Whether to test connections before use (default: True)
        """
        self.db_url = db_url or os.environ.get("DATABASE_URL")

        if not self.db_url:
            raise ValueError("Database URL not provided. Set DATABASE_URL environment variable.")

        # Get or create the shared engine singleton with pool configuration
        self._engine: Engine = get_engine(
            db_url=self.db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
        )

        self._repositories: Dict[str, BaseRepository] = {}

    def get_repository(self, repo_class: Type[R]) -> R:
        """
        Get or create a repository of the specified type.

        All repositories share the same database engine and connection pool.

        Args:
            repo_class: The repository class to instantiate

        Returns:
            An instance of the specified repository class
        """
        repo_name = repo_class.__name__

        if repo_name not in self._repositories:
            # Pass the shared engine to the repository
            self._repositories[repo_name] = repo_class(engine=self._engine)

        return cast(R, self._repositories[repo_name])

    @property
    def course(self) -> CourseRepository:
        """Get the course repository."""
        return self.get_repository(CourseRepository)

    @property
    def department(self) -> DepartmentRepository:
        """Get the department repository."""
        return self.get_repository(DepartmentRepository)

    @property
    def faculty(self) -> FacultyRepository:
        """Get the faculty repository."""
        return self.get_repository(FacultyRepository)

    @property
    def lecture(self) -> LectureRepository:
        """Get the lecture repository."""
        return self.get_repository(LectureRepository)

    @property
    def professor(self) -> ProfessorRepository:
        """Get the professor repository."""
        return self.get_repository(ProfessorRepository)

    @property
    def topic(self) -> TopicRepository:
        """Get the topic repository."""
        return self.get_repository(TopicRepository)

    @property
    def voice(self) -> VoiceRepository:
        """Get the voice repository."""
        return self.get_repository(VoiceRepository)

    @property
    def job(self) -> JobRepository:
        """Get the job repository."""
        return self.get_repository(JobRepository)

    @property
    def student(self) -> StudentRepository:
        """Get the student repository."""
        return self.get_repository(StudentRepository)

    @property
    def preference(self) -> PreferenceRepository:
        """Get the preference repository."""
        return self.get_repository(PreferenceRepository)

    @property
    def featured(self) -> FeaturedItemRepository:
        """Get the featured item repository."""
        return self.get_repository(FeaturedItemRepository)

    @property
    def tag(self) -> TagRepository:
        """Get the tag repository."""
        return self.get_repository(TagRepository)

    def create_tables(self):
        """Create all database tables if they don't exist."""
        # We only need to call this once for any repository
        repo = self.get_repository(DepartmentRepository)
        repo.create_tables()

    def dispose_engines(self):
        """
        Dispose of the shared database engine and close all connections.

        This should be called during application shutdown.
        """
        logger.info("Disposing shared database engine from factory")
        dispose_engine()
        self._repositories.clear()

    def get_pool_status(self) -> dict:
        """
        Get current connection pool status for monitoring.

        Returns:
            Dictionary with pool statistics including:
            - status: 'active' or 'not_initialized'
            - pool_size: Current pool size
            - checked_in: Connections available in pool
            - checked_out: Connections currently in use
            - overflow: Overflow connections in use
        """
        return get_pool_status()
