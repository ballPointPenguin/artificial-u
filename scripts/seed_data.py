# scripts/seed_data.py
"""Seed initial data for ArtificialU (idempotent)."""

import os
from typing import Optional

from artificial_u.models.core import Faculty
from artificial_u.models.repositories.faculty import FacultyRepository

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


def seed_faculties(db_url: Optional[str] = None) -> None:
    """Seed faculties. Idempotent - safe to run multiple times."""
    repo = FacultyRepository(db_url=db_url or os.environ.get("DATABASE_URL"))

    created_count = 0
    updated_count = 0

    for faculty_data in FACULTIES:
        name = faculty_data["name"]
        description = faculty_data.get("description")

        existing = repo.get_by_name(name)
        if existing is None:
            repo.create(Faculty(name=name, description=description))
            created_count += 1
        else:
            # Update description if changed
            if (existing.description or "") != (description or ""):
                existing.description = description
                repo.update(existing)
                updated_count += 1

    print(f"Seeded faculties: {created_count} created, {updated_count} updated")


if __name__ == "__main__":
    print("Seeding faculties...")
    seed_faculties()
