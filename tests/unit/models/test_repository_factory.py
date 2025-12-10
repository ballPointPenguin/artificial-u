"""
Unit tests for the RepositoryFactory.
"""

from unittest.mock import patch

import pytest

from artificial_u.models import engine as engine_module
from artificial_u.models.repositories.course import CourseRepository
from artificial_u.models.repositories.department import DepartmentRepository
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.models.repositories.lecture import LectureRepository
from artificial_u.models.repositories.professor import ProfessorRepository
from artificial_u.models.repositories.voice import VoiceRepository


@pytest.fixture(autouse=True)
def reset_engine_singleton():
    """Reset the global engine singleton before each test."""
    engine_module.dispose_engine()
    yield
    engine_module.dispose_engine()


@pytest.mark.unit
class TestRepositoryFactory:
    """Test the RepositoryFactory class."""

    def test_init_with_db_url(self):
        """Test initializing with a database URL."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        assert factory.db_url == "sqlite:///test.db"

    def test_init_with_pool_settings(self):
        """Test initializing with custom pool settings."""
        factory = RepositoryFactory(
            db_url="sqlite:///test.db",
            pool_size=10,
            max_overflow=20,
            pool_timeout=60,
            pool_recycle=3600,
        )
        assert factory.db_url == "sqlite:///test.db"
        # Verify engine was created (pool settings are passed to get_engine)
        assert factory._engine is not None

    @patch.dict("artificial_u.models.repositories.factory.os.environ", {}, clear=True)
    def test_init_without_db_url_raises_error(self):
        """Test initializing without a database URL raises an error."""
        with pytest.raises(ValueError, match="Database URL not provided"):
            RepositoryFactory()

    def test_get_repository(self):
        """Test getting a repository instance."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        repo = factory.get_repository(DepartmentRepository)
        assert isinstance(repo, DepartmentRepository)

        # Second call should return the same instance
        repo2 = factory.get_repository(DepartmentRepository)
        assert repo is repo2  # Same instance

    def test_all_repositories_share_same_engine(self):
        """Test that all repositories created by factory share the same engine."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")

        dept_repo = factory.department
        prof_repo = factory.professor
        course_repo = factory.course

        # All repositories should share the same engine
        assert dept_repo.engine is prof_repo.engine
        assert prof_repo.engine is course_repo.engine
        assert course_repo.engine is factory._engine

    def test_department_property(self):
        """Test the department property."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        assert isinstance(factory.department, DepartmentRepository)

    def test_professor_property(self):
        """Test the professor property."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        assert isinstance(factory.professor, ProfessorRepository)

    def test_course_property(self):
        """Test the course property."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        assert isinstance(factory.course, CourseRepository)

    def test_lecture_property(self):
        """Test the lecture property."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        assert isinstance(factory.lecture, LectureRepository)

    def test_voice_property(self):
        """Test the voice property."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        assert isinstance(factory.voice, VoiceRepository)

    @patch("artificial_u.models.repositories.base.BaseRepository.create_tables")
    def test_create_tables(self, mock_create_tables):
        """Test creating tables."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        factory.create_tables()
        mock_create_tables.assert_called_once()

    def test_get_pool_status(self):
        """Test getting pool status."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        status = factory.get_pool_status()

        assert status["status"] == "active"
        assert "pool_size" in status
        assert "checked_in" in status
        assert "checked_out" in status

    def test_dispose_engines(self):
        """Test disposing engines clears repositories and engine."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        # Create some repositories
        _ = factory.department
        _ = factory.professor

        assert len(factory._repositories) > 0

        factory.dispose_engines()

        # Repositories should be cleared
        assert len(factory._repositories) == 0
