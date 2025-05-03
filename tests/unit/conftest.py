"""
Pytest configuration for unit tests.

This file contains fixtures specifically for unit tests,
including mocks for external dependencies.
"""

from unittest.mock import MagicMock, patch

import pytest


# Mock Repository to avoid database connections
@pytest.fixture(autouse=True)
def mock_repository():
    """Mock the Repository class to avoid database connections in unit tests."""
    with patch("artificial_u.models.repositories.RepositoryFactory") as mock_repo_class:
        # Create a mock instance that will be returned when Repository is instantiated
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Set up some default returns that might be needed
        mock_repo.list_voices.return_value = []
        mock_repo.get_voice_by_elevenlabs_id.return_value = None

        yield mock_repo


@pytest.fixture
def mock_session():
    """
    Create a standardized mock SQLAlchemy session for repository unit tests.

    This fixture provides a consistent interface for mocking database sessions
    across all repository tests.
    """
    session = MagicMock()

    # Configure the session to return itself for common method chains
    session.__enter__.return_value = session

    # Common session methods
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.delete = MagicMock()
    session.rollback = MagicMock()

    # Query builder methods
    query_mock = MagicMock()
    session.query = MagicMock(return_value=query_mock)
    query_mock.filter = MagicMock(return_value=query_mock)
    query_mock.filter_by = MagicMock(return_value=query_mock)
    query_mock.join = MagicMock(return_value=query_mock)
    query_mock.order_by = MagicMock(return_value=query_mock)
    query_mock.offset = MagicMock(return_value=query_mock)
    query_mock.limit = MagicMock(return_value=query_mock)
    query_mock.all = MagicMock(return_value=[])
    query_mock.first = MagicMock(return_value=None)
    query_mock.scalar = MagicMock(return_value=0)

    # Additional methods
    session.get = MagicMock(return_value=None)

    return session


@pytest.fixture
def repository_with_session(mock_session):
    """
    Create a repository instance that uses a mock session.

    This fixture can be extended by other fixtures to create
    specific repository types with the mock session.
    """

    def _create_repository_with_session(repository_class):
        repo = repository_class()
        repo.get_session = MagicMock(return_value=mock_session)
        return repo

    return _create_repository_with_session
