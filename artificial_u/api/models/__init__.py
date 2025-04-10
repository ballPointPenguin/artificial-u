"""
API models for input/output data formats.
"""

from artificial_u.api.models.professors import (
    ProfessorBase,
    ProfessorCreate,
    ProfessorUpdate,
    ProfessorResponse,
    ProfessorsListResponse,
    CourseBrief,
    LectureBrief,
    ProfessorCoursesResponse,
    ProfessorLecturesResponse,
)

__all__ = [
    "ProfessorBase",
    "ProfessorCreate",
    "ProfessorUpdate",
    "ProfessorResponse",
    "ProfessorsListResponse",
    "CourseBrief",
    "LectureBrief",
    "ProfessorCoursesResponse",
    "ProfessorLecturesResponse",
]
