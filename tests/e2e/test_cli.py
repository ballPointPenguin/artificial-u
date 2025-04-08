"""
End-to-end tests for CLI functionality.

These tests use the Click test runner to verify CLI commands
work correctly with a real database (but mocked APIs).
"""

import pytest
from click.testing import CliRunner
from artificial_u.cli.app import cli


@pytest.fixture
def runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.mark.e2e
def test_create_course_command(runner):
    """Test the create-course CLI command."""
    pass  # Test implementation would go here


@pytest.mark.e2e
def test_manage_voices_command(runner):
    """Test the manage-voices CLI command."""
    pass  # Test implementation would go here
