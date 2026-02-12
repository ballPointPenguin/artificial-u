"""
Global search endpoint.

Searches across lectures, courses, professors, departments, and topics
using ILIKE pattern matching, returning grouped results capped per category.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_

from artificial_u.api.dependencies import get_repository_factory
from artificial_u.models.database import (
    CourseModel,
    DepartmentModel,
    LectureModel,
    ProfessorModel,
    TopicModel,
)
from artificial_u.models.repositories import RepositoryFactory

router = APIRouter(prefix="/search", tags=["Search"])

MAX_RESULTS_PER_CATEGORY = 5


# -- Compact result models (lighter than full entity responses) --


class LectureSearchResult(BaseModel):
    """Lecture hit from global search."""

    id: int
    title: str
    summary: Optional[str] = None
    course_id: int
    course_title: Optional[str] = None
    course_code: Optional[str] = None
    professor_name: Optional[str] = None
    department_name: Optional[str] = None
    audio_url: Optional[str] = None
    duration: Optional[int] = None


class CourseSearchResult(BaseModel):
    """Course hit from global search."""

    id: int
    code: str
    title: str
    description: Optional[str] = None
    level: Optional[str] = None
    department_name: Optional[str] = None
    professor_name: Optional[str] = None
    status: Optional[str] = None


class ProfessorSearchResult(BaseModel):
    """Professor hit from global search."""

    id: int
    name: str
    title: Optional[str] = None
    specialization: Optional[str] = None
    department_name: Optional[str] = None
    image_url: Optional[str] = None


class DepartmentSearchResult(BaseModel):
    """Department hit from global search."""

    id: int
    name: str
    code: str
    description: Optional[str] = None


class TopicSearchResult(BaseModel):
    """Topic hit from global search."""

    id: int
    title: str
    week: int
    course_id: int
    course_title: Optional[str] = None
    course_code: Optional[str] = None


class SearchResponse(BaseModel):
    """Grouped search results across all entity types."""

    query: str = Field(..., description="The search query that was executed")
    lectures: List[LectureSearchResult] = Field(
        default_factory=list, description="Matching lectures"
    )
    courses: List[CourseSearchResult] = Field(default_factory=list, description="Matching courses")
    professors: List[ProfessorSearchResult] = Field(
        default_factory=list, description="Matching professors"
    )
    departments: List[DepartmentSearchResult] = Field(
        default_factory=list, description="Matching departments"
    )
    topics: List[TopicSearchResult] = Field(default_factory=list, description="Matching topics")


@router.get("", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    limit: int = Query(
        MAX_RESULTS_PER_CATEGORY,
        ge=1,
        le=20,
        description="Max results per category",
    ),
    repository_factory: RepositoryFactory = Depends(get_repository_factory),
):
    """
    Search across lectures, courses, professors, departments, and topics.

    Returns up to `limit` results per category, matched via case-insensitive
    substring search (ILIKE).
    """
    pattern = f"%{q}%"

    with repository_factory.lecture.get_session() as session:
        # -- Lectures: title, summary --
        lecture_rows = (
            session.query(LectureModel)
            .outerjoin(CourseModel, LectureModel.course_id == CourseModel.id)
            .outerjoin(ProfessorModel, CourseModel.professor_id == ProfessorModel.id)
            .outerjoin(DepartmentModel, CourseModel.department_id == DepartmentModel.id)
            .filter(
                or_(
                    LectureModel.title.ilike(pattern),
                    LectureModel.summary.ilike(pattern),
                )
            )
            .order_by(LectureModel.created_at.desc())
            .limit(limit)
            .all()
        )
        lectures = [
            LectureSearchResult(
                id=lec.id,
                title=lec.title,
                summary=lec.summary,
                course_id=lec.course_id,
                course_title=lec.course.title if lec.course else None,
                course_code=lec.course.code if lec.course else None,
                professor_name=(
                    lec.course.professor.name if lec.course and lec.course.professor else None
                ),
                department_name=(
                    lec.course.department.name if lec.course and lec.course.department else None
                ),
                audio_url=lec.audio_url,
                duration=lec.duration,
            )
            for lec in lecture_rows
        ]

        # -- Courses: title, description, code --
        course_rows = (
            session.query(CourseModel)
            .outerjoin(DepartmentModel, CourseModel.department_id == DepartmentModel.id)
            .outerjoin(ProfessorModel, CourseModel.professor_id == ProfessorModel.id)
            .filter(
                or_(
                    CourseModel.title.ilike(pattern),
                    CourseModel.description.ilike(pattern),
                    CourseModel.code.ilike(pattern),
                )
            )
            .order_by(CourseModel.updated_at.desc())
            .limit(limit)
            .all()
        )
        courses = [
            CourseSearchResult(
                id=c.id,
                code=c.code,
                title=c.title,
                description=c.description,
                level=c.level,
                department_name=c.department.name if c.department else None,
                professor_name=c.professor.name if c.professor else None,
                status=c.status,
            )
            for c in course_rows
        ]

        # -- Professors: name, specialization --
        professor_rows = (
            session.query(ProfessorModel)
            .outerjoin(DepartmentModel, ProfessorModel.department_id == DepartmentModel.id)
            .filter(
                or_(
                    ProfessorModel.name.ilike(pattern),
                    ProfessorModel.specialization.ilike(pattern),
                )
            )
            .order_by(ProfessorModel.name)
            .limit(limit)
            .all()
        )
        professors = [
            ProfessorSearchResult(
                id=p.id,
                name=p.name,
                title=p.title,
                specialization=p.specialization,
                department_name=p.department.name if p.department else None,
                image_url=p.image_url,
            )
            for p in professor_rows
        ]

        # -- Departments: name, description --
        department_rows = (
            session.query(DepartmentModel)
            .filter(
                or_(
                    DepartmentModel.name.ilike(pattern),
                    DepartmentModel.description.ilike(pattern),
                )
            )
            .order_by(DepartmentModel.name)
            .limit(limit)
            .all()
        )
        departments = [
            DepartmentSearchResult(
                id=d.id,
                name=d.name,
                code=d.code,
                description=d.description,
            )
            for d in department_rows
        ]

        # -- Topics: title --
        topic_rows = (
            session.query(TopicModel)
            .outerjoin(CourseModel, TopicModel.course_id == CourseModel.id)
            .filter(TopicModel.title.ilike(pattern))
            .order_by(TopicModel.title)
            .limit(limit)
            .all()
        )
        topics = [
            TopicSearchResult(
                id=t.id,
                title=t.title,
                week=t.week,
                course_id=t.course_id,
                course_title=t.course.title if t.course else None,
                course_code=t.course.code if t.course else None,
            )
            for t in topic_rows
        ]

    return SearchResponse(
        query=q,
        lectures=lectures,
        courses=courses,
        professors=professors,
        departments=departments,
        topics=topics,
    )
