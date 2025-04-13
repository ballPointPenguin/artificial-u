"""
Repository module for ArtificialU database operations.
"""

from artificial_u.models.repositories.base import BaseRepository
from artificial_u.models.repositories.course import CourseRepository
from artificial_u.models.repositories.department import DepartmentRepository
from artificial_u.models.repositories.factory import RepositoryFactory
from artificial_u.models.repositories.lecture import LectureRepository
from artificial_u.models.repositories.professor import ProfessorRepository
from artificial_u.models.repositories.voice import VoiceRepository

__all__ = [
    "RepositoryFactory",
    "BaseRepository",
    "DepartmentRepository",
    "ProfessorRepository",
    "CourseRepository",
    "LectureRepository",
    "VoiceRepository",
]
