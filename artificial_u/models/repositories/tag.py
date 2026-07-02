"""
Repository for Tag operations.

Tags belong to a single content-language universe: English courses carry
English tags, French courses carry French tags. Uniqueness is enforced on
(slug, language), and the slug is the deduplication mechanism.
"""

import re
import unicodedata
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from artificial_u.models.core import Tag
from artificial_u.models.database import CourseModel, CourseTagModel, TagModel
from artificial_u.models.repositories.base import BaseRepository


class TagRepository(BaseRepository):
    """Repository for managing tags and course-tag assignments."""

    @staticmethod
    def slugify(name: str) -> str:
        """
        Normalize a display name into a slug: lowercase, accents stripped,
        non-word runs collapsed to single hyphens.
        """
        normalized = unicodedata.normalize("NFKD", name)
        without_accents = "".join(c for c in normalized if not unicodedata.combining(c))
        return re.sub(r"[^\w]+", "-", without_accents.lower()).strip("-")

    def get_or_create_by_names(self, names: List[str], language: str = "en") -> List[Tag]:
        """
        Resolve display names to Tag rows in the given language universe,
        creating any that do not exist yet. Names that normalize to the same
        slug are deduplicated (first occurrence wins).

        Args:
            names: Display names, e.g. ["Quantum Physics", "Ethics"]
            language: Content language of the tag universe

        Returns:
            List of Tag models in input order (after dedup)
        """
        names_by_slug: dict = {}
        for raw in names:
            name = " ".join(str(raw).split())
            slug = self.slugify(name) if name else ""
            if slug and slug not in names_by_slug:
                names_by_slug[slug] = name

        if not names_by_slug:
            return []

        tags: List[Tag] = []
        with self.get_session() as session:
            for slug, name in names_by_slug.items():
                row = (
                    session.query(TagModel)
                    .filter(TagModel.slug == slug, TagModel.language == language)
                    .first()
                )
                if not row:
                    row = TagModel(slug=slug, name=name, language=language)
                    session.add(row)
                    try:
                        session.commit()
                    except IntegrityError:
                        # Another worker created the same (slug, language) concurrently
                        session.rollback()
                        row = (
                            session.query(TagModel)
                            .filter(TagModel.slug == slug, TagModel.language == language)
                            .one()
                        )
                tags.append(self._to_model(row))
        return tags

    def set_course_tags(self, course_id: int, tag_ids: List[int]) -> List[Tag]:
        """
        Replace the full tag set of a course in one transaction.

        Args:
            course_id: Course to update
            tag_ids: Tag IDs to assign (duplicates ignored)

        Returns:
            The course's tags after the update, ordered by name
        """
        unique_ids = list(dict.fromkeys(tag_ids))
        with self.get_session() as session:
            session.query(CourseTagModel).filter(CourseTagModel.course_id == course_id).delete()
            for tag_id in unique_ids:
                session.add(CourseTagModel(course_id=course_id, tag_id=tag_id))
            session.commit()
            rows = (
                session.query(TagModel)
                .join(CourseTagModel, CourseTagModel.tag_id == TagModel.id)
                .filter(CourseTagModel.course_id == course_id)
                .order_by(TagModel.name)
                .all()
            )
            return [self._to_model(r) for r in rows]

    def list_for_course(self, course_id: int) -> List[Tag]:
        """List a course's tags ordered by name."""
        with self.get_session() as session:
            rows = (
                session.query(TagModel)
                .join(CourseTagModel, CourseTagModel.tag_id == TagModel.id)
                .filter(CourseTagModel.course_id == course_id)
                .order_by(TagModel.name)
                .all()
            )
            return [self._to_model(r) for r in rows]

    def list_with_counts(
        self,
        language: str = "en",
        q: Optional[str] = None,
        limit: int = 100,
    ) -> List[Tuple[Tag, int]]:
        """
        List tags in a language universe with published-course counts,
        most-used first. Tags with no published courses are omitted.

        Args:
            language: Content language of the tag universe
            q: Optional name prefix filter
            limit: Maximum number of tags returned

        Returns:
            List of (Tag, course_count) tuples
        """
        with self.get_session() as session:
            count_col = func.count(CourseModel.id)
            query = (
                session.query(TagModel, count_col)
                .join(CourseTagModel, CourseTagModel.tag_id == TagModel.id)
                .join(CourseModel, CourseModel.id == CourseTagModel.course_id)
                .filter(TagModel.language == language, CourseModel.status == "published")
            )
            if q:
                query = query.filter(TagModel.name.ilike(f"{q}%"))
            rows = (
                query.group_by(TagModel.id)
                .order_by(count_col.desc(), TagModel.name.asc())
                .limit(limit)
                .all()
            )
            return [(self._to_model(tag), count) for tag, count in rows]

    def list_top_names(self, language: str = "en", limit: int = 100) -> List[str]:
        """
        List the most-used tag display names in a language universe, for
        priming the generation prompt. Counts include courses of any status
        so draft vocabulary is reused too.
        """
        with self.get_session() as session:
            count_col = func.count(CourseTagModel.course_id)
            rows = (
                session.query(TagModel.name)
                .join(CourseTagModel, CourseTagModel.tag_id == TagModel.id)
                .filter(TagModel.language == language)
                .group_by(TagModel.id)
                .order_by(count_col.desc(), TagModel.name.asc())
                .limit(limit)
                .all()
            )
            return [name for (name,) in rows]

    def list_backfill_course_ids(
        self,
        force: bool = False,
        include_hidden: bool = False,
    ) -> List[int]:
        """
        Course IDs eligible for tag backfill: published courses without any
        tags. `force` includes already-tagged courses; `include_hidden`
        includes non-published courses.
        """
        with self.get_session() as session:
            query = session.query(CourseModel.id)
            if not include_hidden:
                query = query.filter(CourseModel.status == "published")
            if not force:
                tagged = session.query(CourseTagModel.course_id).filter(
                    CourseTagModel.course_id == CourseModel.id
                )
                query = query.filter(~tagged.exists())
            return [course_id for (course_id,) in query.order_by(CourseModel.id).all()]

    @staticmethod
    def _to_model(row: TagModel) -> Tag:
        return Tag(
            id=row.id,
            slug=row.slug,
            name=row.name,
            language=row.language,
            created_at=row.created_at,
        )
