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
