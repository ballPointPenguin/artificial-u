#!/usr/bin/env python3
"""
Seed Mistral Voxtral preset voices into the voices table (idempotent).

This script creates voice records for each of Mistral's 20 preset TTS voices.
It is safe to run multiple times - existing voices are skipped.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from artificial_u.models.core import Voice  # noqa: E402
from artificial_u.models.repositories.voice import VoiceRepository  # noqa: E402

# Mistral Voxtral preset voices with metadata.
# Gender/age/descriptive are best-effort characterizations of Mistral's preset names.
MISTRAL_VOICES = [
    {"name": "alloy", "descriptive": "neutral", "gender": "neutral"},
    {"name": "ash", "descriptive": "warm", "gender": "male"},
    {"name": "breeze", "descriptive": "gentle", "gender": "female"},
    {"name": "cove", "descriptive": "calm", "gender": "male"},
    {"name": "echo", "descriptive": "clear", "gender": "neutral"},
    {"name": "ember", "descriptive": "warm", "gender": "female"},
    {"name": "fable", "descriptive": "storytelling", "gender": "neutral"},
    {"name": "haze", "descriptive": "soft", "gender": "neutral"},
    {"name": "lark", "descriptive": "bright", "gender": "female"},
    {"name": "maple", "descriptive": "warm", "gender": "female"},
    {"name": "nova", "descriptive": "energetic", "gender": "female"},
    {"name": "onyx", "descriptive": "deep", "gender": "male"},
    {"name": "orbit", "descriptive": "steady", "gender": "male"},
    {"name": "reed", "descriptive": "clear", "gender": "male"},
    {"name": "sage", "descriptive": "wise", "gender": "neutral"},
    {"name": "shimmer", "descriptive": "bright", "gender": "female"},
    {"name": "vale", "descriptive": "calm", "gender": "neutral"},
    {"name": "vortex", "descriptive": "dynamic", "gender": "male"},
    {"name": "whisper", "descriptive": "soft", "gender": "neutral"},
    {"name": "zen", "descriptive": "serene", "gender": "neutral"},
]

TTS_BACKEND = "mistral"


def seed_mistral_voices(
    db_url: str | None = None,
    dry_run: bool = False,
    logger: logging.Logger | None = None,
) -> tuple[int, int]:
    """
    Seed Mistral preset voices. Idempotent - safe to run multiple times.

    Args:
        db_url: Optional database URL (defaults to DATABASE_URL env var)
        dry_run: If True, report what would happen without making changes
        logger: Optional logger instance

    Returns:
        Tuple of (created_count, skipped_count)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    effective_url = db_url or os.environ.get("DATABASE_URL")
    logger.info("Initializing voice repository...")
    repo = VoiceRepository(db_url=effective_url)

    created = 0
    skipped = 0

    for voice_data in MISTRAL_VOICES:
        voice_name = voice_data["name"]
        external_id = voice_name  # Mistral uses the preset name as the voice identifier

        existing = repo.get_by_external_id(TTS_BACKEND, external_id)
        if existing is not None:
            logger.debug(f"Voice already exists: {voice_name} (id={existing.id})")
            skipped += 1
            continue

        if dry_run:
            logger.info(f"[DRY RUN] Would create voice: {voice_name}")
            created += 1
            continue

        voice = Voice(
            tts_backend=TTS_BACKEND,
            external_id=external_id,
            name=f"Mistral {voice_name.title()}",
            gender=voice_data.get("gender"),
            descriptive=voice_data.get("descriptive"),
            language="en",
            category="preset",
            use_case="informative_educational",
            description=f"Mistral Voxtral preset voice: {voice_name}",
        )

        repo.create(voice)
        logger.info(f"Created voice: {voice_name} (backend={TTS_BACKEND})")
        created += 1

    return created, skipped


def main():
    parser = argparse.ArgumentParser(description="Seed Mistral Voxtral preset voices")
    parser.add_argument("--db-url", help="Database URL (default: DATABASE_URL env var)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Report changes without applying them"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    try:
        if args.dry_run:
            logger.info("DRY RUN mode - no changes will be made")

        created, skipped = seed_mistral_voices(
            db_url=args.db_url, dry_run=args.dry_run, logger=logger
        )

        logger.info(f"Mistral voice seeding complete: {created} created, {skipped} skipped")

    except Exception as e:
        logger.error(f"Error seeding Mistral voices: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
