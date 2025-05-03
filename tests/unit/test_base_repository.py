"""
Unit tests for BaseRepository.
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from artificial_u.models.repositories.base import BaseRepository


@pytest.mark.unit
class TestBaseRepository:
    """Test the BaseRepository class."""

    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_init_with_db_url(self):
        """Test initializing with a database URL."""
        repo = BaseRepository(db_url="sqlite:///test.db")
        assert repo.db_url == "sqlite:///test.db"
        assert str(repo.engine.url) == "sqlite:///test.db"

    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_init_from_env(self):
        """Test initializing from environment variable."""
        repo = BaseRepository()
        assert repo.db_url == "sqlite:///:memory:"
        assert str(repo.engine.url) == "sqlite:///:memory:"

    @patch.dict("artificial_u.models.repositories.base.os.environ", {}, clear=True)
    def test_init_without_db_url(self):
        """Test initializing without a database URL raises an error."""
        # Using clear=True ensures all environment variables are cleared
        with pytest.raises(ValueError, match="Database URL not provided"):
            BaseRepository()

    @patch("artificial_u.models.repositories.base.create_engine")
    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_engine_creation(self, mock_create_engine):
        """Test that the engine is created properly."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        repo = BaseRepository()

        mock_create_engine.assert_called_once_with("sqlite:///:memory:")
        assert repo.engine == mock_engine

    @patch("artificial_u.models.repositories.base.Session")
    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_get_session(self, mock_session_class):
        """Test getting a database session."""
        mock_session = MagicMock(spec=Session)
        mock_session_class.return_value = mock_session

        repo = BaseRepository()
        session = repo.get_session()

        assert session == mock_session

    @patch("artificial_u.models.database.Base.metadata.create_all")
    @patch.dict(
        "artificial_u.models.repositories.base.os.environ", {"DATABASE_URL": "sqlite:///:memory:"}
    )
    def test_create_tables(self, mock_create_all):
        """Test creating database tables."""
        repo = BaseRepository()
        repo.create_tables()

        mock_create_all.assert_called_once_with(repo.engine)
