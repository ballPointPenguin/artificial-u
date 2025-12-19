"""
Preference repository for database operations.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_

from artificial_u.models.core import Preference
from artificial_u.models.database import PreferenceModel
from artificial_u.models.repositories.base import BaseRepository


class PreferenceRepository(BaseRepository):
    """Repository for Preference operations."""

    def get_global(self, scope: str) -> Optional[Preference]:
        """
        Get a global preference by scope.

        Args:
            scope: The preference scope/key (e.g., "LECTURE_GENERATION_MODEL")

        Returns:
            Preference object if found, None otherwise
        """
        with self.get_session() as session:
            db_pref = (
                session.query(PreferenceModel)
                .filter(
                    and_(
                        PreferenceModel.scope == scope,
                        PreferenceModel.is_global == True,  # noqa: E712
                    )
                )
                .first()
            )
            if not db_pref:
                return None
            return self._to_preference(db_pref)

    def get_user(self, student_id: int, scope: str) -> Optional[Preference]:
        """
        Get a user-specific preference.

        Args:
            student_id: ID of the student
            scope: The preference scope/key

        Returns:
            Preference object if found, None otherwise
        """
        with self.get_session() as session:
            db_pref = (
                session.query(PreferenceModel)
                .filter(
                    and_(
                        PreferenceModel.student_id == student_id,
                        PreferenceModel.scope == scope,
                        PreferenceModel.is_global == False,  # noqa: E712
                    )
                )
                .first()
            )
            if not db_pref:
                return None
            return self._to_preference(db_pref)

    def get(self, student_id: Optional[int], scope: str) -> Optional[Preference]:
        """
        Get a preference, checking user-specific first, then global.

        Args:
            student_id: ID of the student (None to check only global)
            scope: The preference scope/key

        Returns:
            Preference object if found (user-specific takes precedence), None otherwise
        """
        # Check user-specific preference first if student_id provided
        if student_id is not None:
            user_pref = self.get_user(student_id, scope)
            if user_pref:
                return user_pref

        # Fall back to global preference
        return self.get_global(scope)

    def set_global(self, scope: str, value: str) -> Preference:
        """
        Set or update a global preference.

        Args:
            scope: The preference scope/key
            value: The preference value

        Returns:
            The created or updated Preference object
        """
        with self.get_session() as session:
            # Check if preference exists
            db_pref = (
                session.query(PreferenceModel)
                .filter(
                    and_(
                        PreferenceModel.scope == scope,
                        PreferenceModel.is_global == True,  # noqa: E712
                    )
                )
                .first()
            )

            if db_pref:
                # Update existing
                db_pref.value = value
                db_pref.updated_at = datetime.now()
            else:
                # Create new
                db_pref = PreferenceModel(
                    scope=scope,
                    value=value,
                    is_global=True,
                    student_id=None,
                )
                session.add(db_pref)

            session.commit()
            session.refresh(db_pref)
            return self._to_preference(db_pref)

    def set_user(self, student_id: int, scope: str, value: str) -> Preference:
        """
        Set or update a user-specific preference.

        Args:
            student_id: ID of the student
            scope: The preference scope/key
            value: The preference value

        Returns:
            The created or updated Preference object
        """
        with self.get_session() as session:
            # Check if preference exists
            db_pref = (
                session.query(PreferenceModel)
                .filter(
                    and_(
                        PreferenceModel.student_id == student_id,
                        PreferenceModel.scope == scope,
                        PreferenceModel.is_global == False,  # noqa: E712
                    )
                )
                .first()
            )

            if db_pref:
                # Update existing
                db_pref.value = value
                db_pref.updated_at = datetime.now()
            else:
                # Create new
                db_pref = PreferenceModel(
                    student_id=student_id,
                    scope=scope,
                    value=value,
                    is_global=False,
                )
                session.add(db_pref)

            session.commit()
            session.refresh(db_pref)
            return self._to_preference(db_pref)

    def list_all(self, is_global: Optional[bool] = None) -> List[Preference]:
        """
        List all preferences, optionally filtered by is_global.

        Args:
            is_global: If provided, filter by is_global value

        Returns:
            List of Preference objects
        """
        with self.get_session() as session:
            query = session.query(PreferenceModel)
            if is_global is not None:
                query = query.filter(PreferenceModel.is_global == is_global)

            db_prefs = query.all()
            return [self._to_preference(db_pref) for db_pref in db_prefs]

    def delete(self, preference_id: int) -> bool:
        """
        Delete a preference.

        Args:
            preference_id: ID of the preference to delete

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If preference not found
        """
        with self.get_session() as session:
            db_pref = session.get(PreferenceModel, preference_id)
            if not db_pref:
                raise ValueError(f"Preference with ID {preference_id} not found")

            session.delete(db_pref)
            session.commit()
            return True

    def delete_by_scope(self, scope: str, student_id: Optional[int] = None) -> bool:
        """
        Delete a preference by scope and optional student_id.

        Args:
            scope: The preference scope/key
            student_id: If provided, delete user preference; otherwise delete global

        Returns:
            True if deleted successfully, False if not found
        """
        with self.get_session() as session:
            if student_id is None:
                # Delete global preference
                db_pref = (
                    session.query(PreferenceModel)
                    .filter(
                        and_(
                            PreferenceModel.scope == scope,
                            PreferenceModel.is_global == True,  # noqa: E712
                        )
                    )
                    .first()
                )
            else:
                # Delete user preference
                db_pref = (
                    session.query(PreferenceModel)
                    .filter(
                        and_(
                            PreferenceModel.student_id == student_id,
                            PreferenceModel.scope == scope,
                            PreferenceModel.is_global == False,  # noqa: E712
                        )
                    )
                    .first()
                )

            if not db_pref:
                return False

            session.delete(db_pref)
            session.commit()
            return True

    def _to_preference(self, db_pref: PreferenceModel) -> Preference:
        """Convert a PreferenceModel to a Preference object."""
        return Preference(
            id=db_pref.id,
            student_id=db_pref.student_id,
            scope=db_pref.scope,
            value=db_pref.value,
            is_global=db_pref.is_global,
            created_at=db_pref.created_at,
            updated_at=db_pref.updated_at,
        )
