"""
Integration tests for DepartmentService.
"""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from artificial_u.models.core import Course, Faculty, Professor
from artificial_u.models.repositories import RepositoryFactory
from artificial_u.services import DepartmentService
from artificial_u.utils import DepartmentNotFoundError, DependencyError

# Example AI-generated XML response for department
MOCK_DEPARTMENT_XML = """
<output>
  <department>
    <name>Data Science</name>
    <code>DS</code>
    <faculty>Engineering</faculty>
    <description>A modern department focused on data analytics and machine learning.</description>
  </department>
</output>
"""


@pytest.fixture
def repository_factory():
    """Create a repository factory that uses the test database."""
    # The DATABASE_URL will be picked up from .env.test
    return RepositoryFactory()


@pytest.fixture
def content_service():
    """Create a mock ContentService with async support."""
    mock = MagicMock()
    mock.generate_text = AsyncMock(return_value=MOCK_DEPARTMENT_XML)
    return mock


@pytest.fixture
def department_service(repository_factory):
    """Create a DepartmentService with mocked dependent services."""
    professor_service = MagicMock()
    course_service = MagicMock()
    return DepartmentService(
        repository_factory=repository_factory,
        professor_service=professor_service,
        course_service=course_service,
        logger=logging.getLogger(__name__),
    )


@pytest.fixture
def sample_faculties(repository_factory):
    """Create sample faculties for testing."""
    faculties = {}
    for name in ["Engineering", "Science", "Arts", "Business", "Test"]:
        faculty = Faculty(name=name, description=f"The {name} faculty.", language="en")
        faculty = repository_factory.faculty.create(faculty)
        faculties[name] = faculty.id
    return faculties


@pytest.mark.integration
class TestDepartmentService:
    """Integration tests for DepartmentService."""

    def test_create_and_get_department(
        self, department_service, repository_factory, sample_faculties
    ):
        """Test creating and retrieving a department."""
        # Create a new department
        dept = department_service.create_department(
            name="Computer Science",
            code="CS",
            faculty_id=sample_faculties["Engineering"],
            description="Study of computation",
        )

        # Verify it was created with an ID
        assert dept.id is not None
        assert dept.name == "Computer Science"
        assert dept.code == "CS"

        # Retrieve the department and verify
        retrieved = department_service.get_department(dept.id)
        assert retrieved.id == dept.id
        assert retrieved.name == "Computer Science"
        assert retrieved.code == "CS"

    def test_update_department(self, department_service, repository_factory, sample_faculties):
        """Test updating a department."""
        # Create a department
        dept = department_service.create_department(
            name="Economics", code="ECON", faculty_id=sample_faculties["Business"]
        )

        # Update the department
        updated = department_service.update_department(
            dept.id, {"name": "Economics and Finance", "code": "ECONFIN"}
        )

        # Verify updates
        assert updated.name == "Economics and Finance"
        assert updated.code == "ECONFIN"

        # Retrieve to confirm persistence
        retrieved = department_service.get_department(dept.id)
        assert retrieved.name == "Economics and Finance"
        assert retrieved.code == "ECONFIN"

    def test_list_departments(self, department_service, repository_factory, sample_faculties):
        """Test listing departments with/without faculty filter."""
        # Create departments in different faculties
        department_service.create_department(
            name="Physics", code="PHYS", faculty_id=sample_faculties["Science"]
        )
        department_service.create_department(
            name="Mathematics", code="MATH", faculty_id=sample_faculties["Science"]
        )
        department_service.create_department(
            name="History", code="HIST", faculty_id=sample_faculties["Arts"]
        )

        # List all departments
        all_depts = department_service.list_departments()
        assert len(all_depts) >= 3  # At least our 3 (could be more if DB has existing data)

        # List by faculty_id
        science_depts = department_service.list_departments(faculty_id=sample_faculties["Science"])
        assert len(science_depts) >= 2
        codes = [d.code for d in science_depts]
        assert "PHYS" in codes
        assert "MATH" in codes

        arts_depts = department_service.list_departments(faculty_id=sample_faculties["Arts"])
        assert len(arts_depts) >= 1
        assert any(d.code == "HIST" for d in arts_depts)

    def test_get_department_not_found(self, department_service):
        """Test getting a non-existent department raises appropriate error."""
        with pytest.raises(DepartmentNotFoundError):
            department_service.get_department("999999")

    def test_department_with_professors(
        self, department_service, repository_factory, sample_faculties
    ):
        """Test department with professors - creates professors, checks dependencies."""
        # Create a department
        dept = department_service.create_department(
            name="Chemistry", code="CHEM", faculty_id=sample_faculties["Science"]
        )

        # Create a professor in this department
        professor = Professor(
            name="Dr. Jane Smith",
            title="Associate Professor",
            department_id=dept.id,
            specialization="Organic Chemistry",
        )
        professor = repository_factory.professor.create(professor)

        # Get department professors
        professors = department_service.get_department_professors(dept.id)
        assert len(professors) >= 1
        assert any(p.id == professor.id for p in professors)

        # Test dependency protection - shouldn't be able to delete department with professors
        with pytest.raises(DependencyError):
            department_service.delete_department(dept.id)

    def test_department_with_courses(
        self, department_service, repository_factory, sample_faculties
    ):
        """Test department with courses - creates courses, checks dependencies."""
        # Create a department
        dept = department_service.create_department(
            name="Biology", code="BIO", faculty_id=sample_faculties["Science"]
        )

        # Create a course in this department
        course = Course(
            code="BIO101",
            title="Introduction to Biology",
            department_id=dept.id,
            level="Undergraduate",
            description="Basic biology concepts",
            lectures_per_week=2,
            total_weeks=14,
            language="en",
            topics=[{"name": "Cell Biology"}, {"name": "Genetics"}],
        )
        course = repository_factory.course.create(course)

        # Get department courses
        courses = department_service.get_department_courses(dept.id)
        assert len(courses) >= 1
        assert any(c.id == course.id for c in courses)

        # Test dependency protection - shouldn't be able to delete department with courses
        with pytest.raises(DependencyError):
            department_service.delete_department(dept.id)

    def test_delete_department(self, department_service, repository_factory, sample_faculties):
        """Test deleting a department with no dependencies."""
        # Create a temporary department
        dept = department_service.create_department(
            name="Temp Dept",
            code="TEMP-DELETE",  # Use unique code to avoid conflicts
            faculty_id=sample_faculties["Test"],
        )

        # Delete it
        result = department_service.delete_department(dept.id)
        assert result is True

        # Verify it's gone
        with pytest.raises(DepartmentNotFoundError):
            department_service.get_department(dept.id)
