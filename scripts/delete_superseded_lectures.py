#!/usr/bin/env python3
"""Identify and optionally delete superseded lecture revisions.

By default this script is a dry run. Use --apply to delete candidate lectures via
LectureService.delete_lecture(), which also performs best-effort storage cleanup.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from sqlalchemy import text

# Ensure project root is on the Python path when executing as a script.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

from artificial_u.models.repositories.factory import RepositoryFactory  # noqa: E402
from artificial_u.services.lecture_service import LectureService  # noqa: E402


@dataclass(frozen=True)
class LectureDeletionCandidate:
    id: int
    topic_id: int
    revision: int
    max_revision: int
    topic_lecture_count: int
    title: Optional[str]
    audio_url: Optional[str]
    transcript_url: Optional[str]
    timeline_url: Optional[str]
    images_timeline_url: Optional[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find older lecture revisions and optionally delete them with storage cleanup."
        ),
    )
    parser.add_argument(
        "--db-url",
        help="Database connection URL. Defaults to DATABASE_URL env var if unset.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete candidate lectures. Default is dry-run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview candidates without deleting. This is the default.",
    )
    parser.add_argument(
        "--topic-id",
        type=int,
        help="Limit candidate search to one topic ID.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional cap on candidates to report/delete.",
    )
    parser.add_argument(
        "--mode",
        choices=("lower-than-max", "keep-one-per-topic"),
        default="lower-than-max",
        help=(
            "Candidate strategy. lower-than-max deletes revisions below the max revision "
            "for each topic. keep-one-per-topic keeps one newest/highest-revision row and "
            "returns all others, including duplicate max revisions."
        ),
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
    return logging.getLogger("scripts.delete_superseded_lectures")


def _candidate_query(mode: str) -> str:
    if mode == "keep-one-per-topic":
        return """
            WITH ranked AS (
                SELECT
                    id,
                    topic_id,
                    revision,
                    title,
                    audio_url,
                    transcript_url,
                    timeline_url,
                    images_timeline_url,
                    COUNT(*) OVER (PARTITION BY topic_id) AS topic_lecture_count,
                    MAX(revision) OVER (PARTITION BY topic_id) AS max_revision,
                    ROW_NUMBER() OVER (
                        PARTITION BY topic_id
                        ORDER BY revision DESC, created_at DESC, id DESC
                    ) AS keep_rank
                FROM lectures
                WHERE (:topic_id IS NULL OR topic_id = :topic_id)
            )
            SELECT
                id,
                topic_id,
                revision,
                title,
                audio_url,
                transcript_url,
                timeline_url,
                images_timeline_url,
                topic_lecture_count,
                max_revision
            FROM ranked
            WHERE topic_lecture_count > 1
              AND keep_rank > 1
            ORDER BY topic_id, revision DESC, id DESC
        """

    return """
        WITH ranked AS (
            SELECT
                id,
                topic_id,
                revision,
                title,
                audio_url,
                transcript_url,
                timeline_url,
                images_timeline_url,
                COUNT(*) OVER (PARTITION BY topic_id) AS topic_lecture_count,
                MAX(revision) OVER (PARTITION BY topic_id) AS max_revision
            FROM lectures
            WHERE (:topic_id IS NULL OR topic_id = :topic_id)
        )
        SELECT
            id,
            topic_id,
            revision,
            title,
            audio_url,
            transcript_url,
            timeline_url,
            images_timeline_url,
            topic_lecture_count,
            max_revision
        FROM ranked
        WHERE topic_lecture_count > 1
          AND revision < max_revision
        ORDER BY topic_id, revision, id
    """


def collect_candidates(
    repository_factory: RepositoryFactory,
    *,
    mode: str,
    topic_id: Optional[int],
    limit: Optional[int],
) -> List[LectureDeletionCandidate]:
    query = _candidate_query(mode)
    if limit is not None and limit > 0:
        query = f"{query}\nLIMIT :limit"

    params = {"topic_id": topic_id}
    if limit is not None and limit > 0:
        params["limit"] = limit

    with repository_factory.lecture.get_session() as session:
        rows = session.execute(text(query), params).mappings().all()

    return [
        LectureDeletionCandidate(
            id=int(row["id"]),
            topic_id=int(row["topic_id"]),
            revision=int(row["revision"]),
            max_revision=int(row["max_revision"]),
            topic_lecture_count=int(row["topic_lecture_count"]),
            title=row["title"],
            audio_url=row["audio_url"],
            transcript_url=row["transcript_url"],
            timeline_url=row["timeline_url"],
            images_timeline_url=row["images_timeline_url"],
        )
        for row in rows
    ]


def log_candidates(candidates: List[LectureDeletionCandidate], logger: logging.Logger) -> None:
    if not candidates:
        logger.info("No superseded lecture candidates found.")
        return

    for candidate in candidates:
        asset_labels = [
            label
            for label, url in (
                ("audio", candidate.audio_url),
                ("transcript", candidate.transcript_url),
                ("timeline", candidate.timeline_url),
                ("images_timeline", candidate.images_timeline_url),
            )
            if url
        ]
        logger.info(
            "Candidate lecture_id=%s topic_id=%s revision=%s max_revision=%s "
            "topic_lecture_count=%s assets=%s title=%r",
            candidate.id,
            candidate.topic_id,
            candidate.revision,
            candidate.max_revision,
            candidate.topic_lecture_count,
            ",".join(asset_labels) if asset_labels else "none",
            candidate.title,
        )


def delete_candidates(
    candidates: List[LectureDeletionCandidate],
    lecture_service: LectureService,
    logger: logging.Logger,
) -> int:
    deleted = 0
    for candidate in candidates:
        try:
            logger.info(
                "Deleting lecture_id=%s topic_id=%s revision=%s",
                candidate.id,
                candidate.topic_id,
                candidate.revision,
            )
            if lecture_service.delete_lecture(candidate.id):
                deleted += 1
        except Exception as e:
            logger.error(
                "Failed deleting lecture_id=%s topic_id=%s revision=%s: %s",
                candidate.id,
                candidate.topic_id,
                candidate.revision,
                e,
                exc_info=True,
            )
    return deleted


def main() -> int:
    args = parse_args()
    logger = configure_logging(args.log_level)

    db_url = args.db_url or os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("Database URL not provided. Set --db-url or DATABASE_URL.")
        return 1

    dry_run = not args.apply
    if args.dry_run and args.apply:
        logger.error("Use either --dry-run or --apply, not both.")
        return 1

    repository_factory = RepositoryFactory(db_url=db_url)
    try:
        candidates = collect_candidates(
            repository_factory,
            mode=args.mode,
            topic_id=args.topic_id,
            limit=args.limit,
        )

        logger.info(
            "Found %d candidate lecture(s) with mode=%s%s.",
            len(candidates),
            args.mode,
            f" for topic_id={args.topic_id}" if args.topic_id else "",
        )
        log_candidates(candidates, logger)

        if dry_run:
            logger.info("Dry run only. Re-run with --apply to delete these lectures.")
            return 0

        lecture_service = LectureService(
            repository_factory=repository_factory,
            logger=logger,
        )
        deleted = delete_candidates(candidates, lecture_service, logger)
        logger.info("Deleted %d of %d candidate lecture(s).", deleted, len(candidates))
        return 0 if deleted == len(candidates) else 1
    finally:
        repository_factory.dispose_engines()


if __name__ == "__main__":
    raise SystemExit(main())
