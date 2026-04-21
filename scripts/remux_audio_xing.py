#!/usr/bin/env python3
"""Remux existing lecture MP3s so they carry a correct Xing/Info header.

Background
----------
MP3 has no file-level duration field. Players and metadata readers rely on
the Xing/LAME header (embedded in the first MPEG frame) to report total
length. When our TTS pipeline concatenated per-chunk MP3s, the inherited
Xing from chunk 1 described only chunk 1, and a previous "fix" invoked
ffmpeg with `-write_xing 0` which stripped the header entirely instead of
rewriting it. The result: Finder, mutagen, and browsers all fall back to
CBR extrapolation and report wildly wrong durations. Browsers "chase" the
real duration while scrubbing maps to a shrunken timeline, which breaks
caption sync.

This script downloads each affected audio file from S3/MinIO, re-muxes it
with `ffmpeg -c:a copy` (letting the default MP3 muxer write a correct
Xing header based on the actual frame count), re-uploads the corrected
file to the same object key, and updates `lectures.duration` in the
database with the newly accurate value.

Preconditions
-------------
- ffmpeg on PATH.
- `DATABASE_URL` set (or pass `--db-url`).
- Valid AWS credentials resolvable by boto3's default chain (env vars,
  `~/.aws/credentials`, or an active SSO session). Pass `--aws-profile`
  to force a specific profile. The script validates the credentials with
  `sts:GetCallerIdentity` before processing any lectures and errors out
  if they're missing or expired.

Idempotency
-----------
By default the script is a no-op for files that already report a
consistent duration. For each file we compare the mutagen-reported
duration before and after the remux; if they agree within 1 second AND
the DB value also agrees, we skip both the upload and the DB write. Pass
`--force` to re-upload and re-write everything regardless.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import boto3  # noqa: E402
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError  # noqa: E402
from mutagen.mp3 import MP3  # noqa: E402

from artificial_u.config import get_settings  # noqa: E402
from artificial_u.models.repositories.factory import RepositoryFactory  # noqa: E402
from artificial_u.services.storage_service import StorageService  # noqa: E402

DEFAULT_BATCH_SIZE = 5
DURATION_TOLERANCE_SECONDS = 1.0
FFMPEG_TIMEOUT_SECONDS = 120


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Re-mux lecture MP3s so they have a correct Xing header, "
            "then update lectures.duration with the accurate value."
        ),
    )
    parser.add_argument(
        "--db-url",
        help="Database connection URL. Defaults to DATABASE_URL env var if unset.",
    )
    parser.add_argument(
        "--aws-profile",
        help=(
            "AWS profile to use (sets AWS_PROFILE before StorageService "
            "builds its boto3 client). Useful when you have multiple SSO "
            "profiles configured."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=(
            f"Number of audio files to process concurrently per batch "
            f"(default: {DEFAULT_BATCH_SIZE}). Each file is ~8MB in+out, "
            "so keep this modest."
        ),
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
        "--force",
        action="store_true",
        help=(
            "Re-upload and re-write DB duration for every file even when "
            "the existing durations already look correct."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without uploading files or updating the DB.",
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
    # Quiet noisy boto3/urllib3 at INFO so our output stays readable.
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return logging.getLogger("scripts.remux_audio_xing")


def verify_prerequisites(logger: logging.Logger) -> bool:
    """Check ffmpeg and AWS credentials up-front. Returns False on failure."""
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        logger.error(
            "ffmpeg not found on PATH. Install it (e.g. `brew install ffmpeg`) " "and try again."
        )
        return False
    logger.info("Using ffmpeg at %s", ffmpeg_path)

    settings = get_settings()
    if settings.STORAGE_TYPE != "s3":
        logger.info(
            "STORAGE_TYPE=%s - skipping AWS credential check (local/MinIO).",
            settings.STORAGE_TYPE,
        )
        return True

    try:
        session = boto3.session.Session(region_name=settings.STORAGE_REGION)
        identity = session.client("sts").get_caller_identity()
    except NoCredentialsError:
        logger.error(
            "No AWS credentials found. Run `aws sso login` (or set "
            "AWS_PROFILE / AWS_ACCESS_KEY_ID) and retry."
        )
        return False
    except (ClientError, BotoCoreError) as e:
        logger.error(
            "AWS credentials are present but invalid or expired (%s). "
            "Re-authenticate (e.g. `aws sso login`) and retry.",
            e,
        )
        return False

    logger.info(
        "AWS identity verified: account=%s arn=%s",
        identity.get("Account"),
        identity.get("Arn"),
    )
    return True


def read_mp3_duration_seconds(audio_bytes: bytes) -> Optional[float]:
    """Return mutagen's reported duration for the given MP3 bytes, or None."""
    try:
        audio = MP3(io.BytesIO(audio_bytes))
        if audio.info and audio.info.length:
            return float(audio.info.length)
        return None
    except Exception:
        return None


