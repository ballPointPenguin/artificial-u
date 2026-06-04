#!/usr/bin/env python3
"""
Seed xAI (Grok) voices into the voices table from the live API (idempotent).

Fetches the actual voice catalog from the xAI Voices API and upserts records
into the local database. Voices that already exist (matched by tts_backend +
external_id) are skipped.

NOTE: Seeding is optional. The frontend lists xAI voices on-demand via
GET /api/v1/voices/xai/catalog, so new voices appear automatically without
running this script. Seeding is useful if you prefer a pre-populated DB.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).parent.parent / ".env")

from artificial_u.integrations.xai.voice_manager import XAIVoiceManager  # noqa: E402
from artificial_u.models.core import Voice  # noqa: E402
from artificial_u.models.repositories.voice import VoiceRepository  # noqa: E402

TTS_BACKEND = "xai"


def seed_xai_voices(
    db_url: str | None = None,
    dry_run: bool = False,
    logger: logging.Logger | None = None,
) -> tuple[int, int]:
    """
    Seed xAI voices from the live API. Idempotent.

    Returns:
        Tuple of (created_count, skipped_count)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        logger.error("XAI_API_KEY is not set — cannot fetch voice catalog")
        sys.exit(1)

    raw_voices = XAIVoiceManager(api_key=api_key, logger=logger).list_voices()
    logger.info("Fetched %d voices from xAI API", len(raw_voices))

    effective_url = db_url or os.environ.get("DATABASE_URL")
    repo = VoiceRepository(db_url=effective_url)

    created = 0
    skipped = 0

    for v in raw_voices:
        external_id = v.get("id")
        if not external_id:
            continue

        existing = repo.get_by_external_id(TTS_BACKEND, external_id)
        if existing is not None:
            logger.debug("Voice already exists: %s (db id=%s)", v.get("name"), existing.id)
            skipped += 1
            continue

        if dry_run:
            logger.info("[DRY RUN] Would create: %s (%s)", v.get("name"), external_id)
            created += 1
            continue

        voice = Voice(
            tts_backend=TTS_BACKEND,
            external_id=external_id,
            name=v.get("name") or external_id,
            gender=v.get("gender"),
            language=v.get("language"),
            category="preset",
        )

        repo.create(voice)
        logger.info("Created voice: %s (external_id=%s)", voice.name, external_id)
        created += 1

    return created, skipped


def main():
    parser = argparse.ArgumentParser(description="Seed xAI (Grok) voices from the live API")
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
            logger.info("DRY RUN mode — no changes will be made")

        created, skipped = seed_xai_voices(db_url=args.db_url, dry_run=args.dry_run, logger=logger)
        logger.info("xAI voice seeding complete: %d created, %d skipped", created, skipped)

    except Exception as e:
        logger.error("Error seeding xAI voices: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
