#!/usr/bin/env python3
"""Backfill ID3 metadata tags to existing lecture audio files."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

# Ensure project root is on the Python path when executing as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from artificial_u.audio import ID3Tagger  # noqa: E402
from artificial_u.config import get_settings  # noqa: E402
from artificial_u.models.repositories.factory import RepositoryFactory  # noqa: E402
from artificial_u.services.storage_service import StorageService  # noqa: E402

DEFAULT_BATCH_SIZE = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add ID3 metadata tags to existing lecture audio files.",
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
        help="Preview changes without uploading tagged files.",
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
    return logging.getLogger("scripts.backfill_audio_id3_tags")


def collect_lectures_with_audio(
    repository_factory: RepositoryFactory,
    lecture_id: int = None,
    course_id: int = None,
    limit: int = None,
    logger: logging.Logger = None,
) -> List[int]:
    """Return IDs of lectures that have audio URLs."""
    lecture_repo = repository_factory.lecture

    with lecture_repo.get_session() as session:
        from artificial_u.models.database import LectureModel

        query = session.query(LectureModel.id).filter(LectureModel.audio_url.isnot(None))

        # Apply filters
        if lecture_id:
            query = query.filter(LectureModel.id == lecture_id)
        if course_id:
            query = query.filter(LectureModel.course_id == course_id)

        query = query.order_by(LectureModel.id)

        if limit is not None and limit > 0:
            query = query.limit(limit)

        ids = [row[0] for row in query.all()]

    logger.info("Found %d lectures with audio files to process", len(ids))
    return ids


async def process_lecture_audio(
    lecture_id: int,
    repository_factory: RepositoryFactory,
    storage_service: StorageService,
    tagger: ID3Tagger,
    dry_run: bool,
    logger: logging.Logger,
) -> bool:
    """
    Download, tag, and re-upload audio for a single lecture.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get lecture details
        lecture = repository_factory.lecture.get(lecture_id)
        if not lecture or not lecture.audio_url:
            logger.warning(f"Lecture {lecture_id} has no audio URL, skipping")
            return False

        # Get related course and topic
        course = repository_factory.course.get(lecture.course_id)
        topic = repository_factory.topic.get(lecture.topic_id)

        if not course or not topic:
            logger.warning(f"Lecture {lecture_id} missing course or topic metadata, skipping")
            return False

        logger.info(
            f"Processing lecture {lecture_id}: {lecture.title} "
            f"(Course: {course.title}, Week: {topic.week}, Order: {topic.order})"
        )

        # Parse audio URL to get bucket and object key
        bucket, object_key = storage_service.parse_storage_url(lecture.audio_url)
        if not bucket or not object_key:
            logger.error(f"Failed to parse audio URL for lecture {lecture_id}: {lecture.audio_url}")
            return False

        # Download audio file
        logger.debug(f"Downloading audio from {bucket}/{object_key}")
        audio_bytes, content_type = await storage_service.download_file(bucket, object_key)

        if not audio_bytes:
            logger.error(f"Failed to download audio for lecture {lecture_id}")
            return False

        logger.debug(f"Downloaded {len(audio_bytes)} bytes")

        # Calculate track number
        track_number = tagger.calculate_track_number(
            topic_week=topic.week,
            topic_order=topic.order,
            course_id=course.id,
            repository_factory=repository_factory,
        )

        # Generate comment
        settings = get_settings()
        model_name = getattr(lecture, "created_with", None) or settings.TTS_VOICE_MODEL
        comment = tagger.generate_comment(
            model_name=model_name,
            include_elevenlabs=True,
        )

        # Add ID3 tags
        logger.debug(
            f"Adding ID3 tags: title='{lecture.title}', album='{course.title}', track={track_number}"
        )
        tagged_audio = tagger.add_tags_to_audio(
            audio_bytes=audio_bytes,
            title=lecture.title or f"Lecture {topic.week}.{topic.order}",
            album=course.title,
            track_number=track_number,
            year=lecture.created_at.year if hasattr(lecture, "created_at") else None,
            comment=comment if comment else None,
        )

        if dry_run:
            logger.info(
                f"[Dry Run] Would upload tagged audio for lecture {lecture_id} "
                f"({len(tagged_audio)} bytes) to {bucket}/{object_key}"
            )
            return True

        # Re-upload tagged audio (overwrite existing file)
        logger.debug(f"Uploading tagged audio ({len(tagged_audio)} bytes)")
        success, url = await storage_service.upload_file(
            file_data=tagged_audio,
            bucket=bucket,
            object_name=object_key,
            content_type="audio/mpeg",
        )

        if not success:
            logger.error(f"Failed to upload tagged audio for lecture {lecture_id}")
            return False

        logger.info(f"Successfully tagged and uploaded audio for lecture {lecture_id}")
        return True

    except Exception as e:
        logger.error(f"Error processing lecture {lecture_id}: {e}", exc_info=True)
        return False


async def backfill_audio_tags(
    lecture_ids: List[int],
    repository_factory: RepositoryFactory,
    batch_size: int,
    dry_run: bool,
    logger: logging.Logger,
) -> Dict[str, int]:
    """Process audio files in batches and add ID3 tags."""
    stats = {"total": len(lecture_ids), "success": 0, "failed": 0, "skipped": 0}

    if not lecture_ids:
        return stats

    # Initialize services
    storage_service = StorageService(logger=logger)
    tagger = ID3Tagger(logger=logger)

    # Process in batches to avoid overwhelming the system
    for start in range(0, len(lecture_ids), batch_size):
        batch_ids = lecture_ids[start : start + batch_size]
        logger.info(f"Processing batch {start // batch_size + 1} ({len(batch_ids)} lectures)")

        # Process batch concurrently for better performance
        tasks = [
            process_lecture_audio(
                lecture_id=lecture_id,
                repository_factory=repository_factory,
                storage_service=storage_service,
                tagger=tagger,
                dry_run=dry_run,
                logger=logger,
            )
            for lecture_id in batch_ids
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
        f"Audio tagging complete: {stats['success']} successful, "
        f"{stats['failed']} failed, {stats['skipped']} skipped, "
        f"{stats['total']} total"
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
        # Collect lectures to process
        lecture_ids = collect_lectures_with_audio(
            repository_factory=repository_factory,
            lecture_id=args.lecture_id,
            course_id=args.course_id,
            limit=args.max_files,
            logger=logger,
        )

        if not lecture_ids:
            logger.info("No lectures with audio files to process.")
            return 0

        # Process lectures
        await backfill_audio_tags(
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