def remux_with_xing_header(
    audio_bytes: bytes, ffmpeg_path: str, logger: logging.Logger
) -> Optional[bytes]:
    """
    Re-mux MP3 bytes via `ffmpeg -c:a copy` so the output has a correct
    Xing/Info header. Preserves ID3v2 metadata (ffmpeg's MP3 muxer maps
    global metadata from the input by default).

    Returns the fixed bytes, or None on failure.
    """
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix="remux_xing_")
        input_path = os.path.join(temp_dir, "input.mp3")
        output_path = os.path.join(temp_dir, "output.mp3")

        with open(input_path, "wb") as f:
            f.write(audio_bytes)

        cmd = [
            ffmpeg_path,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            input_path,
            "-c:a",
            "copy",
            "-map_metadata",
            "0",
            "-id3v2_version",
            "3",
            output_path,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            logger.warning(
                "ffmpeg remux failed (exit %d): %s",
                result.returncode,
                result.stderr.strip(),
            )
            return None

        with open(output_path, "rb") as f:
            return f.read()
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg remux timed out after %ds", FFMPEG_TIMEOUT_SECONDS)
        return None
    except Exception as e:
        logger.warning("Error during ffmpeg remux: %s", e)
        return None
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass


def collect_lectures_with_audio(
    repository_factory: RepositoryFactory,
    lecture_id: Optional[int],
    course_id: Optional[int],
    limit: Optional[int],
    logger: logging.Logger,
) -> List[int]:
    """Return IDs of lectures that have audio URLs, filtered by the given args."""
    from artificial_u.models.database import LectureModel

    with repository_factory.lecture.get_session() as session:
        query = session.query(LectureModel.id).filter(LectureModel.audio_url.isnot(None))

        if lecture_id:
            query = query.filter(LectureModel.id == lecture_id)
        if course_id:
            query = query.filter(LectureModel.course_id == course_id)

        query = query.order_by(LectureModel.id)
        if limit is not None and limit > 0:
            query = query.limit(limit)

        ids = [row[0] for row in query.all()]

    logger.info("Found %d lectures with audio to consider", len(ids))
    return ids


async def process_lecture(
    lecture_id: int,
    repository_factory: RepositoryFactory,
    storage_service: StorageService,
    ffmpeg_path: str,
    force: bool,
    dry_run: bool,
    logger: logging.Logger,
) -> str:
    """
    Download, remux, and (if changed) re-upload one lecture's audio.
    Updates lectures.duration when the mutagen-reported duration changes.

    Returns one of: "fixed", "skipped", "failed".
    """
    try:
        lecture = repository_factory.lecture.get(lecture_id)
        if not lecture or not lecture.audio_url:
            logger.warning("Lecture %d has no audio URL, skipping", lecture_id)
            return "skipped"

        bucket, object_key = storage_service.parse_storage_url(lecture.audio_url)
        if not bucket or not object_key:
            logger.error(
                "Failed to parse audio URL for lecture %d: %s",
                lecture_id,
                lecture.audio_url,
            )
            return "failed"

        audio_bytes, _content_type = await storage_service.download_file(bucket, object_key)
        if not audio_bytes:
            logger.error("Failed to download audio for lecture %d", lecture_id)
            return "failed"

        orig_size = len(audio_bytes)
        orig_duration = read_mp3_duration_seconds(audio_bytes)

        fixed_bytes = await asyncio.to_thread(
            remux_with_xing_header, audio_bytes, ffmpeg_path, logger
        )
        if not fixed_bytes:
            logger.error("ffmpeg failed to remux lecture %d", lecture_id)
            return "failed"

        new_duration = read_mp3_duration_seconds(fixed_bytes)
        if new_duration is None:
            logger.error("Could not read duration from remuxed output for lecture %d", lecture_id)
            return "failed"

        # Detect whether anything needs to change. We consider a file
        # "already correct" when the remuxed duration agrees with both
        # the input duration and the DB duration within tolerance.
        duration_diff_vs_input = (
            abs((orig_duration or 0.0) - new_duration)
            if orig_duration is not None
            else float("inf")
        )
        db_duration = float(lecture.duration) if lecture.duration is not None else None
        duration_diff_vs_db = (
            abs((db_duration or 0.0) - new_duration) if db_duration is not None else float("inf")
        )
        already_correct = (
            duration_diff_vs_input < DURATION_TOLERANCE_SECONDS
            and duration_diff_vs_db < DURATION_TOLERANCE_SECONDS
        )

        new_duration_int = int(round(new_duration))

        if already_correct and not force:
            logger.info(
                "Lecture %d already correct (%.1fs, db=%s, size=%d); skipping",
                lecture_id,
                new_duration,
                lecture.duration,
                orig_size,
            )
            return "skipped"

        action_summary = (
            f"lecture={lecture_id} "
            f"orig_duration={orig_duration!s} "
            f"new_duration={new_duration:.1f}s "
            f"db_duration={lecture.duration!s} "
            f"orig_bytes={orig_size} new_bytes={len(fixed_bytes)}"
        )

        if dry_run:
            logger.info("[Dry Run] Would remux and update: %s", action_summary)
            return "fixed"

        upload_success, _url = await storage_service.upload_file(
            file_data=fixed_bytes,
            bucket=bucket,
            object_name=object_key,
            content_type="audio/mpeg",
        )
        if not upload_success:
            logger.error("Failed to upload remuxed audio for lecture %d", lecture_id)
            return "failed"

        repository_factory.lecture.update_fields(
            lecture_id=lecture_id,
            update_data={"duration": new_duration_int},
        )
        logger.info("Remuxed and updated duration: %s", action_summary)
        return "fixed"

    except Exception as e:
        logger.error("Error processing lecture %d: %s", lecture_id, e, exc_info=True)
        return "failed"


async def remux_all(
    lecture_ids: List[int],
    repository_factory: RepositoryFactory,
    ffmpeg_path: str,
    batch_size: int,
    force: bool,
    dry_run: bool,
    logger: logging.Logger,
) -> Dict[str, int]:
    """Process lectures in batches. Returns counters for the final summary."""
    stats = {"total": len(lecture_ids), "fixed": 0, "skipped": 0, "failed": 0}
    if not lecture_ids:
        return stats

    storage_service = StorageService(logger=logger)

    for start in range(0, len(lecture_ids), batch_size):
        batch_ids = lecture_ids[start : start + batch_size]
        logger.info(
            "Processing batch %d (%d lectures, ids=%s)",
            start // batch_size + 1,
            len(batch_ids),
            batch_ids,
        )

        tasks = [
            process_lecture(
                lecture_id=lid,
                repository_factory=repository_factory,
                storage_service=storage_service,
                ffmpeg_path=ffmpeg_path,
                force=force,
                dry_run=dry_run,
                logger=logger,
            )
            for lid in batch_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                stats["failed"] += 1
            elif result in stats:
                stats[result] += 1
            else:
                stats["failed"] += 1

    logger.info(
        "Remux complete: fixed=%d skipped=%d failed=%d total=%d",
        stats["fixed"],
        stats["skipped"],
        stats["failed"],
        stats["total"],
    )
    return stats


async def main_async(args: argparse.Namespace, logger: logging.Logger) -> int:
    if args.aws_profile:
        os.environ["AWS_PROFILE"] = args.aws_profile
        logger.info("Using AWS_PROFILE=%s", args.aws_profile)

    if not verify_prerequisites(logger):
        return 1

    ffmpeg_path = shutil.which("ffmpeg")
    assert ffmpeg_path  # verify_prerequisites guarantees this

    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("Database URL not provided. Set --db-url or DATABASE_URL.")
        return 1

    repository_factory = RepositoryFactory(db_url=db_url)
    try:
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

        await remux_all(
            lecture_ids=lecture_ids,
            repository_factory=repository_factory,
            ffmpeg_path=ffmpeg_path,
            batch_size=max(1, args.batch_size),
            force=args.force,
            dry_run=args.dry_run,
            logger=logger,
        )
    finally:
        repository_factory.dispose_engines()

    logger.info("Remux process completed.")
    return 0


def main() -> int:
    args = parse_args()
    logger = configure_logging(args.log_level)
    return asyncio.run(main_async(args, logger))


if __name__ == "__main__":
    raise SystemExit(main())
