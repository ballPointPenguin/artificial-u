#!/usr/bin/env python3
"""Backfill tts_backend and external_id for existing voice records.

Sets tts_backend='elevenlabs' and external_id=el_voice_id for any voice rows
that are missing these values. Safe to run multiple times (idempotent).

The Alembic migration (e4f5a6b7c8d9) already performs this backfill inline,
but this script exists as a standalone safety net for production deployments
where the migration may have run before the backfill logic was added, or
for re-running after manual data fixes.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure project root is on the Python path when executing as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from artificial_u.models.repositories.factory import RepositoryFactory  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill tts_backend and external_id for existing voice records.",
    )
    parser.add_argument(
        "--db-url",
        help="Database connection URL. Defaults to DATABASE_URL env var if unset.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without updating the database.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args()


def configure_logging(level: str) -> logging.Logger:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("scripts.backfill_voice_tts_backend")


def backfill_voices(db_url: str, dry_run: bool, logger: logging.Logger) -> dict:
    """Backfill tts_backend and external_id on voice records."""
    from sqlalchemy import text

    stats = {"total": 0, "backfilled_backend": 0, "backfilled_external_id": 0, "skipped": 0}

    repository_factory = RepositoryFactory(db_url=db_url)

    try:
        with repository_factory.voice.get_session() as session:
            # Count total voices
            result = session.execute(text("SELECT COUNT(*) FROM voices"))
            stats["total"] = result.scalar() or 0
            logger.info("Total voice records: %d", stats["total"])

            # Count voices missing tts_backend (shouldn't happen after migration, but just in case)
            result = session.execute(
                text("SELECT COUNT(*) FROM voices WHERE tts_backend IS NULL")
            )
            missing_backend = result.scalar() or 0

            # Count voices missing external_id
            result = session.execute(
                text(
                    "SELECT COUNT(*) FROM voices "
                    "WHERE external_id IS NULL AND el_voice_id IS NOT NULL"
                )
            )
            missing_external_id = result.scalar() or 0

            logger.info(
                "Voices needing backfill: %d missing tts_backend, %d missing external_id",
                missing_backend,
                missing_external_id,
            )

            if missing_backend == 0 and missing_external_id == 0:
                logger.info("Nothing to backfill. All voice records are up to date.")
                return stats

            if dry_run:
                logger.info(
                    "[Dry Run] Would set tts_backend='elevenlabs' on %d rows", missing_backend
                )
                logger.info(
                    "[Dry Run] Would set external_id=el_voice_id on %d rows", missing_external_id
                )
                stats["backfilled_backend"] = missing_backend
                stats["backfilled_external_id"] = missing_external_id
                return stats

            # Backfill tts_backend
            if missing_backend > 0:
                result = session.execute(
                    text(
                        "UPDATE voices SET tts_backend = 'elevenlabs' "
                        "WHERE tts_backend IS NULL"
                    )
                )
                stats["backfilled_backend"] = result.rowcount
                logger.info("Set tts_backend='elevenlabs' on %d rows", result.rowcount)

            # Backfill external_id from el_voice_id
            if missing_external_id > 0:
                result = session.execute(
                    text(
                        "UPDATE voices SET external_id = el_voice_id "
                        "WHERE external_id IS NULL AND el_voice_id IS NOT NULL"
                    )
                )
                stats["backfilled_external_id"] = result.rowcount
                logger.info("Set external_id=el_voice_id on %d rows", result.rowcount)

            session.commit()
            logger.info("Backfill committed successfully.")

    finally:
        repository_factory.dispose_engines()

    return stats


def main() -> int:
    args = parse_args()
    logger = configure_logging(args.log_level)

    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("Database URL not provided. Set --db-url or DATABASE_URL.")
        return 1

    stats = backfill_voices(db_url=db_url, dry_run=args.dry_run, logger=logger)

    logger.info(
        "Backfill complete: %d total, %d backend, %d external_id, %d skipped",
        stats["total"],
        stats["backfilled_backend"],
        stats["backfilled_external_id"],
        stats["skipped"],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
