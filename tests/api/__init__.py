"""
API Tests package for the ArtificialU project.
"""

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "api: mark tests that are part of the API test suite")
