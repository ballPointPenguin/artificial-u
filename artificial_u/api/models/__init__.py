"""
API data models for serialization and validation.
These models define the structure of request and response data.
"""

from artificial_u.api.models.courses import (
    CourseBase,
    CourseCreate,
    CourseLecturesResponse,
    CourseResponse,
    CoursesListResponse,
    CourseUpdate,
    DepartmentBrief,
    LectureBrief,
    ProfessorBrief,
)
from artificial_u.api.models.departments import CourseBrief as DepartmentCourseBrief
from artificial_u.api.models.departments import (
    DepartmentBase,
    DepartmentCoursesResponse,
    DepartmentCreate,
    DepartmentProfessorsResponse,
    DepartmentResponse,
    DepartmentsListResponse,
    DepartmentUpdate,
)
from artificial_u.api.models.departments import (
    ProfessorBrief as DepartmentProfessorBrief,
)
from artificial_u.api.models.error_codes import ErrorCode, get_error_description
from artificial_u.api.models.errors import ErrorDetail, ErrorResponse

# Re-export models for easier imports
from artificial_u.api.models.professors import CourseBrief as ProfessorCourseBrief
from artificial_u.api.models.professors import LectureBrief as ProfessorLectureBrief
from artificial_u.api.models.professors import (
    ProfessorBase,
    ProfessorCoursesResponse,
    ProfessorCreate,
    ProfessorLecturesResponse,
    ProfessorResponse,
    ProfessorsListResponse,
    ProfessorUpdate,
)

# All models that should be available for import
__all__ = [
    # Professor models
    "ProfessorBase",
    "ProfessorCreate",
    "ProfessorUpdate",
    "ProfessorResponse",
    "ProfessorsListResponse",
    "ProfessorCourseBrief",
    "ProfessorLectureBrief",
    "ProfessorCoursesResponse",
    "ProfessorLecturesResponse",
    # Department models
    "DepartmentBase",
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    "DepartmentsListResponse",
    "DepartmentProfessorBrief",
    "DepartmentCourseBrief",
    "DepartmentProfessorsResponse",
    "DepartmentCoursesResponse",
    # Course models
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "CoursesListResponse",
    "ProfessorBrief",
    "LectureBrief",
    "DepartmentBrief",
    "CourseLecturesResponse",
    # Errors
    "ErrorDetail",
    "ErrorResponse",
    "ErrorCode",
    "get_error_description",
]
