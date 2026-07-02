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
from artificial_u.api.models.courses import (
    TagBrief,
    TagsUpdate,
)

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

# Error model
from artificial_u.api.models.error_codes import (
    ErrorCode,
    get_error_description,
)
from artificial_u.api.models.errors import (
    ErrorDetail,
    ErrorResponse,
)

# Faculty model
from artificial_u.api.models.faculties import (
    FacultiesListResponse,
    FacultyResponse,
)

# Lecture model
from artificial_u.api.models.lectures import (
    AdminLectureListItem,
    AdminLectureListResponse,
    Lecture,
    LectureBase,
    LectureCreate,
    LectureGenerate,
    LectureListResponse,
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

# Quickstart model
from artificial_u.api.models.quickstart import CourseBrief as QuickstartCourseBrief
from artificial_u.api.models.quickstart import (
    IntroAudioRequest,
    IntroAudioResponse,
)
from artificial_u.api.models.quickstart import ProfessorDetail as QuickstartProfessorDetail
from artificial_u.api.models.quickstart import (
    QuickstartFinalizeRequest,
    QuickstartFinalizeResponse,
    QuickstartMatchRequest,
    QuickstartMatchResponse,
    QuickstartProfessorActionRequest,
    QuickstartProfessorResponse,
    QuickstartRegenerateProfessorRequest,
    QuickstartStartRequest,
    QuickstartStartResponse,
)

# Student model
from artificial_u.api.models.students import (
    StudentCoinsAdd,
    StudentResponse,
    StudentRoleUpdate,
    StudentsListResponse,
    StudentUpdate,
)

# Topic model
from artificial_u.api.models.topics import (
    Topic,
    TopicBase,
    TopicCreate,
    TopicGenerate,
    TopicListResponse,
    TopicUpdate,
)

# Voice model
from artificial_u.api.models.voice import (
    ManualVoiceAssignmentRequest,
    VoiceBase,
    VoiceListResponse,
    VoiceResponse,
)

# All models that should be available for import
__all__ = [
    # Course model
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "CourseGenerate",
    "CourseResponse",
    "TagBrief",
    "TagsUpdate",
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
    # Faculty model
    "FacultyResponse",
    "FacultiesListResponse",
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
    "LectureBase",
    "LectureCreate",
    "LectureUpdate",
    "Lecture",
    "LectureGenerate",
    "LectureListResponse",
    "AdminLectureListItem",
    "AdminLectureListResponse",
    # Topic model
    "TopicBase",
    "TopicCreate",
    "TopicUpdate",
    "Topic",
    "TopicGenerate",
    "TopicListResponse",
    # Voice model
    "VoiceBase",
    "VoiceResponse",
    "VoiceListResponse",
    "ManualVoiceAssignmentRequest",
    # Student model
    "StudentResponse",
    "StudentUpdate",
    "StudentsListResponse",
    "StudentRoleUpdate",
    "StudentCoinsAdd",
    # Error codes
    "ErrorDetail",
    "ErrorResponse",
    "ErrorCode",
    "get_error_description",
    # Quickstart model
    "QuickstartCourseBrief",
    "QuickstartProfessorDetail",
    "QuickstartMatchRequest",
    "QuickstartMatchResponse",
    "QuickstartStartRequest",
    "QuickstartStartResponse",
    "QuickstartProfessorResponse",
    "QuickstartProfessorActionRequest",
    "QuickstartRegenerateProfessorRequest",
    "QuickstartFinalizeRequest",
    "QuickstartFinalizeResponse",
    "IntroAudioRequest",
    "IntroAudioResponse",
]
