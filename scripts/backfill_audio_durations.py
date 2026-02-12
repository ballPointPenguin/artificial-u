#!/usr/bin/env python3
"""Backfill audio duration (in seconds) for existing lecture audio files.

Downloads each audio file from S3/MinIO, reads the duration via mutagen,
and stores it in the lectures.duration column. Read-only on audio files
(no re-upload).
"""

from __future__ import annotations

import argparse
import asyncio
import io
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Ensure project root is on the Python path when executing as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mutagen.mp3 import MP3  # noqa: E402

from artificial_u.models.repositories.factory import RepositoryFactory  # noqa: E402
from artificial_u.services.storage_service import StorageService  # noqa: E402

DEFAULT_BATCH_SIZE = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill audio duration for lectures with audio files.",
    )
    parser.add_argument(
        "--db-url",
        help="Database connection URL. Defaults to DATABASE_URL env var if unset.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of audio files to process per batch (default: {DEFAULT_BATCH_SIZE}).",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Optional cap on the number of files to process in this run.",
    )
    parser.add_argument(
        "--lecture-id",
        type=int,
        help="Process only a specific lecture by ID.",
    )
    parser.add_argument(
        "--course-id",
        type=int,
        help="Process only lectures from a specific course by ID.",
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
    return logging.getLogger("scripts.backfill_audio_durations")


def get_duration_from_bytes(audio_bytes: bytes) -> Optional[int]:
    """Return duration in whole seconds from MP3 audio bytes, or None."""
    try:
        audio = MP3(io.BytesIO(audio_bytes))
        if audio.info and audio.info.length:
            return int(audio.info.length)
        return None
    except Exception:
        return None


def collect_lectures_needing_duration(
    repository_factory: RepositoryFactory,
    lecture_id: Optional[int] = None,
    course_id: Optional[int] = None,
    limit: Optional[int] = None,
    logger: Optional[logging.Logger] = None,
) -> List[int]:
    """Return IDs of lectures that have audio but no duration yet."""
    lecture_repo = repository_factory.lecture

    with lecture_repo.get_session() as session:
        from artificial_u.models.database import LectureModel

        query = session.query(LectureModel.id).filter(
            LectureModel.audio_url.isnot(None),
            LectureModel.duration.is_(None),
        )

        if lecture_id:
            query = query.filter(LectureModel.id == lecture_id)
        if course_id:
            query = query.filter(LectureModel.course_id == course_id)

        query = query.order_by(LectureModel.id)

        if limit is not None and limit > 0:
            query = query.limit(limit)

        ids = [row[0] for row in query.all()]

    if logger:
        logger.info("Found %d lectures needing duration backfill", len(ids))
    return ids


async def process_lecture_duration(
    lecture_id: int,
    repository_factory: RepositoryFactory,
    storage_service: StorageService,
    dry_run: bool,
    logger: logging.Logger,
) -> bool:
    """
    Download audio for a lecture, read its duration, and update the DB.

    Returns True on success, False otherwise.
    """
    try:
        lecture = repository_factory.lecture.get(lecture_id)
        if not lecture or not lecture.audio_url:
            logger.warning("Lecture %d has no audio URL, skipping", lecture_id)
            return False

        # Parse audio URL to get bucket and object key
        bucket, object_key = storage_service.parse_storage_url(lecture.audio_url)
        if not bucket or not object_key:
            logger.error(
                "Failed to parse audio URL for lecture %d: %s",
                lecture_id,
                lecture.audio_url,
            )
            return False

        # Download audio file
        logger.debug("Downloading audio from %s/%s", bucket, object_key)
        audio_bytes, _content_type = await storage_service.download_file(bucket, object_key)

        if not audio_bytes:
            logger.error("Failed to download audio for lecture %d", lecture_id)
            return False

        # Read duration
        duration = get_duration_from_bytes(audio_bytes)
        if duration is None:
            logger.warning("Could not determine duration for lecture %d", lecture_id)
            return False

        if dry_run:
            logger.info(
                "[Dry Run] Would set duration=%d seconds for lecture %d",
                duration,
                lecture_id,
            )
            return True

        # Update the lecture record
        repository_factory.lecture.update_fields(
            lecture_id=lecture_id,
            update_data={"duration": duration},
        )

        logger.info("Set duration=%d seconds for lecture %d", duration, lecture_id)
        return True

    except Exception as e:
        logger.error("Error processing lecture %d: %s", lecture_id, e, exc_info=True)
        return False


async def backfill_durations(
    lecture_ids: List[int],
    repository_factory: RepositoryFactory,
    batch_size: int,
    dry_run: bool,
    logger: logging.Logger,
) -> Dict[str, int]:
    """Process audio files in batches to backfill duration."""
    stats = {"total": len(lecture_ids), "success": 0, "failed": 0, "skipped": 0}

    if not lecture_ids:
        return stats

    storage_service = StorageService(logger=logger)

    for start in range(0, len(lecture_ids), batch_size):
        batch_ids = lecture_ids[start : start + batch_size]
        logger.info(
            "Processing batch %d (%d lectures)",
            start // batch_size + 1,
            len(batch_ids),
        )

        tasks = [
            process_lecture_duration(
                lecture_id=lid,
                repository_factory=repository_factory,
                storage_service=storage_service,
                dry_run=dry_run,
                logger=logger,
            )
            for lid in batch_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                stats["failed"] += 1
            elif result:
                stats["success"] += 1
            else:
                stats["skipped"] += 1

    logger.info(
        "Duration backfill complete: %d successful, %d failed, %d skipped, %d total",
        stats["success"],
        stats["failed"],
        stats["skipped"],
        stats["total"],
    )

    return stats


async def main_async(args: argparse.Namespace, logger: logging.Logger) -> int:
    """Async main function."""
    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("Database URL not provided. Set --db-url or DATABASE_URL.")
        return 1

    repository_factory = RepositoryFactory(db_url=db_url)

    try:
        lecture_ids = collect_lectures_needing_duration(
            repository_factory=repository_factory,
            lecture_id=args.lecture_id,
            course_id=args.course_id,
            limit=args.max_files,
            logger=logger,
        )

        if not lecture_ids:
            logger.info("No lectures need duration backfill.")
            return 0

        await backfill_durations(
            lecture_ids=lecture_ids,
            repository_factory=repository_factory,
            batch_size=max(1, args.batch_size),
            dry_run=args.dry_run,
            logger=logger,
        )

    finally:
        repository_factory.dispose_engines()

    logger.info("Backfill process completed.")
    return 0


def main() -> int:
    args = parse_args()
    logger = configure_logging(args.log_level)
    return asyncio.run(main_async(args, logger))


if __name__ == "__main__":
    raise SystemExit(main())
