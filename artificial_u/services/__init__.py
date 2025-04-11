"""
Services package for ArtificialU.
Contains modules for different service responsibilities.
"""

import os
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# Check if we're running in a test environment
def is_test_environment() -> bool:
    """Check if we're running in a test environment."""
    return os.environ.get("TESTING") == "true" or "pytest" in sys.modules


# Only import actual implementations if we're not in a unit test
# This avoids database connection issues during unit tests
if not is_test_environment():
    try:
        from artificial_u.models.database import Repository
        from artificial_u.services.voice_service import VoiceService

        # Initialize services
        db_repository = Repository()
        voice_service = VoiceService(repository=db_repository)

        logger.info("Initialized production services")
    except Exception as e:
        logger.warning(f"Error initializing services: {e}")
        db_repository = None
        voice_service = None
else:
    # In test environment, don't initialize real services
    logger.info("In test environment - not initializing real services")
    db_repository = None
    voice_service = None
