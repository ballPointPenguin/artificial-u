"""
Unit tests for the RepositoryFactory.
"""

from unittest.mock import patch

import pytest

from artificial_u.models.repositories.course import CourseRepository
from artificial_u.models.repositories.department import DepartmentRepository
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.models.repositories.lecture import LectureRepository
from artificial_u.models.repositories.professor import ProfessorRepository
from artificial_u.models.repositories.voice import VoiceRepository


@pytest.mark.unit
class TestRepositoryFactory:
    """Test the RepositoryFactory class."""

    def test_init_with_db_url(self):
        """Test initializing with a database URL."""
        factory = RepositoryFactory(db_url="sqlite:///test.db")
        assert factory.db_url == "sqlite:///test.db"

    def test_init_without_db_url(self):
        """Test initializing without a database URL."""
        factory = RepositoryFactory()
        assert factory.db_url is None

    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_get_repository(self):
        """Test getting a repository instance."""
        factory = RepositoryFactory()
        repo = factory.get_repository(DepartmentRepository)
        assert isinstance(repo, DepartmentRepository)

        # Second call should return the same instance
        repo2 = factory.get_repository(DepartmentRepository)
        assert repo is repo2  # Same instance

    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_department_property(self):
        """Test the department property."""
        factory = RepositoryFactory()
        assert isinstance(factory.department, DepartmentRepository)

    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_professor_property(self):
        """Test the professor property."""
        factory = RepositoryFactory()
        assert isinstance(factory.professor, ProfessorRepository)

    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_course_property(self):
        """Test the course property."""
        factory = RepositoryFactory()
        assert isinstance(factory.course, CourseRepository)

    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_lecture_property(self):
        """Test the lecture property."""
        factory = RepositoryFactory()
        assert isinstance(factory.lecture, LectureRepository)

    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_voice_property(self):
        """Test the voice property."""
        factory = RepositoryFactory()
        assert isinstance(factory.voice, VoiceRepository)

    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    @patch("artificial_u.models.repositories.base.BaseRepository.create_tables")
    def test_create_tables(self, mock_create_tables):
        """Test creating tables."""
        factory = RepositoryFactory()
        factory.create_tables()
        mock_create_tables.assert_called_once()

    @patch.dict("artificial_u.models.repositories.base.os.environ", {}, clear=True)
    def test_repository_raises_without_db_url(self):
        """Test that accessing a repository without a db_url raises an error."""
        factory = RepositoryFactory()
        with pytest.raises(ValueError, match="Database URL not provided"):
            factory.department
