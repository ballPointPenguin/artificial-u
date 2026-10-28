#!/usr/bin/env python3
"""Migrate Qwen voices from qwen-audio-3.0 to the qwen-audio-3.1-tts-flash voices.

For every ``tts_backend='qwen'`` voice row that is not a 3.1 voice:

1. Pick a replacement 3.1 voice (explicit mapping for known 3.0 voices, otherwise
   by gender: female -> Ava_v3.1, male/unknown -> Brian_v3.1).
2. Make sure the replacement exists in ``voices`` (the 3.1 catalog is upserted).
3. Re-point professors that used the old voice (``tts_backend`` stays ``qwen``).
4. Delete the old voice row, unless a lecture still references it. Lectures keep
   pointing at the voice that narrated their audio; those rows are left in place
   and reported so you can decide what to do with them.

Idempotent. Always run with ``--dry-run`` first.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is on the Python path when executing as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text  # noqa: E402

from artificial_u.integrations.qwen.voice_manager import QwenVoiceManager  # noqa: E402
from artificial_u.models.core import Voice  # noqa: E402
from artificial_u.models.repositories.factory import RepositoryFactory  # noqa: E402

TTS_BACKEND = "qwen"

# 3.0 voice id -> closest 3.1 voice id
VOICE_MAP = {
    "loongjohn": "Brian_v3.1",
    "loongmary": "Emily_v3.1",
    "loongeva_v3.6": "Luna_v3.1",
    "longanlufeng": "Andy_v3.1",
    "longanlingxin": "longanlingxin_v3.1",
    "longanfengyue": "longanfengyue_v3.1",
    "longanhuan_v3.6": "longanhuan_v3.1",
}
FALLBACK_FEMALE = "Ava_v3.1"
FALLBACK_MALE = "Brian_v3.1"


def replacement_voice_id(old_external_id: str, gender: Optional[str]) -> str:
    """Return the 3.1 voice id that should replace a 3.0 voice."""
    if old_external_id in VOICE_MAP:
        return VOICE_MAP[old_external_id]
    return FALLBACK_FEMALE if (gender or "").lower() == "female" else FALLBACK_MALE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--db-url", help="Database URL. Defaults to DATABASE_URL.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changing the DB.")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def migrate(db_url: str, dry_run: bool, logger: logging.Logger) -> dict:
    stats = {"seeded": 0, "remapped": 0, "professors": 0, "deleted": 0, "kept_for_lectures": 0}

    factory = RepositoryFactory(db_url=db_url)
    repo = factory.voice
    catalog = {v["id"]: v for v in QwenVoiceManager().list_voices()}

    try:
        # 1. Ensure the 3.1 catalog is present
        for external_id, info in catalog.items():
            if repo.get_by_external_id(TTS_BACKEND, external_id):
                continue
            stats["seeded"] += 1
            logger.info(
                "%sSeed %s (%s)", "[Dry Run] " if dry_run else "", external_id, info["name"]
            )
            if not dry_run:
                repo.create(
                    Voice(
                        tts_backend=TTS_BACKEND,
                        external_id=external_id,
                        name=info["name"],
                        gender=info.get("gender"),
                        accent=info.get("accent"),
                        description=info.get("description"),
                        language="en" if "en" in info["languages"] else info["languages"][0],
                        category="preset",
                    )
                )

        # 2. Re-point and remove legacy voices
        old_voices = [
            v
            for v in repo.list(tts_backend=TTS_BACKEND, limit=10_000)
            if v.external_id not in catalog
        ]
        logger.info("Found %d legacy Qwen voice(s)", len(old_voices))

        with repo.get_session() as session:
            for old in old_voices:
                new_ext = replacement_voice_id(old.external_id or "", old.gender)
                new = repo.get_by_external_id(TTS_BACKEND, new_ext)
                new_id = new.id if new else None
                if new_id is None and not dry_run:
                    raise RuntimeError(f"Replacement voice {new_ext} missing after seeding")

                professors = session.execute(
                    text("SELECT COUNT(*) FROM professors WHERE voice_id = :v"), {"v": old.id}
                ).scalar()
                lectures = session.execute(
                    text("SELECT COUNT(*) FROM lectures WHERE voice_id = :v"), {"v": old.id}
                ).scalar()
                logger.info(
                    "%s%s (%s) -> %s: %d professor(s), %d lecture(s)",
                    "[Dry Run] " if dry_run else "",
                    old.external_id,
                    old.name,
                    new_ext,
                    professors,
                    lectures,
                )
                stats["remapped"] += 1
                stats["professors"] += professors
                if lectures:
                    stats["kept_for_lectures"] += 1
                else:
                    stats["deleted"] += 1
                if dry_run:
                    continue

                session.execute(
                    text("UPDATE professors SET voice_id = :n WHERE voice_id = :o"),
                    {"n": new_id, "o": old.id},
                )
                if not lectures:
                    session.execute(text("DELETE FROM voices WHERE id = :o"), {"o": old.id})
            if not dry_run:
                session.commit()
    finally:
        factory.dispose_engines()

    return stats


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("scripts.backfill_qwen_voices_v31")

    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("Database URL not provided. Set --db-url or DATABASE_URL.")
        return 1

    stats = migrate(db_url=db_url, dry_run=args.dry_run, logger=logger)
    logger.info(
        "Done%s: %d seeded, %d legacy voices remapped (%d professors re-pointed), "
        "%d deleted, %d kept because lectures reference them",
        " (dry run)" if args.dry_run else "",
        stats["seeded"],
        stats["remapped"],
        stats["professors"],
        stats["deleted"],
        stats["kept_for_lectures"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
