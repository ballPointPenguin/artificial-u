"""
API services for business logic.
"""

from artificial_u.api.services.base_service import BaseApiService
from artificial_u.api.services.course_service import CourseApiService
from artificial_u.api.services.department_service import DepartmentApiService
from artificial_u.api.services.faculty_service import FacultyApiService
from artificial_u.api.services.lecture_service import LectureApiService
from artificial_u.api.services.professor_service import ProfessorApiService
from artificial_u.api.services.topic_service import TopicApiService

__all__ = [
    "BaseApiService",
    "ProfessorApiService",
    "CourseApiService",
    "DepartmentApiService",
    "FacultyApiService",
    "LectureApiService",
    "TopicApiService",
]
