"""
API data models for serialization and validation.
These models define the structure of request and response data.
"""

# Course model
from artificial_u.api.models.courses import (
    CourseBase,
    CourseCreate,
    CourseGenerate,
    CourseLecturesResponse,
    CourseResponse,
    CoursesListResponse,
    CourseUpdate,
)
from artificial_u.api.models.courses import DepartmentBrief as CourseDepartmentBrief
from artificial_u.api.models.courses import (
    GeneratedCourseData,
)
from artificial_u.api.models.courses import LectureBrief as CourseLectureBrief
from artificial_u.api.models.courses import ProfessorBrief as CourseProfessorBrief

# Department model
from artificial_u.api.models.departments import CourseBrief as DepartmentCourseBrief
from artificial_u.api.models.departments import (
    DepartmentBase,
    DepartmentCoursesResponse,
    DepartmentCreate,
    DepartmentGenerate,
    DepartmentProfessorsResponse,
    DepartmentResponse,
    DepartmentsListResponse,
    DepartmentUpdate,
)
from artificial_u.api.models.departments import ProfessorBrief as DepartmentProfessorBrief
from artificial_u.api.models.error_codes import (
    ErrorCode,
    get_error_description,
)

# Error model
from artificial_u.api.models.errors import (
    ErrorDetail,
    ErrorResponse,
)

# Lecture model
from artificial_u.api.models.lectures import (
    Lecture,
    LectureCreate,
    LectureGenerate,
    LectureList,
    LectureUpdate,
)

# Professor model
from artificial_u.api.models.professors import CourseBrief as ProfessorCourseBrief
from artificial_u.api.models.professors import LectureBrief as ProfessorLectureBrief
from artificial_u.api.models.professors import (
    ProfessorBase,
    ProfessorCoursesResponse,
    ProfessorCreate,
    ProfessorGenerate,
    ProfessorLecturesResponse,
    ProfessorResponse,
    ProfessorsListResponse,
    ProfessorUpdate,
)

# All models that should be available for import
__all__ = [
    # Course model
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseGenerate",
    "CourseResponse",
    "CoursesListResponse",
    "CourseProfessorBrief",
    "CourseLectureBrief",
    "CourseDepartmentBrief",
    "CourseLecturesResponse",
    "GeneratedCourseData",
    # Department model
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentGenerate",
    "DepartmentResponse",
    "DepartmentsListResponse",
    "DepartmentProfessorBrief",
    "DepartmentCourseBrief",
    "DepartmentProfessorsResponse",
    "DepartmentCoursesResponse",
    # Professor model
    "ProfessorBase",
    "ProfessorCreate",
    "ProfessorUpdate",
    "ProfessorGenerate",
    "ProfessorResponse",
    "ProfessorsListResponse",
    "ProfessorCourseBrief",
    "ProfessorLectureBrief",
    "ProfessorCoursesResponse",
    "ProfessorLecturesResponse",
    # Lecture model
    "LectureCreate",
    "LectureUpdate",
    "Lecture",
    "LectureGenerate",
    "LectureList",
    # Error codes
    "ErrorDetail",
    "ErrorResponse",
    "ErrorCode",
    "get_error_description",
]
