#!/usr/bin/env python3
"""
Seed initial data for ArtificialU (idempotent).

This script seeds the database with initial faculty data and other foundational
records. It is safe to run multiple times.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from artificial_u.models.core import Faculty  # noqa: E402
from artificial_u.models.repositories.faculty import FacultyRepository  # noqa: E402

FACULTIES = [
    {
        "name": "Arts & Humanities",
        "description": (
            "The study of human culture, creativity, and thought through philosophy, literature, art, religion, "
            "and languages. Explores questions of meaning, value, beauty, and the human condition across time "
            "and civilizations."
        ),
    },
    {
        "name": "Natural Sciences",
        "description": (
            "Investigation of the natural world through empirical observation and experimentation. Encompasses the "
            "life sciences, earth and environmental sciences, physical sciences, and the study of mind and brain. "
            "From cosmology to ecology, from geology to neuroscience."
        ),
    },
    {
        "name": "Technology & Computing",
        "description": (
            "The theory and practice of computation, information systems, and emerging technologies. "
            "Includes artificial intelligence, mathematics, data science, and the applications of technology "
            "in transforming society and solving complex problems."
        ),
    },
    {
        "name": "Social & Historical Sciences",
        "description": (
            "The systematic study of human societies, institutions, and historical development. "
            "Examines social structures, cultural patterns, economic systems, political organization, and the "
            "forces that shape human communities across time and space."
        ),
    },
    {
        "name": "Curiosities & Esoterica",
        "description": (
            "A home for interdisciplinary exploration, unconventional inquiries, and subjects that transcend "
            "traditional academic boundaries. Where the strange, the niche, and the experimental find their place."
        ),
    },
]


def seed_faculties(
    db_url: Optional[str] = None, logger: Optional[logging.Logger] = None
) -> tuple[int, int]:
    """
    Seed faculties. Idempotent - safe to run multiple times.

    Args:
        db_url: Optional database URL (defaults to DATABASE_URL env var)
        logger: Optional logger instance

    Returns:
        Tuple of (created_count, updated_count)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info("Initializing faculty repository...")
    repo = FacultyRepository(db_url=db_url or os.environ.get("DATABASE_URL"))

    created_count = 0
    updated_count = 0

    for faculty_data in FACULTIES:
        name = faculty_data["name"]
        description = faculty_data.get("description")

        existing = repo.get_by_name(name)
        if existing is None:
            logger.info(f"Creating faculty: {name}")
            repo.create(Faculty(name=name, description=description))
            created_count += 1
        else:
            # Update description if changed
            if (existing.description or "") != (description or ""):
                logger.info(f"Updating faculty description: {name}")
                existing.description = description
                repo.update(existing)
                updated_count += 1
            else:
                logger.debug(f"Faculty unchanged: {name}")

    return created_count, updated_count


def main():
    """Seed the database with initial data."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting database seeding...")

        # Seed faculties
        created, updated = seed_faculties(logger=logger)
        logger.info(f"Seeded faculties: {created} created, {updated} updated")

        # Get total faculty count
        repo = FacultyRepository(db_url=os.environ.get("DATABASE_URL"))
        total_faculties = len(repo.list())

        logger.info("Database seeding statistics:")
        logger.info(f"  Total faculties: {total_faculties}")
        logger.info("Database seeding completed successfully")

    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
