#!/usr/bin/env python3
"""Backfill AI-generated subject tags for courses that don't have any yet.

Each course is tagged in its own content-language universe (English courses
get English tags from the English prompt, French courses get French tags),
so this is safe to run against a mixed-language library.

Safe to run multiple times (idempotent): courses that already have tags are
skipped unless --force is passed.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# Ensure project root is on the Python path when executing as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from artificial_u.models.repositories.factory import RepositoryFactory  # noqa: E402
from artificial_u.services.content_service import ContentService  # noqa: E402
from artificial_u.services.course_service import CourseService  # noqa: E402
from artificial_u.services.tag_generator_service import TagGeneratorService  # noqa: E402
from artificial_u.utils.exceptions import ContentGenerationError, CourseNotFoundError  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill AI-generated tags for courses missing them.",
    )
    parser.add_argument(
        "--db-url",
        help="Database connection URL. Defaults to DATABASE_URL env var if unset.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate tags for courses that already have some, not just untagged ones.",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Also tag hidden/draft courses (default: published only).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on the number of courses to tag in this run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview which courses would be tagged without calling the model.",
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
    return logging.getLogger("scripts.backfill_course_tags")


def collect_course_ids(
    repository_factory: RepositoryFactory,
    force: bool,
    include_hidden: bool,
    limit: Optional[int],
    logger: logging.Logger,
) -> List[int]:
    """Return course IDs eligible for tag generation."""
    course_ids = repository_factory.tag.list_backfill_course_ids(
        force=force, include_hidden=include_hidden
    )
    logger.info(
        "Found %d course(s) eligible for tag generation (force=%s, include_hidden=%s)",
        len(course_ids),
        force,
        include_hidden,
    )
    if limit is not None and limit > 0:
        course_ids = course_ids[:limit]
        logger.info("Capped to %d course(s) via --limit", len(course_ids))
    return course_ids


async def backfill_tags(
    generator: TagGeneratorService,
    course_ids: Iterable[int],
    dry_run: bool,
    logger: logging.Logger,
) -> Dict[str, int]:
    """Generate and save tags for the given course IDs."""
    ids = list(course_ids)
    stats = {"attempted": len(ids), "tagged": 0, "skipped": 0, "failed": 0}

    if not ids:
        return stats

    if dry_run:
        for course_id in ids:
            logger.info("[Dry Run] Would generate tags for course %s", course_id)
        return stats

    for course_id in ids:
        try:
            tags = await generator.generate_tags_for_course(course_id)
            logger.info("Tagged course %s with: %s", course_id, ", ".join(t.name for t in tags))
            stats["tagged"] += 1
        except CourseNotFoundError:
            logger.warning("Course %s not found; skipping", course_id)
            stats["skipped"] += 1
        except ContentGenerationError as exc:
            logger.error("Tag generation failed for course %s: %s", course_id, exc)
            stats["failed"] += 1
        except Exception:  # noqa: BLE001
            logger.exception("Unexpected error tagging course %s", course_id)
            stats["failed"] += 1

    logger.info(
        "Tag backfill complete: %d tagged, %d skipped, %d failed (of %d attempted)",
        stats["tagged"],
        stats["skipped"],
        stats["failed"],
        stats["attempted"],
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

    try:
        course_ids = collect_course_ids(
            repository_factory=repository_factory,
            force=args.force,
            include_hidden=args.include_hidden,
            limit=args.limit,
            logger=logger,
        )

        if not course_ids:
            logger.info("No courses require tag generation.")
            return 0

        # get_course() only touches repository_factory, so the collaborators
        # this CourseService normally needs for smart selection are unused here.
        course_service = CourseService(
            repository_factory=repository_factory,
            professor_service=None,
            department_selector_service=None,
            professor_selector_service=None,
            logger=logger,
        )
        content_service = ContentService(logger=logger)
        generator = TagGeneratorService(
            course_service=course_service,
            content_service=content_service,
            repository_factory=repository_factory,
            logger=logger,
        )

        asyncio.run(
            backfill_tags(
                generator=generator,
                course_ids=course_ids,
                dry_run=args.dry_run,
                logger=logger,
            )
        )
    finally:
        repository_factory.dispose_engines()

    logger.info("Backfill process completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
