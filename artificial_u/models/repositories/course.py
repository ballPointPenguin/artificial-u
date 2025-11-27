from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from artificial_u.models.core import Course, Student
from artificial_u.models.database import (
    CourseModel,
    LectureModel,
    TopicModel,
)
from artificial_u.models.repositories.base import BaseRepository


class CourseRepository(BaseRepository):
    def __init__(self, db_url: Optional[str] = None):
        super().__init__(db_url)
        self.model = CourseModel

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    def _convert_student(self, db_student) -> Optional[Student]:
        if not db_student:
            return None
        if getattr(db_student, "id", None) is None:
            return None
        return Student(
            id=db_student.id,
            name=db_student.name,
            email=db_student.email,
            auth0_sub=getattr(db_student, "auth0_sub", None),
            role=getattr(db_student, "role", "viewer"),
            coins=getattr(db_student, "coins", 0),
            is_active=getattr(db_student, "is_active", True),
        )

    def _convert_course(self, db_course: CourseModel) -> Course:
        student_obj = getattr(db_course, "student", None)
        course_student = None
        if student_obj is not None and isinstance(getattr(student_obj, "id", None), int):
            course_student = self._convert_student(student_obj)

        return Course(
            id=db_course.id,
            code=db_course.code,
            title=db_course.title,
            credits=db_course.credits,
            description=db_course.description,
            lectures_per_week=db_course.lectures_per_week,
            level=db_course.level,
            total_weeks=db_course.total_weeks,
            status=db_course.status,
            department_id=db_course.department_id,
            professor_id=db_course.professor_id,
            created_by=db_course.created_by,
            created_with=db_course.created_with,
            created_at=db_course.created_at,
            updated_at=db_course.updated_at,
            student=course_student,
            lectures_with_audio_count=0,
            topics_count=0,
        )

    # ------------------------------------------------------------------
    # Legacy CRUD interface (used by services/tests)
    # ------------------------------------------------------------------

    def create(self, course: Course) -> Course:
        with self.get_session() as session:
            db_course = CourseModel(
                code=course.code,
                title=course.title,
                credits=course.credits,
                description=course.description,
                lectures_per_week=course.lectures_per_week,
                level=course.level,
                total_weeks=course.total_weeks,
                status=course.status,
                department_id=course.department_id,
                professor_id=course.professor_id,
                created_by=course.created_by,
                created_with=course.created_with,
            )

            session.add(db_course)
            session.commit()
            session.refresh(db_course)

            created_course = self._convert_course(db_course)
            course.id = created_course.id
            course.created_at = created_course.created_at
            course.updated_at = created_course.updated_at
            return course

    def get(self, course_id: int) -> Optional[Course]:
        with self.get_session() as session:
            db_course = (
                session.query(self.model)
                .options(joinedload(self.model.student))
                .filter_by(id=course_id)
                .first()
            )
            if db_course:
                return self._convert_course(db_course)
        return None

    def get_by_code(self, code: str) -> Optional[Course]:
        with self.get_session() as session:
            db_course = session.query(self.model).filter_by(code=code).first()
            if db_course:
                return self._convert_course(db_course)
        return None

    def list(self, department_id: Optional[int] = None) -> List[Course]:
        with self.get_session() as session:
            query = session.query(self.model)
            if department_id is not None:
                query = query.filter_by(department_id=department_id)
            db_courses = query.all()
            return [self._convert_course(course) for course in db_courses]

    def update(self, course: Course) -> Course:
        with self.get_session() as session:
            db_course = session.query(self.model).filter_by(id=course.id).first()
            if not db_course:
                raise ValueError(f"Course with ID {course.id} not found")

            db_course.code = course.code
            db_course.title = course.title
            db_course.credits = course.credits
            db_course.description = course.description
            db_course.lectures_per_week = course.lectures_per_week
            db_course.level = course.level
            db_course.total_weeks = course.total_weeks
            db_course.status = course.status
            db_course.department_id = course.department_id
            db_course.professor_id = course.professor_id
            db_course.created_by = course.created_by
            db_course.created_with = course.created_with

            session.commit()
            session.refresh(db_course)

            updated_course = self._convert_course(db_course)
            course.updated_at = updated_course.updated_at
            return course

    def delete(self, course_id: int) -> bool:
        with self.get_session() as session:
            db_course = session.query(self.model).filter_by(id=course_id).first()
            if not db_course:
                return False
            session.delete(db_course)
            session.commit()
            return True

    def list_and_count(
        self,
        page: int = 1,
        size: int = 10,
        sort_by: str = "updated_at",
        order: str = "desc",
        department_id: Optional[int] = None,
        professor_id: Optional[int] = None,
        level: Optional[str] = None,
        title: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> Tuple[List[Course], int]:
        """
        List courses with advanced filtering, sorting, pagination, and counts.
        Returns a tuple of (courses, total_count).
        """
        with self.get_session() as session:
            # Subquery for lectures with audio
            # Count distinct topics (not total lectures) to handle multiple revisions
            lectures_audio_sq = (
                session.query(
                    LectureModel.course_id,
                    func.count(func.distinct(LectureModel.topic_id)).label("audio_count"),
                )
                .filter(LectureModel.audio_url.isnot(None))
                .group_by(LectureModel.course_id)
                .subquery()
            )

            # Subquery for total topics
            topics_sq = (
                session.query(
                    TopicModel.course_id,
                    func.count(TopicModel.id).label("topics_count"),
                )
                .group_by(TopicModel.course_id)
                .subquery()
            )

            # Main query
            query = (
                session.query(
                    CourseModel,
                    lectures_audio_sq.c.audio_count,
                    topics_sq.c.topics_count,
                )
                .outerjoin(lectures_audio_sq, CourseModel.id == lectures_audio_sq.c.course_id)
                .outerjoin(topics_sq, CourseModel.id == topics_sq.c.course_id)
                .options(
                    joinedload(CourseModel.professor),
                    joinedload(CourseModel.department),
                    joinedload(CourseModel.student),
                )
            )

            # Filtering
            if department_id:
                query = query.filter(CourseModel.department_id == department_id)
            if professor_id:
                query = query.filter(CourseModel.professor_id == professor_id)
            if level:
                query = query.filter(CourseModel.level == level)
            if title:
                query = query.filter(CourseModel.title.ilike(f"%{title}%"))
            if created_by:
                query = query.filter(CourseModel.created_by == created_by)

            # Get total count before sorting and pagination
            total_count = query.count()

            # Sorting
            sort_column = getattr(CourseModel, sort_by, CourseModel.updated_at)
            if order == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())

            # Pagination
            query = query.limit(size).offset((page - 1) * size)

            # Execute query
            results = query.all()

            # Process results into Course models
            courses = []
            for course_model, audio_count, topics_count in results:
                course = Course.model_validate(course_model, from_attributes=True)
                course.lectures_with_audio_count = audio_count or 0
                course.topics_count = topics_count or 0
                courses.append(course)

            return courses, total_count

    def list_recent(self, limit: int = 20) -> List[Course]:
        """List most recent courses ordered by ID descending."""
        with self.get_session() as session:
            db_courses = (
                session.query(self.model)
                .options(
                    joinedload(self.model.professor),
                    joinedload(self.model.department),
                    joinedload(self.model.student),
                )
                .order_by(self.model.id.desc())
                .limit(limit)
                .all()
            )
            return [Course.model_validate(c, from_attributes=True) for c in db_courses]
