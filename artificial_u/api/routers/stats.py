"""
Platform statistics endpoint.

Provides aggregate counts for the homepage stats strip:
courses, lectures (with audio), and total audio hours.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func

from artificial_u.api.dependencies import get_repository_factory
from artificial_u.models.database import CourseModel, LectureModel
from artificial_u.models.repositories import RepositoryFactory

router = APIRouter(prefix="/stats", tags=["Stats"])


class StatsResponse(BaseModel):
    """Aggregate platform statistics."""

    course_count: int = Field(..., description="Total number of published courses")
    lecture_count: int = Field(..., description="Total number of lectures with audio")
    audio_hours: int = Field(..., description="Total hours of audio content (rounded down)")


@router.get("", response_model=StatsResponse)
async def get_stats(
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Get aggregate platform statistics.

    Returns counts of published courses, lectures with audio,
    and total audio hours derived from the lectures.duration column.
    """
    with repository_factory.lecture.get_session() as session:
        # Count published courses
        course_count = (
            session.query(func.count(CourseModel.id))
            .filter(CourseModel.status == "published")
            .scalar()
            or 0
        )

        # Count lectures that have audio
        lecture_count = (
            session.query(func.count(LectureModel.id))
            .filter(LectureModel.audio_url.isnot(None))
            .scalar()
            or 0
        )

        # Sum duration (seconds) for all lectures with audio, convert to hours
        total_seconds = (
            session.query(func.sum(LectureModel.duration))
            .filter(LectureModel.audio_url.isnot(None))
            .scalar()
            or 0
        )
        audio_hours = total_seconds // 3600

    return StatsResponse(
        course_count=course_count,
        lecture_count=lecture_count,
        audio_hours=audio_hours,
    )
