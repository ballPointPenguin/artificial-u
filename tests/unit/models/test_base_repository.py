"""
Unit tests for BaseRepository.
"""

from unittest.mock import MagicMock, patch

import pytest

from artificial_u.models import engine as engine_module
from artificial_u.models.repositories.base import BaseRepository


@pytest.fixture(autouse=True)
def reset_engine_singleton():
    """Reset the global engine singleton before each test."""
    engine_module.dispose_engine()
    yield
    engine_module.dispose_engine()


@pytest.mark.unit
class TestBaseRepository:
    """Test the BaseRepository class."""

    def test_init_with_db_url(self):
        """Test initializing with a database URL."""
        repo = BaseRepository(db_url="sqlite:///test.db")
        assert repo.db_url == "sqlite:///test.db"
        assert str(repo.engine.url) == "sqlite:///test.db"

    def test_init_with_engine(self):
        """Test initializing with a pre-existing engine."""
        from sqlalchemy import create_engine

        custom_engine = create_engine("sqlite:///:memory:")
        repo = BaseRepository(engine=custom_engine)
        assert repo.engine is custom_engine
        assert "memory" in str(repo.engine.url)

    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_init_from_env(self):
        """Test initializing from environment variable."""
        repo = BaseRepository()
        assert repo.db_url == "sqlite:///:memory:"
        # Engine URL should match what we passed
        assert "memory" in str(repo.engine.url)

    @patch.dict("artificial_u.models.repositories.base.os.environ", {}, clear=True)
    def test_init_without_db_url(self):
        """Test initializing without a database URL raises an error."""
        # Using clear=True ensures all environment variables are cleared
        with pytest.raises(ValueError, match="Database URL not provided"):
            BaseRepository()

    @patch("artificial_u.models.repositories.base.get_engine")
    def test_engine_creation_uses_shared_singleton(self, mock_get_engine):
        """Test that the repository uses the shared engine singleton."""
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        repo = BaseRepository(db_url="sqlite:///:memory:")

        mock_get_engine.assert_called_once_with("sqlite:///:memory:")
        assert repo.engine == mock_engine

    def test_get_session(self, mock_session):
        """Test getting a database session."""
        # Override the get_session method to return our mock
        repo = BaseRepository(db_url="sqlite:///test.db")
        with patch.object(repo, "get_session", return_value=mock_session):
            session = repo.get_session()
            assert session == mock_session

    @patch("artificial_u.models.database.Base.metadata.create_all")
    def test_create_tables(self, mock_create_all):
        """Test creating database tables."""
        repo = BaseRepository(db_url="sqlite:///test.db")
        repo.create_tables()

        mock_create_all.assert_called_once_with(repo.engine)

    def test_dispose_engine_is_noop(self):
        """Test that dispose_engine is a no-op for individual repositories."""
        repo = BaseRepository(db_url="sqlite:///test.db")
        # This should not raise and should be a no-op
        repo.dispose_engine()
        # Engine should still be accessible
        assert repo.engine is not None
