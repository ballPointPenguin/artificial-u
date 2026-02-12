"""
Repository for FeaturedItem operations.
"""

from typing import List, Optional

from artificial_u.models.core import FeaturedItem
from artificial_u.models.database import FeaturedItemModel
from artificial_u.models.repositories.base import BaseRepository


class FeaturedItemRepository(BaseRepository):
    """Repository for managing featured homepage items."""

    def list_by_type(
        self,
        item_type: str,
        language: str = "en",
    ) -> List[FeaturedItem]:
        """
        List featured items of a given type for a language, ordered by display_order.

        Args:
            item_type: One of "lecture", "professor", "department"
            language: Language code (default "en")

        Returns:
            List of FeaturedItem models
        """
        with self.get_session() as session:
            rows = (
                session.query(FeaturedItemModel)
                .filter(
                    FeaturedItemModel.item_type == item_type,
                    FeaturedItemModel.language == language,
                )
                .order_by(FeaturedItemModel.display_order, FeaturedItemModel.id)
                .all()
            )
            return [self._to_model(r) for r in rows]

    def list_all(self, language: str = "en") -> List[FeaturedItem]:
        """
        List all featured items for a language.

        Args:
            language: Language code (default "en")

        Returns:
            List of FeaturedItem models
        """
        with self.get_session() as session:
            rows = (
                session.query(FeaturedItemModel)
                .filter(FeaturedItemModel.language == language)
                .order_by(
                    FeaturedItemModel.item_type,
                    FeaturedItemModel.display_order,
                    FeaturedItemModel.id,
                )
                .all()
            )
            return [self._to_model(r) for r in rows]

    def add(
        self,
        item_type: str,
        item_id: int,
        language: str = "en",
        display_order: int = 0,
    ) -> FeaturedItem:
        """
        Add an item to featured. If it already exists for that type+id+language,
        returns the existing record.

        Args:
            item_type: One of "lecture", "professor", "department"
            item_id: PK of the source record
            language: Language code
            display_order: Sort order (lower = first)

        Returns:
            The created or existing FeaturedItem
        """
        with self.get_session() as session:
            existing = (
                session.query(FeaturedItemModel)
                .filter(
                    FeaturedItemModel.item_type == item_type,
                    FeaturedItemModel.item_id == item_id,
                    FeaturedItemModel.language == language,
                )
                .first()
            )
            if existing:
                return self._to_model(existing)

            row = FeaturedItemModel(
                item_type=item_type,
                item_id=item_id,
                language=language,
                display_order=display_order,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._to_model(row)

    def remove(self, featured_id: int) -> bool:
        """
        Remove a featured item by its own PK.

        Returns:
            True if deleted, False if not found
        """
        with self.get_session() as session:
            row = session.get(FeaturedItemModel, featured_id)
            if not row:
                return False
            session.delete(row)
            session.commit()
            return True

    def update_order(self, featured_id: int, display_order: int) -> Optional[FeaturedItem]:
        """
        Update the display order of a featured item.

        Returns:
            Updated FeaturedItem, or None if not found
        """
        with self.get_session() as session:
            row = session.get(FeaturedItemModel, featured_id)
            if not row:
                return None
            row.display_order = display_order
            session.commit()
            session.refresh(row)
            return self._to_model(row)

    @staticmethod
    def _to_model(row: FeaturedItemModel) -> FeaturedItem:
        return FeaturedItem(
            id=row.id,
            item_type=row.item_type,
            item_id=row.item_id,
            language=row.language,
            display_order=row.display_order,
            created_at=row.created_at,
        )
