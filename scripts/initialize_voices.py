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

from artificial_u.integrations.elevenlabs.models import (  # noqa: E402
    ELEVENLABS_V4_MODEL,
    voice_lists_model,
)
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
        count_premade = voice_service.fetch_and_store_premade_voices()
        logger.info(f"Stored {count_premade} premade voices in the database")

        # Seed common non-English languages from shared voices to avoid EN-only DBs
        # See docs/languages.md for rationale
        seed_languages = [
            "es",  # Spanish
            "de",  # German
            "ja",  # Japanese
            "fr",  # French
            "pt",  # Portuguese
            "ru",  # Russian
            "it",  # Italian
            "zh",  # Chinese
            "ar",  # Arabic
            "el",  # Greek
        ]
        for lang in seed_languages:
            logger.info(f"Ensuring language catalog populated for '{lang}' ...")
            # Use internal helper via public API fetch/save path
            # Pull a couple of pages unfiltered except language
            page = 0
            pages_to_fetch = 2
            while page < pages_to_fetch:
                voices, has_more = voice_service.client.get_shared_voices(
                    language=lang, page_size=100, page=page
                )
                for v in voices:
                    voice_service._save_voice_to_db(v)
                if not has_more:
                    break
                page += 1

        # Repair voices added by ID that never captured verified_languages
        logger.info("Refreshing voices with empty verified_languages ...")
        refresh = voice_service.refresh_voices_missing_verified_languages()
        logger.info(
            f"  Checked {refresh['checked']}, updated {refresh['updated']}, "
            f"unresolved {refresh['unresolved']}"
        )

        # Get some statistics
        total_voices = repository_factory.voice.count()
        premade_count = repository_factory.voice.count(category="premade")
        professional_count = repository_factory.voice.count(category="professional")
        high_quality_count = repository_factory.voice.count(category="high_quality")
        it_count = repository_factory.voice.count(language="it")
        fr_count = repository_factory.voice.count(language="fr")
        es_count = repository_factory.voice.count(language="es")

        el_voices = repository_factory.voice.list(tts_backend="elevenlabs", limit=100000)
        v4_count = sum(voice_lists_model(v.model_dump(), ELEVENLABS_V4_MODEL) for v in el_voices)

        logger.info("Voice database statistics:")
        logger.info(f"  Voices verified for {ELEVENLABS_V4_MODEL}: {v4_count}/{len(el_voices)}")
        logger.info(f"  Total voices: {total_voices}")
        logger.info(f"  Premade voices: {premade_count}")
        logger.info(f"  Professional voices: {professional_count}")
        logger.info(f"  High quality voices: {high_quality_count}")
        logger.info(f"  Italian voices: {it_count}")
        logger.info(f"  French voices: {fr_count}")
        logger.info(f"  Spanish voices: {es_count}")

    except Exception as e:
        logger.error(f"Error initializing voices: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
