#!/usr/bin/env python3
"""Backfill lecture metadata such as word counts and summaries."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

# Ensure project root is on the Python path when executing as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from artificial_u.models.database import LectureModel  # noqa: E402
from artificial_u.models.repositories.factory import RepositoryFactory  # noqa: E402
from artificial_u.models.repositories.lecture import LectureRepository  # noqa: E402
from artificial_u.services.content_service import ContentService  # noqa: E402
from artificial_u.services.lecture_generator_service import LectureGeneratorService  # noqa: E402
from artificial_u.services.lecture_service import LectureService  # noqa: E402
from artificial_u.utils.exceptions import (  # noqa: E402
    ContentGenerationError,
    DatabaseError,
    LectureNotFoundError,
)

DEFAULT_BATCH_SIZE = 50


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill lecture word counts and (optionally) summaries.",
    )
    parser.add_argument(
        "--db-url",
        help="Database connection URL. Defaults to DATABASE_URL env var if unset.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Number of lectures to process per batch when updating word counts (default: {DEFAULT_BATCH_SIZE}).",
    )
    parser.add_argument(
        "--generate-summaries",
        action="store_true",
        help="Attempt to generate summaries for lectures missing them (requires content generation credentials).",
    )
    parser.add_argument(
        "--max-summaries",
        type=int,
        default=None,
        help="Optional cap on the number of summaries to generate in this run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without persisting updates.",
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
    return logging.getLogger("scripts.backfill_lecture_metadata")


def backfill_word_counts(
    lecture_repo: LectureRepository,
    batch_size: int,
    dry_run: bool,
    logger: logging.Logger,
) -> Dict[str, int]:
    """Populate missing word counts for lectures."""

    stats = {"total_missing": 0, "updated": 0, "skipped": 0}

    with lecture_repo.get_session() as session:
        id_query = (
            session.query(LectureModel.id)
            .filter(LectureModel.word_count.is_(None))
            .filter(LectureModel.content.isnot(None))
            .order_by(LectureModel.id)
        )
        missing_ids = [row[0] for row in id_query.all()]

    stats["total_missing"] = len(missing_ids)
    logger.info("Found %d lectures missing word_count", stats["total_missing"])

    if stats["total_missing"] == 0:
        return stats

    for start in range(0, len(missing_ids), batch_size):
        batch_ids = missing_ids[start : start + batch_size]

        with lecture_repo.get_session() as session:
            lectures = (
                session.query(LectureModel)
                .filter(LectureModel.id.in_(batch_ids))
                .order_by(LectureModel.id)
                .all()
            )

            for lecture in lectures:
                word_count = LectureRepository._calculate_word_count(lecture.content)

                if word_count is None:
                    stats["skipped"] += 1
                    logger.debug(
                        "Skipping lecture %s: unable to calculate word count (no content).",
                        lecture.id,
                    )
                    continue

                if dry_run:
                    logger.info(
                        "[Dry Run] Would set lecture %s word_count to %s",
                        lecture.id,
                        word_count,
                    )
                else:
                    lecture.word_count = word_count
                    session.add(lecture)
                    stats["updated"] += 1

            if not dry_run:
                session.commit()

    logger.info(
        "Word count backfill complete: %d updated, %d skipped, %d total missing",
        stats["updated"],
        stats["skipped"],
        stats["total_missing"],
    )

    return stats


def collect_missing_summary_ids(
    lecture_repo: LectureRepository,
    limit: Optional[int],
    logger: logging.Logger,
) -> List[int]:
    """Return IDs of lectures that are missing summaries but have content."""

    with lecture_repo.get_session() as session:
        query = (
            session.query(LectureModel.id)
            .filter(
                or_(
                    LectureModel.summary.is_(None),
                    func.length(func.trim(LectureModel.summary)) == 0,
                )
            )
            .filter(LectureModel.content.isnot(None))
            .order_by(LectureModel.id)
        )

        if limit is not None and limit > 0:
            query = query.limit(limit)

        ids = [row[0] for row in query.all()]

    logger.info("Found %d lectures lacking summaries", len(ids))
    return ids


async def backfill_summaries(
    generator: LectureGeneratorService,
    lecture_ids: Iterable[int],
    dry_run: bool,
    logger: logging.Logger,
) -> Dict[str, int]:
    """Generate summaries for the provided lecture IDs."""

    ids = list(lecture_ids)
    stats = {"attempted": len(ids), "generated": 0, "skipped": 0, "failed": 0}

    if not ids:
        return stats

    if dry_run:
        for lecture_id in ids:
            logger.info("[Dry Run] Would generate summary for lecture %s", lecture_id)
        return stats

    for lecture_id in ids:
        try:
            result = await generator.generate_lecture_summary(lecture_id)
            if result.get("summary"):
                stats["generated"] += 1
            else:
                stats["skipped"] += 1
        except LectureNotFoundError:
            logger.warning("Lecture %s not found; skipping summary generation", lecture_id)
            stats["skipped"] += 1
        except ContentGenerationError as exc:
            logger.error("Summary generation failed for lecture %s: %s", lecture_id, exc)
            stats["failed"] += 1
        except DatabaseError as exc:
            logger.error(
                "Database error while updating summary for lecture %s: %s", lecture_id, exc
            )
            stats["failed"] += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Unexpected error during summary generation for lecture %s", lecture_id
            )
            stats["failed"] += 1

    logger.info(
        "Summary generation complete: %d generated, %d skipped, %d failed",
        stats["generated"],
        stats["skipped"],
        stats["failed"],
    )
    return stats


def main() -> int:
    args = parse_args()
    logger = configure_logging(args.log_level)

    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("Database URL not provided. Set --db-url or DATABASE_URL.")
        return 1

    repository_factory = RepositoryFactory(db_url=db_url)
    lecture_repo = repository_factory.lecture

    try:
        backfill_word_counts(
            lecture_repo=lecture_repo,
            batch_size=max(1, args.batch_size),
            dry_run=args.dry_run,
            logger=logger,
        )

        if args.generate_summaries:
            lecture_ids = collect_missing_summary_ids(
                lecture_repo=lecture_repo,
                limit=args.max_summaries,
                logger=logger,
            )

            if lecture_ids:
                lecture_service = LectureService(
                    repository_factory=repository_factory,
                    logger=logger,
                )
                content_service = ContentService(logger=logger)

                generator = LectureGeneratorService(
                    lecture_service=lecture_service,
                    content_service=content_service,
                    course_service=None,
                    professor_service=None,
                    repository_factory=repository_factory,
                    topic_service=None,
                    job_enqueue_service=None,
                    storage_service=None,
                    logger=logger,
                )

                asyncio.run(
                    backfill_summaries(
                        generator=generator,
                        lecture_ids=lecture_ids,
                        dry_run=args.dry_run,
                        logger=logger,
                    )
                )
            else:
                logger.info("No lectures require summary generation.")
    finally:
        repository_factory.dispose_engines()

    logger.info("Backfill process completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
