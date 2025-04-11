"""
API data models for serialization and validation.
These models define the structure of request and response data.
"""

# Re-export models for easier imports
from artificial_u.api.models.professors import (
    ProfessorBase,
    ProfessorCreate,
    ProfessorUpdate,
    ProfessorResponse,
    ProfessorsListResponse,
    CourseBrief as ProfessorCourseBrief,
    LectureBrief as ProfessorLectureBrief,
    ProfessorCoursesResponse,
    ProfessorLecturesResponse,
)
from artificial_u.api.models.departments import (
    DepartmentBase,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentsListResponse,
    ProfessorBrief as DepartmentProfessorBrief,
    CourseBrief as DepartmentCourseBrief,
    DepartmentProfessorsResponse,
    DepartmentCoursesResponse,
)
from artificial_u.api.models.courses import (
    CourseBase,
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CoursesListResponse,
    ProfessorBrief,
    LectureBrief,
    DepartmentBrief,
    CourseLecturesResponse,
)
from artificial_u.api.models.errors import (
    ErrorDetail,
    ErrorResponse,
)
from artificial_u.api.models.error_codes import (
    ErrorCode,
    get_error_description,
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
