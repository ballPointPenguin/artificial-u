"""
API configuration module for ArtificialU.
"""

from functools import lru_cache

from artificial_u.config.settings import Settings, get_settings

# Re-export the Settings class and get_settings function
__all__ = ["Settings", "get_settings"]
