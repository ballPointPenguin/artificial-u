"""
Pytest configuration and shared fixtures.
"""

import os
import pytest
from pathlib import Path
from typing import Generator

from artificial_u.models.database import Repository
from artificial_u.system import UniversitySystem


@pytest.fixture(scope="session")
def test_db_path() -> str:
    """Provide path to test database."""
    return "test_university.db"


@pytest.fixture(scope="session")
def test_audio_path(tmp_path_factory) -> Path:
    """Provide temporary directory for test audio files."""
    return tmp_path_factory.mktemp("test_audio")


@pytest.fixture
def repository(test_db_path: str) -> Generator[Repository, None, None]:
    """Provide a test repository instance with a clean database."""
    repo = Repository(db_path=test_db_path)
    yield repo
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def mock_system(repository: Repository, test_audio_path: Path) -> UniversitySystem:
    """Provide a UniversitySystem instance with mocked external dependencies."""
    return UniversitySystem(
        anthropic_api_key="mock_anthropic_key",
        elevenlabs_api_key="mock_elevenlabs_key",
        db_path=repository.db_path,
        audio_path=str(test_audio_path),
    )
