#!/usr/bin/env python3
"""
Initialize the database with premade voices from ElevenLabs.

This script fetches all premade voices from the v2/voices endpoint and stores them
in the database for use in voice selection.
"""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from artificial_u.models.repositories import RepositoryFactory  # noqa: E402
from artificial_u.services import VoiceService  # noqa: E402


def main():
    """Initialize the database with premade voices."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    try:
        # Initialize services
        logger.info("Initializing voice service...")
        repository_factory = RepositoryFactory()
        voice_service = VoiceService(repository_factory=repository_factory)

        # Fetch and store premade voices
        logger.info("Fetching premade voices from ElevenLabs...")
        count = voice_service.fetch_and_store_premade_voices()

        logger.info(f"Successfully stored {count} premade voices in the database")

        # Get some statistics
        total_voices = repository_factory.voice.count()
        premade_count = repository_factory.voice.count(category="premade")
        professional_count = repository_factory.voice.count(category="professional")
        high_quality_count = repository_factory.voice.count(category="high_quality")

        logger.info("Voice database statistics:")
        logger.info(f"  Total voices: {total_voices}")
        logger.info(f"  Premade voices: {premade_count}")
        logger.info(f"  Professional voices: {professional_count}")
        logger.info(f"  High quality voices: {high_quality_count}")

    except Exception as e:
        logger.error(f"Error initializing voices: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
