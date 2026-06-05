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

FACULTIES_EN = [
    {
        "name": "Arts & Humanities",
        "language": "en",
        "description": (
            "The study of human culture, creativity, and thought through philosophy, literature, art, religion, "
            "and languages. Explores questions of meaning, value, beauty, and the human condition across time "
            "and civilizations."
        ),
    },
    {
        "name": "Natural Sciences",
        "language": "en",
        "description": (
            "Investigation of the natural world through empirical observation and experimentation. Encompasses the "
            "life sciences, earth and environmental sciences, physical sciences, and the study of mind and brain. "
            "From cosmology to ecology, from geology to neuroscience."
        ),
    },
    {
        "name": "Technology & Computing",
        "language": "en",
        "description": (
            "The theory and practice of computation, information systems, and emerging technologies. "
            "Includes artificial intelligence, mathematics, data science, and the applications of technology "
            "in transforming society and solving complex problems."
        ),
    },
    {
        "name": "Social & Historical Sciences",
        "language": "en",
        "description": (
            "The systematic study of human societies, institutions, and historical development. "
            "Examines social structures, cultural patterns, economic systems, political organization, and the "
            "forces that shape human communities across time and space."
        ),
    },
    {
        "name": "Curiosities & Esoterica",
        "language": "en",
        "description": (
            "A home for interdisciplinary exploration, unconventional inquiries, and subjects that transcend "
            "traditional academic boundaries. Where the strange, the niche, and the experimental find their place."
        ),
    },
]

FACULTIES_FR = [
    {
        "name": "Arts et Humanités",
        "language": "fr",
        "description": (
            "L'étude de la culture humaine, de la créativité et de la pensée à travers la philosophie, "
            "la littérature, l'art, la religion et les langues. Une exploration des questions de sens, "
            "de valeur, de beauté et de la condition humaine à travers le temps et les civilisations."
        ),
    },
    {
        "name": "Sciences Naturelles",
        "language": "fr",
        "description": (
            "L'investigation du monde naturel par l'observation empirique et l'expérimentation. "
            "Englobe les sciences du vivant, les sciences de la Terre et de l'environnement, les sciences "
            "physiques, ainsi que l'étude de l'esprit et du cerveau. De la cosmologie à l'écologie, "
            "de la géologie aux neurosciences."
        ),
    },
    {
        "name": "Technologie et Informatique",
        "language": "fr",
        "description": (
            "La théorie et la pratique du calcul, des systèmes d'information et des technologies émergentes. "
            "Comprend l'intelligence artificielle, les mathématiques, la science des données, et les applications "
            "de la technologie pour transformer la société et résoudre des problèmes complexes."
        ),
    },
    {
        "name": "Sciences Sociales et Historiques",
        "language": "fr",
        "description": (
            "L'étude systématique des sociétés humaines, des institutions et du développement historique. "
            "Examine les structures sociales, les schémas culturels, les systèmes économiques, l'organisation "
            "politique et les forces qui façonnent les communautés humaines à travers le temps et l'espace."
        ),
    },
    {
        "name": "Curiosités et Ésotérica",
        "language": "fr",
        "description": (
            "Un espace pour l'exploration interdisciplinaire, les enquêtes non conventionnelles et les sujets "
            "qui transcendent les frontières académiques traditionnelles. Là où l'étrange, le pointu "
            "et l'expérimental trouvent leur place."
        ),
    },
]

# All faculty sets indexed by language code
ALL_FACULTIES = {
    "en": FACULTIES_EN,
    "fr": FACULTIES_FR,
}


def seed_faculties(
    db_url: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    languages: Optional[list] = None,
) -> tuple[int, int]:
    """
    Seed faculties for the given language codes. Idempotent - safe to run multiple times.

    Args:
        db_url: Optional database URL (defaults to DATABASE_URL env var)
        logger: Optional logger instance
        languages: Language codes to seed (defaults to all defined languages)

    Returns:
        Tuple of (created_count, updated_count)
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if languages is None:
        languages = list(ALL_FACULTIES.keys())

    logger.info("Initializing faculty repository...")
    repo = FacultyRepository(db_url=db_url or os.environ.get("DATABASE_URL"))

    created_count = 0
    updated_count = 0

    for lang in languages:
        faculties_for_lang = ALL_FACULTIES.get(lang, [])
        for faculty_data in faculties_for_lang:
            name = faculty_data["name"]
            language = faculty_data["language"]
            description = faculty_data.get("description")

            existing = repo.get_by_name_and_language(name, language)
            if existing is None:
                logger.info(f"Creating faculty [{language}]: {name}")
                repo.create(Faculty(name=name, description=description, language=language))
                created_count += 1
            else:
                if (existing.description or "") != (description or ""):
                    logger.info(f"Updating faculty [{language}]: {name}")
                    existing.description = description
                    repo.update(existing)
                    updated_count += 1
                else:
                    logger.debug(f"Faculty unchanged [{language}]: {name}")

    return created_count, updated_count


def main():
    """Seed the database with initial data."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    try:
        logger.info("Starting database seeding...")

        created, updated = seed_faculties(logger=logger)
        logger.info(f"Seeded faculties: {created} created, {updated} updated")

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
