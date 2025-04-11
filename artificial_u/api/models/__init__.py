"""
API models for input/output data formats.
"""

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
]
