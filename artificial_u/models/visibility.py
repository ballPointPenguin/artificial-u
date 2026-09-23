"""
Course discoverability rules.

Hidden courses (and the topics and lectures under them) are unlisted, not
private: anyone with a direct URL can open them, but they must not surface in
discovery views (search, browse, recent/featured lists, professor/department
course lists, aggregate stats) except to their owner or an admin.

Direct lookups scoped to a specific course/topic/lecture intentionally skip
this filter.
"""

from typing import Optional

from sqlalchemy import ColumnElement, or_, true

from artificial_u.models.core import Student
from artificial_u.models.database import CourseModel


def discoverable_courses(viewer: Optional[Student]) -> ColumnElement[bool]:
    """
    SQL criterion selecting the courses `viewer` may discover.

    - Anonymous: published courses only
    - Signed in: published courses plus hidden courses they created
    - Admin: every course

    Apply to any query that selects or joins `CourseModel`.
    """
    if viewer is not None and viewer.role == "admin":
        return true()
    published = CourseModel.status == "published"
    if viewer is None or viewer.id is None:
        return published
    return or_(published, CourseModel.created_by == viewer.id)
